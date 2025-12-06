# main.py - FastMCP Expense Tracker server (Modular Architecture)

from fastmcp import FastMCP
from datetime import datetime

from db.client import expenses_col, client

mcp = FastMCP("ExpenseTracker")

# -----------------------
# Simple test tool
# -----------------------
# @mcp.tool()
# def ping():
#     """Simple ping test - returns pong"""
#     return {"status": "success", "message": "pong"}

# @mcp.tool()
# async def test_connection():
#     """Test MongoDB connection"""
#     try:
#         await client.admin.command('ping')
#         return {"status": "success", "message": "MongoDB connection successful"}
#     except Exception as e:
#         return {"status": "error", "message": f"Connection failed: {str(e)}"}

# -----------------------
# Utility: serialize Mongo docs
# -----------------------
def serialize(doc):
    doc = dict(doc)
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc

# -----------------------
# MCP TOOLS
# -----------------------
@mcp.tool()
async def add_expense(date: str, amount: float, category: str, subcategory: str = "", note: str = ""):
    """
    Add a new expense document.
    Triggered by natural language: "Add milk expense for 8 rupees today"
    """
    try:
        doc = {
            "date": date,
            "amount": float(amount),
            "category": category,
            "subcategory": subcategory or "",
            "note": note or "",
            "created_at": datetime.utcnow()
        }
        res = await expenses_col.insert_one(doc)
        return {"status": "success", "id": str(res.inserted_id)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def list_expenses(start_date: str, end_date: str):
    """
    List all expenses in the date range.
    Example prompt: "List my expenses from Jan 1 to Jan 10"
    """
    try:
        cursor = expenses_col.find(
            {"date": {"$gte": start_date, "$lte": end_date}}
        ).sort([("date", -1), ("_id", -1)])

        output = []
        async for doc in cursor:
            output.append(serialize(doc))

        return output
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def summarize(start_date: str, end_date: str, category: str = None):
    """
    Summarize spending by category.
    Example prompt: "Summarize my food expenses for this month"
    """
    try:
        match = {"date": {"$gte": start_date, "$lte": end_date}}
        if category:
            match["category"] = category

        pipeline = [
            {"$match": match},
            {"$group": {
                "_id": "$category",
                "total_amount": {"$sum": "$amount"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"total_amount": -1}}
        ]

        cursor = expenses_col.aggregate(pipeline)
        out = []

        async for doc in cursor:
            out.append({
                "category": doc["_id"],
                "total_amount": doc["total_amount"],
                "count": doc["count"]
            })

        return out
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def setup_database():
    """
    Initialize database schema and indexes. Call this once before using other tools.
    """
    from db.init import setup_collection_hybrid
    try:
        await setup_collection_hybrid()
        return {"status": "success", "message": "Database initialized successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
