# db/init.py - Hybrid schema initialisation + test write

from .client import db, expenses_col
from .schema import expense_json_schema
from datetime import datetime
from pymongo.errors import OperationFailure
import logging

logger = logging.getLogger(__name__)

async def setup_collection_hybrid():
    """
    Creates collection if missing, applies schema validator,
    creates indexes, and performs test write.
    """
    cname = "expenses"
    
    try:
        existing = await db.list_collection_names()
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise

    # Create collection + validator if missing
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
            print(f"[OK] Created '{cname}' WITHOUT validator (provider restricted). Details: {e}")

    else:
        # Try updating validator using collMod
        try:
            await db.command({
                "collMod": cname,
                "validator": {"$jsonSchema": expense_json_schema},
                "validationLevel": "moderate",
                "validationAction": "error"
            })
            print(f"[OK] Validator updated on existing collection '{cname}'.")
        except OperationFailure as e:
            print(f"[WARN] collMod restricted by cluster; continuing without update.")
        except Exception as e:
            print(f"[WARN] collMod error (ignored): {e}")

    # Indexes
    try:
        await expenses_col.create_index([("date", -1)], name="idx_date_desc")
        await expenses_col.create_index([("category", 1)], name="idx_category")
        print("[OK] Indexes ensured.")
    except Exception as e:
        logger.warning(f"Index creation issue: {e}")

    # Test write (your SQLite WAL test equivalent)
    try:
        test_doc = {
            "date": "2000-01-01",
            "amount": 0,
            "category": "test",
            "subcategory": "",
            "note": "init-test",
            "created_at": datetime.utcnow()
        }

        inserted = await expenses_col.insert_one(test_doc)
        await expenses_col.delete_one({"_id": inserted.inserted_id})
        print("[OK] MongoDB test write OK (insert + delete).")
    except Exception as e:
        logger.error(f"Test write failed: {e}")
        raise
