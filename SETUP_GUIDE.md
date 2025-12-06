# Expense Tracker MCP - Production Setup Guide

## System Architecture

This is a complete AI-powered expense tracking system with:
- **FastMCP Server**: MCP protocol server with expense management tools
- **FastAPI Auth Backend**: JWT authentication with HttpOnly cookies
- **React Frontend**: Vite-based UI with Gemini AI integration
- **MongoDB Atlas**: Cloud database with user isolation

## Project Structure

```
expense-tracker-mcp-server/
├── main.py                    # FastMCP server with user_id filtering
├── db/
│   ├── client.py             # MongoDB connection (Motor)
│   ├── schema.py             # JSON schemas (expenses + users)
│   └── init.py               # Database initialization
├── fastapi_auth/
│   └── main.py               # JWT auth + MCP gateway
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── services/         # API client + Gemini
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
├── client/
│   ├── client.py             # LangChain MCP client
│   └── client1.py            # LangGraph agent
├── .env                       # Environment variables
└── pyproject.toml            # Python dependencies
```

## Setup Instructions

### 1. Install Python Dependencies

```bash
# Core dependencies
uv add fastmcp motor pymongo certifi python-dotenv

# FastAPI auth dependencies
uv add fastapi uvicorn python-jose[cryptography] passlib[bcrypt] httpx

# LangChain/LangGraph dependencies (optional, for agents)
uv add langchain langchain-google-genai langgraph langchain-mcp-adapters
```

### 2. Configure Environment Variables

Update `.env`:
```bash
# MongoDB Atlas
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?appName=Cluster1

# JWT Secret (generate with: openssl rand -hex 32)
JWT_SECRET_KEY=your-secret-key-here

# Gemini API Key
GEMINI_API_KEY=your-gemini-api-key

# MCP Server URL (if deployed separately)
MCP_SERVER_URL=http://localhost:8000
```

Update `frontend/.env`:
```bash
VITE_GEMINI_API_KEY=your-gemini-api-key
```

### 3. Initialize Database

Run database setup once:
```bash
# Start MCP server
uv run fastmcp dev main.py --ui-port 8888

# In MCP Inspector, call:
setup_database()
```

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 5. Run All Services

**Terminal 1 - MCP Server (Port 8000):**
```bash
uv run fastmcp run main.py
```

**Terminal 2 - FastAPI Auth (Port 8001):**
```bash
cd fastapi_auth
uvicorn main:app --port 8001 --reload
```

**Terminal 3 - React Frontend (Port 5173):**
```bash
cd frontend
npm run dev
```

### 6. Access the Application

Open browser: `http://localhost:5173`

## Security Features

✅ **HttpOnly Secure Cookies** - JWT stored in HttpOnly cookies, not localStorage
✅ **Password Hashing** - Bcrypt with salt rounds
✅ **User Data Isolation** - All queries filtered by user_id
✅ **CORS Protection** - Configured for specific origins
✅ **SameSite=Strict** - CSRF protection

## API Endpoints

### Authentication (Port 8001)
- `POST /auth/signup` - Create account
- `POST /auth/login` - Login (sets cookie)
- `POST /auth/logout` - Logout (clears cookie)
- `GET /auth/me` - Get current user

### MCP Gateway (Port 8001)
- `POST /mcp/execute` - Execute MCP tools (requires auth)

### MCP Tools (Port 8000)
- `add_expense(user_id, date, amount, category, subcategory, note)`
- `list_expenses(user_id, start_date, end_date)`
- `summarize(user_id, start_date, end_date, category?)`
- `delete_expense(user_id, expense_id)`
- `setup_database()` - Admin only

## Usage Flow

1. **User signs up** → FastAPI creates user in MongoDB
2. **User logs in** → FastAPI returns JWT in HttpOnly cookie
3. **User types**: "Add coffee expense of $5 today"
4. **Frontend → Gemini** → Parses to: `{"tool": "add_expense", "args": {...}}`
5. **Frontend → FastAPI** → Attaches user_id from JWT
6. **FastAPI → MCP** → Executes tool with user_id
7. **MCP → MongoDB** → Stores expense with user_id filter

## Key Technologies

- **FastMCP**: MCP protocol server
- **FastAPI**: Authentication & gateway
- **React + Vite**: Frontend framework
- **Gemini Flash 2.0**: Natural language → tool calls
- **Motor**: Async MongoDB driver
- **Tailwind CSS**: Styling
- **JWT**: Secure authentication
- **MongoDB Atlas**: Cloud database

## Production Deployment

1. **Environment Variables**:
   - Set strong JWT_SECRET_KEY
   - Use production MongoDB cluster
   - Enable MongoDB IP whitelist

2. **HTTPS**:
   - Enable `secure=True` in cookie settings
   - Use reverse proxy (Nginx/Caddy)

3. **CORS**:
   - Update `allow_origins` to production domain
   - Remove localhost origins

4. **Monitoring**:
   - Add logging middleware
   - Monitor MongoDB connection pool
   - Track API response times

## Troubleshooting

**SSL Handshake Error:**
- Ensure IP is whitelisted in MongoDB Atlas
- Check certifi is installed: `uv add certifi`

**Cookie Not Set:**
- Verify `withCredentials: true` in axios
- Check CORS `allow_credentials=True`
- Ensure same domain/subdomain

**Gemini Parse Error:**
- Check VITE_GEMINI_API_KEY is set
- Verify Gemini API quota
- Review error message in console

## License

MIT
