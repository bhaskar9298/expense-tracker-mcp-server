# db/schema.py - JSON Schema with user_id filtering

expense_json_schema = {
    "bsonType": "object",
    "required": ["user_id", "date", "amount", "category"],
    "properties": {
        "user_id": {
            "bsonType": "string",
            "description": "User ID from JWT - isolates user data"
        },
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
    "additionalProperties": True
}

user_json_schema = {
    "bsonType": "object",
    "required": ["email", "password_hash"],
    "properties": {
        "email": {
            "bsonType": "string",
            "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
            "description": "User email (unique)"
        },
        "password_hash": {
            "bsonType": "string",
            "description": "Bcrypt hashed password"
        },
        "full_name": {
            "bsonType": "string",
            "description": "User's full name"
        },
        "created_at": {
            "bsonType": "date",
            "description": "Account creation timestamp"
        },
        "updated_at": {
            "bsonType": "date",
            "description": "Last update timestamp"
        }
    }
}
