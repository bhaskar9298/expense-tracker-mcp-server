# db/init.py - Initialize both users and expenses collections

from .client import db, expenses_col
from .schema import expense_json_schema, user_json_schema
from datetime import datetime
from pymongo.errors import OperationFailure
import logging

logger = logging.getLogger(__name__)

async def setup_collection_hybrid():
    """
    Creates collections if missing, applies schema validators,
    creates indexes, and performs test write.
    """
    
    # Setup expenses collection
    await setup_expenses_collection()
    
    # Setup users collection
    await setup_users_collection()

async def setup_expenses_collection():
    """Setup expenses collection with user_id index"""
    cname = "expenses"
    
    try:
        existing = await db.list_collection_names()
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise

    if cname not in existing:
        try:
            await db.create_collection(
                cname,
                validator={"$jsonSchema": expense_json_schema},
                validationLevel="moderate",
                validationAction="error"
            )
            print(f"[OK] Created '{cname}' with JSON-schema validator.")
        except Exception as e:
            await db.create_collection(cname)
            print(f"[OK] Created '{cname}' WITHOUT validator. Details: {e}")
    else:
        try:
            await db.command({
                "collMod": cname,
                "validator": {"$jsonSchema": expense_json_schema},
                "validationLevel": "moderate",
                "validationAction": "error"
            })
            print(f"[OK] Validator updated on '{cname}'.")
        except OperationFailure:
            print(f"[WARN] collMod restricted; continuing without update.")
        except Exception as e:
            print(f"[WARN] collMod error: {e}")

    # Indexes for expenses
    try:
        await expenses_col.create_index([("user_id", 1), ("date", -1)], name="idx_user_date")
        await expenses_col.create_index([("user_id", 1), ("category", 1)], name="idx_user_category")
        await expenses_col.create_index([("date", -1)], name="idx_date_desc")
        print("[OK] Expense indexes ensured.")
    except Exception as e:
        logger.warning(f"Index creation issue: {e}")

    # Test write
    try:
        test_doc = {
            "user_id": "test_user",
            "date": "2000-01-01",
            "amount": 0,
            "category": "test",
            "subcategory": "",
            "note": "init-test",
            "created_at": datetime.utcnow()
        }
        inserted = await expenses_col.insert_one(test_doc)
        await expenses_col.delete_one({"_id": inserted.inserted_id})
        print("[OK] Expense test write OK.")
    except Exception as e:
        logger.error(f"Test write failed: {e}")
        raise

async def setup_users_collection():
    """Setup users collection with email index"""
    cname = "users"
    users_col = db[cname]
    
    try:
        existing = await db.list_collection_names()
        
        if cname not in existing:
            try:
                await db.create_collection(
                    cname,
                    validator={"$jsonSchema": user_json_schema},
                    validationLevel="moderate",
                    validationAction="error"
                )
                print(f"[OK] Created '{cname}' with validator.")
            except Exception as e:
                await db.create_collection(cname)
                print(f"[OK] Created '{cname}' WITHOUT validator. Details: {e}")
        
        # Unique index on email
        await users_col.create_index([("email", 1)], unique=True, name="idx_email_unique")
        print("[OK] User indexes ensured.")
        
    except Exception as e:
        logger.warning(f"User collection setup issue: {e}")
