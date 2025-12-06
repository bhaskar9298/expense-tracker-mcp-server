# fastapi_auth/main.py - Authentication & MCP Gateway
from fastapi import FastAPI, HTTPException, Depends, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import httpx
import hashlib
from typing import Optional
from pathlib import Path

# Load .env from parent directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

app = FastAPI(title="Expense Tracker Auth API")

# CORS Configuration - Update for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Connection
MONGO_URI = os.getenv("MONGODB_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client["expense_tracker"]
users_collection = db["users"]

# Security Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

security = HTTPBearer()

# MCP Server Configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")

# Pydantic Models
class UserSignup(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class MCPExecuteRequest(BaseModel):
    tool: str
    args: dict

class TokenData(BaseModel):
    email: str
    user_id: str

# Authentication Utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash"""
    # Handle the same pre-hashing for long passwords during verification
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        # Pre-hash long passwords with SHA256
        password_bytes = hashlib.sha256(password_bytes).hexdigest().encode('utf-8')
    
    return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    # Bcrypt has a 72-byte limit. For longer passwords, we pre-hash with SHA256
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Pre-hash long passwords with SHA256 before bcrypt
        password_bytes = hashlib.sha256(password_bytes).hexdigest().encode('utf-8')
    
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(request: Request) -> TokenData:
    """Extract user from HttpOnly cookie"""
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        
        if email is None or user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return TokenData(email=email, user_id=user_id)
    
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Routes
@app.post("/auth/signup")
async def signup(user: UserSignup, response: Response):
    """Register new user"""
    # Check if user exists
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_doc = {
        "email": user.email,
        "password_hash": get_password_hash(user.password),
        "full_name": user.full_name,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await users_collection.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    # Create JWT token
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user_id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # Set HttpOnly cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,  # HTTPS only in production
        samesite="strict",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return {
        "status": "success",
        "message": "User created successfully",
        "user": {
            "email": user.email,
            "full_name": user.full_name
        }
    }

@app.post("/auth/login")
async def login(credentials: UserLogin, response: Response):
    """Login user"""
    # Find user
    user = await users_collection.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user_id = str(user["_id"])
    
    # Create JWT token
    access_token = create_access_token(
        data={"sub": credentials.email, "user_id": user_id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # Set HttpOnly cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return {
        "status": "success",
        "message": "Login successful",
        "user": {
            "email": user["email"],
            "full_name": user.get("full_name")
        }
    }

@app.post("/auth/logout")
async def logout(response: Response):
    """Logout user"""
    response.delete_cookie(key="access_token")
    return {"status": "success", "message": "Logged out successfully"}

@app.get("/auth/me")
async def get_me(current_user: TokenData = Depends(get_current_user)):
    """Get current user info"""
    user = await users_collection.find_one({"email": current_user.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "email": user["email"],
        "full_name": user.get("full_name"),
        "created_at": user["created_at"]
    }

@app.post("/mcp/execute")
async def execute_mcp_tool(
    request: MCPExecuteRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Gateway to MCP server - injects user_id from JWT
    """
    # Add user_id to arguments
    args_with_user = {
        "user_id": current_user.user_id,
        **request.args
    }
    
    # Forward to FastMCP remote server
    async with httpx.AsyncClient() as client:
        try:
            # Try direct tool endpoint: /tools/{tool_name}
            response = await client.post(
                f"{MCP_SERVER_URL}/tools/{request.tool}",
                json=args_with_user,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"MCP call failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "auth-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
