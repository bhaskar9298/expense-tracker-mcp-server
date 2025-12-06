# 🤖 AI-Powered Expense Tracker with MCP

A production-ready expense tracking system combining **FastMCP**, **FastAPI**, **React**, and **Gemini AI** for natural language expense management.

## ✨ Features

- 🔐 **Secure Authentication** - JWT with HttpOnly cookies
- 🤖 **AI Natural Language** - "Add coffee expense of $5 today"
- 📊 **Visual Analytics** - Category summaries with charts
- 🔒 **User Data Isolation** - Multi-tenant MongoDB architecture
- ⚡ **Real-time Updates** - Async operations with Motor
- 🎨 **Modern UI** - Tailwind CSS with responsive design

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   React     │ ───▶ │   FastAPI    │ ───▶ │   FastMCP   │
│  Frontend   │      │    Auth      │      │   Server    │
└─────────────┘      └──────────────┘      └─────────────┘
       │                     │                      │
       │                     │                      │
       ▼                     ▼                      ▼
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Gemini    │      │  JWT Cookies │      │  MongoDB    │
│   Flash     │      │   (HttpOnly) │      │   Atlas     │
└─────────────┘      └──────────────┘      └─────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- MongoDB Atlas account
- Gemini API key

### 1. Clone & Install

```bash
# Install Python dependencies
uv add fastmcp motor pymongo certifi python-dotenv fastapi uvicorn python-jose[cryptography] passlib[bcrypt] httpx

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Configure Environment

Create `.env`:
```bash
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
JWT_SECRET_KEY=your-secret-key-here
GEMINI_API_KEY=your-gemini-api-key
```

Create `frontend/.env`:
```bash
VITE_GEMINI_API_KEY=your-gemini-api-key
```

### 3. Initialize Database

```bash
uv run fastmcp dev main.py --ui-port 8888
# In inspector, call: setup_database()
```

### 4. Start All Services

**Option A - Manual (3 terminals):**
```bash
# Terminal 1
uv run fastmcp run main.py

# Terminal 2
cd fastapi_auth && uvicorn main:app --port 8001 --reload

# Terminal 3
cd frontend && npm run dev
```

**Option B - Script (Windows):**
```bash
start.bat
```

**Option B - Script (Linux/Mac):**
```bash
chmod +x start.sh
./start.sh
```

### 5. Open Browser

Navigate to `http://localhost:5173`

## 📖 Usage Examples

### Natural Language Commands

```
"Add coffee expense of $5 today"
"Add lunch at $15 yesterday"
"Show my expenses from last week"
"Show expenses from 2025-12-01 to 2025-12-31"
"Summarize my spending this month"
"Summarize food expenses"
```

### API Usage (via FastAPI)

```bash
# Signup
curl -X POST http://localhost:8001/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass123"}'

# Login
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass123"}' \
  -c cookies.txt

# Add expense via MCP
curl -X POST http://localhost:8001/mcp/execute \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"tool":"add_expense","args":{"date":"2025-12-06","amount":5,"category":"Food"}}'
```

## 🔐 Security Features

✅ **HttpOnly Cookies** - XSS protection  
✅ **Bcrypt Hashing** - Secure passwords  
✅ **JWT Tokens** - Stateless authentication  
✅ **User Isolation** - MongoDB user_id filtering  
✅ **CORS Protection** - Origin whitelist  
✅ **SameSite Cookies** - CSRF protection  

## 📁 Project Structure

```
expense-tracker-mcp-server/
├── main.py                 # FastMCP server
├── db/                     # Database layer
│   ├── client.py          # MongoDB connection
│   ├── schema.py          # JSON schemas
│   └── init.py            # Initialization
├── fastapi_auth/          # Auth backend
│   └── main.py            # FastAPI app
├── frontend/              # React app
│   ├── src/
│   │   ├── components/   # UI components
│   │   ├── services/     # API + Gemini
│   │   └── App.jsx
│   └── package.json
└── client/                # LangChain agents
```

## 🛠️ MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `add_expense` | Add new expense | `user_id, date, amount, category, subcategory?, note?` |
| `list_expenses` | List expenses | `user_id, start_date, end_date` |
| `summarize` | Category summary | `user_id, start_date, end_date, category?` |
| `delete_expense` | Delete expense | `user_id, expense_id` |
| `setup_database` | Initialize DB | none (admin) |

## 🧪 Testing

```bash
# Run MCP server tests
uv run python test_mongo.py

# Test frontend
cd frontend
npm run build
npm run preview
```

## 📊 MongoDB Collections

### users
```javascript
{
  "_id": ObjectId("..."),
  "email": "user@example.com",
  "password_hash": "$2b$12$...",
  "full_name": "John Doe",
  "created_at": ISODate("..."),
  "updated_at": ISODate("...")
}
```

### expenses
```javascript
{
  "_id": ObjectId("..."),
  "user_id": "675a...",
  "date": "2025-12-06",
  "amount": 5.0,
  "category": "Food",
  "subcategory": "Coffee",
  "note": "Morning coffee",
  "created_at": ISODate("...")
}
```

## 🐛 Troubleshooting

**Issue: SSL Handshake Error**
- Whitelist your IP in MongoDB Atlas Network Access
- Verify `certifi` is installed: `uv add certifi`

**Issue: Cookie Not Set**
- Check `withCredentials: true` in axios
- Verify CORS `allow_credentials=True`
- Ensure same domain for dev (use Vite proxy)

**Issue: Gemini API Error**
- Verify `VITE_GEMINI_API_KEY` in `frontend/.env`
- Check API quota at Google AI Studio
- Review browser console for errors

## 📚 Documentation

- [Setup Guide](SETUP_GUIDE.md) - Detailed setup instructions
- [Project Summary](PROJECT_SUMMARY.md) - Complete feature list
- [FastMCP Docs](https://gofastmcp.com)
- [FastAPI Docs](https://fastapi.tiangolo.com)

## 🚀 Deployment

### Production Checklist

- [ ] Set strong `JWT_SECRET_KEY` (32+ chars)
- [ ] Use production MongoDB cluster
- [ ] Enable MongoDB IP whitelist
- [ ] Set `secure=True` for cookies (HTTPS)
- [ ] Update CORS origins to production domain
- [ ] Add logging middleware
- [ ] Set up monitoring (Sentry, etc.)
- [ ] Configure rate limiting
- [ ] Enable database backups

### Deployment Options

- **Vercel** - Frontend
- **Railway/Render** - FastAPI + FastMCP
- **MongoDB Atlas** - Database
- **Cloudflare** - CDN + DDoS protection

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- [FastMCP](https://gofastmcp.com) - MCP protocol server
- [LangChain](https://langchain.com) - LLM framework
- [Gemini](https://ai.google.dev) - Google's AI models
- [FastAPI](https://fastapi.tiangolo.com) - Modern Python API framework

## 📧 Support

For issues and questions:
- 📖 [Documentation](SETUP_GUIDE.md)
- 🐛 [GitHub Issues](https://github.com/yourusername/expense-tracker/issues)
- 💬 [Discussions](https://github.com/yourusername/expense-tracker/discussions)

---

Made with ❤️ using FastMCP, FastAPI, React, and Gemini AI
