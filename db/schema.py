# db/schema.py - JSON Schema mirroring SQLite schema

expense_json_schema = {
    "bsonType": "object",
    "required": ["date", "amount", "category"],
    "properties": {
        "date": {
            "bsonType": "string",
            "description": "Date string (prefer ISO format)"
        },
        "amount": {
            "bsonType": ["double", "int", "decimal"],
            "description": "Expense amount"
        },
        "category": {
            "bsonType": "string",
            "description": "Expense category"
        },
        "subcategory": {
            "bsonType": "string",
            "description": "Optional subcategory"
        },
        "note": {
            "bsonType": "string",
            "description": "Optional note"
        },
        "created_at": {
            "bsonType": "date",
            "description": "Auto-added timestamp"
        }
    },
    "additionalProperties": True   # Allow extra fields (AI-driven flexibility)
}
