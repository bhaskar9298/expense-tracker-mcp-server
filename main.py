# main.py - FastMCP Expense Tracker server with user_id filtering

from fastmcp import FastMCP
from datetime import datetime

from db.client import expenses_col, client

mcp = FastMCP("ExpenseTracker")

# -----------------------
# Utility: serialize Mongo docs
# -----------------------
def serialize(doc):
    doc = dict(doc)
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc

# -----------------------
# MCP TOOLS (with user_id filtering)
# -----------------------
@mcp.tool()
async def add_expense(user_id: str, date: str, amount: float, category: str, subcategory: str = "", note: str = ""):
    """
    Add a new expense document for authenticated user.
    user_id is automatically injected by FastAPI gateway.
    """
    try:
        doc = {
            "user_id": user_id,
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
async def list_expenses(user_id: str, start_date: str, end_date: str):
    """
    List all expenses for authenticated user in date range.
    user_id is automatically injected by FastAPI gateway.
    """
    try:
        cursor = expenses_col.find(
            {
                "user_id": user_id,
                "date": {"$gte": start_date, "$lte": end_date}
            }
        ).sort([("date", -1), ("_id", -1)])

        output = []
        async for doc in cursor:
            output.append(serialize(doc))

        return output
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def summarize(user_id: str, start_date: str, end_date: str, category: str = None):
    """
    Summarize spending by category for authenticated user.
    user_id is automatically injected by FastAPI gateway.
    """
    try:
        match = {
            "user_id": user_id,
            "date": {"$gte": start_date, "$lte": end_date}
        }
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
async def delete_expense(user_id: str, expense_id: str):
    """
    Delete an expense for authenticated user.
    user_id is automatically injected by FastAPI gateway.
    """
    try:
        from bson import ObjectId
        result = await expenses_col.delete_one({
            "_id": ObjectId(expense_id),
            "user_id": user_id  # Ensure user can only delete their own expenses
        })
        
        if result.deleted_count == 0:
            return {"status": "error", "message": "Expense not found or access denied"}
        
        return {"status": "success", "message": "Expense deleted"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def setup_database():
    """
    Initialize database schema and indexes.
    Admin tool - should be called once during setup.
    """
    from db.init import setup_collection_hybrid
    try:
        await setup_collection_hybrid()
        return {"status": "success", "message": "Database initialized successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
if __name__ == "__main":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
