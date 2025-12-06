# db/client.py - MongoDB client and collection setup
import os
import certifi
import ssl
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
if not MONGO_URI:
    raise ValueError("Missing MONGODB_URI environment variable")

# Create SSL context with proper certificate verification
ssl_context = ssl.create_default_context(cafile=certifi.where())
ssl_context.check_hostname = True
ssl_context.verify_mode = ssl.CERT_REQUIRED

# Configure connection with SSL certificate and proper pooling
client = AsyncIOMotorClient(
    MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    tlsAllowInvalidCertificates=False,
    tlsAllowInvalidHostnames=False,
    maxPoolSize=10,
    minPoolSize=1,
    serverSelectionTimeoutMS=30000,
    connectTimeoutMS=30000,
)

db = client["expense_tracker"]
expenses_col = db["expenses"]
