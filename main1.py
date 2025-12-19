# server.py - FastMCP Expense Tracker Server
# Phase 0: Personal expense tracking with user_id filtering
# Phase 1: Database schema extended for group management
# Phase 2: Group Management and Member Management tools
# Phase 3: Multi-User Expense Splitting

from fastmcp import FastMCP
from datetime import datetime
from bson import ObjectId

import sys
import pathlib
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db.client import (
    expenses_col, 
    groups_col, 
    group_members_col,
    expense_participants_col,
    users_col,
    client
)
from server.utils.authorization import (
    is_user_in_group,
    is_user_group_admin,
    get_user_by_email,
    can_user_modify_group,
    can_user_add_members,
    can_user_remove_members,
    get_group_member_count,
    verify_group_exists
)
from server.utils.splits import (
    calculate_splits,
    format_split_summary
)
from decimal import Decimal

mcp = FastMCP("ExpenseTracker")

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def serialize(doc):
    """Convert MongoDB document to JSON-serializable dict"""
    doc = dict(doc)
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc

def validate_object_id(id_str: str) -> bool:
    """Check if string is a valid MongoDB ObjectId"""
    try:
        ObjectId(id_str)
        return True
    except Exception:
        return False

# ============================================================================
# PHASE 0 & 1: EXPENSE MANAGEMENT (Backward Compatible)
# ============================================================================

@mcp.tool()
async def add_expense(user_id: str, date: str, amount: float, category: str, subcategory: str = "", note: str = ""):
    """
    Add a new expense document for authenticated user.
    user_id is automatically injected by FastAPI gateway.
    
    Phase 0: Personal expenses
    Phase 1: Enhanced with optional group_id (for migration compatibility)
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
        if not validate_object_id(expense_id):
            return {"status": "error", "message": "Invalid expense ID format"}
        
        result = await expenses_col.delete_one({
            "_id": ObjectId(expense_id),
            "user_id": user_id  # Ensure user can only delete their own expenses
        })
        
        if result.deleted_count == 0:
            return {"status": "error", "message": "Expense not found or access denied"}
        
        return {"status": "success", "message": "Expense deleted"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ============================================================================
# PHASE 2: GROUP MANAGEMENT
# ============================================================================

@mcp.tool()
async def create_group(user_id: str, name: str, description: str = ""):
    """
    Create a new shared group.
    Creator automatically becomes admin.
    
    Args:
        user_id: User creating the group (injected by FastAPI)
        name: Group name (required, 1-100 chars)
        description: Optional group description (max 500 chars)
        
    Returns:
        {"status": "success", "group_id": "...", "group": {...}}
        or {"status": "error", "message": "..."}
    """
    try:
        # Validate input
        if not name or len(name.strip()) == 0:
            return {"status": "error", "message": "Group name is required"}
        
        if len(name) > 100:
            return {"status": "error", "message": "Group name must be 100 characters or less"}
        
        if len(description) > 500:
            return {"status": "error", "message": "Description must be 500 characters or less"}
        
        # Create group document
        group_doc = {
            "name": name.strip(),
            "description": description.strip() if description else "",
            "created_by": user_id,
            "is_active": True,
            "group_type": "shared",  # Phase 2: Only shared groups (personal groups created by migration)
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert group
        result = await groups_col.insert_one(group_doc)
        group_id = str(result.inserted_id)
        
        # Add creator as admin member
        member_doc = {
            "group_id": group_id,
            "user_id": user_id,
            "role": "admin",
            "is_active": True,
            "joined_at": datetime.utcnow()
        }
        await group_members_col.insert_one(member_doc)
        
        # Return created group
        group_doc["id"] = group_id
        del group_doc["_id"]
        
        return {
            "status": "success",
            "group_id": group_id,
            "group": group_doc,
            "message": f"Group '{name}' created successfully"
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to create group: {str(e)}"}

@mcp.tool()
async def list_groups(user_id: str):
    """
    List all groups user is a member of.
    
    Args:
        user_id: User ID (injected by FastAPI)
        
    Returns:
        List of groups with member count and user's role
    """
    try:
        # Get all active memberships
        memberships = await group_members_col.find({
            "user_id": user_id,
            "is_active": True
        }).to_list(None)
        
        if not memberships:
            return []
        
        # Get group IDs
        group_ids = [ObjectId(m["group_id"]) for m in memberships]
        
        # Get groups
        groups = await groups_col.find({
            "_id": {"$in": group_ids},
            "is_active": True
        }).to_list(None)
        
        # Create role lookup
        role_map = {m["group_id"]: m["role"] for m in memberships}
        
        # Enrich groups with member count and role
        result = []
        for group in groups:
            group_id = str(group["_id"])
            member_count = await get_group_member_count(group_id)
            
            group_data = serialize(group)
            group_data["member_count"] = member_count
            group_data["your_role"] = role_map.get(group_id, "member")
            
            result.append(group_data)
        
        # Sort: personal groups first, then by creation date
        result.sort(key=lambda g: (g.get("group_type") != "personal", g.get("created_at")), reverse=True)
        
        return result
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to list groups: {str(e)}"}

@mcp.tool()
async def get_group_details(user_id: str, group_id: str):
    """
    Get detailed information about a group including members.
    User must be a member of the group.
    
    Args:
        user_id: User ID (injected by FastAPI)
        group_id: Group ID to retrieve
        
    Returns:
        Group details with list of members
    """
    try:
        # Validate group_id format
        if not validate_object_id(group_id):
            return {"status": "error", "message": "Invalid group ID format"}
        
        # Check if user is member
        if not await is_user_in_group(user_id, group_id):
            return {"status": "error", "message": "Access denied: You are not a member of this group"}
        
        # Get group
        group = await groups_col.find_one({
            "_id": ObjectId(group_id),
            "is_active": True
        })
        
        if not group:
            return {"status": "error", "message": "Group not found"}
        
        # Get members
        memberships = await group_members_col.find({
            "group_id": group_id,
            "is_active": True
        }).to_list(None)
        
        # Get user details for members
        user_ids = [ObjectId(m["user_id"]) for m in memberships]
        users = await users_col.find({"_id": {"$in": user_ids}}).to_list(None)
        user_map = {str(u["_id"]): u for u in users}
        
        # Build member list
        members = []
        for membership in memberships:
            uid = membership["user_id"]
            user = user_map.get(uid, {})
            
            members.append({
                "user_id": uid,
                "email": user.get("email", "Unknown"),
                "full_name": user.get("full_name", "Unknown User"),
                "role": membership["role"],
                "joined_at": membership["joined_at"].isoformat() if membership.get("joined_at") else None
            })
        
        # Sort members: admins first, then by join date
        members.sort(key=lambda m: (m["role"] != "admin", m.get("joined_at", "")))
        
        # Prepare response
        group_data = serialize(group)
        group_data["members"] = members
        group_data["member_count"] = len(members)
        group_data["your_role"] = next((m["role"] for m in members if m["user_id"] == user_id), "member")
        
        return group_data
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to get group details: {str(e)}"}

@mcp.tool()
async def update_group(user_id: str, group_id: str, name: str = None, description: str = None):
    """
    Update group information.
    Only admins can update group details.
    
    Args:
        user_id: User ID (injected by FastAPI)
        group_id: Group ID to update
        name: New group name (optional)
        description: New description (optional)
        
    Returns:
        Updated group details
    """
    try:
        # Validate group_id
        if not validate_object_id(group_id):
            return {"status": "error", "message": "Invalid group ID format"}
        
        # Check if user can modify group
        if not await can_user_modify_group(user_id, group_id):
            return {"status": "error", "message": "Access denied: Only admins can update group details"}
        
        # Check if group exists
        if not await verify_group_exists(group_id):
            return {"status": "error", "message": "Group not found"}
        
        # Build update document
        update_doc = {"updated_at": datetime.utcnow()}
        
        if name is not None:
            if len(name.strip()) == 0:
                return {"status": "error", "message": "Group name cannot be empty"}
            if len(name) > 100:
                return {"status": "error", "message": "Group name must be 100 characters or less"}
            update_doc["name"] = name.strip()
        
        if description is not None:
            if len(description) > 500:
                return {"status": "error", "message": "Description must be 500 characters or less"}
            update_doc["description"] = description.strip()
        
        # Check if any personal group (cannot be updated)
        group = await groups_col.find_one({"_id": ObjectId(group_id)})
        if group and group.get("group_type") == "personal":
            return {"status": "error", "message": "Cannot update personal groups"}
        
        # Update group
        result = await groups_col.update_one(
            {"_id": ObjectId(group_id)},
            {"$set": update_doc}
        )
        
        if result.modified_count == 0:
            return {"status": "error", "message": "No changes made"}
        
        # Get updated group
        updated_group = await groups_col.find_one({"_id": ObjectId(group_id)})
        
        return {
            "status": "success",
            "message": "Group updated successfully",
            "group": serialize(updated_group)
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to update group: {str(e)}"}

@mcp.tool()
async def delete_group(user_id: str, group_id: str):
    """
    Soft delete a group (marks as inactive).
    Only group creator/admin can delete.
    Cannot delete personal groups.
    
    Args:
        user_id: User ID (injected by FastAPI)
        group_id: Group ID to delete
        
    Returns:
        Success/error status
    """
    try:
        # Validate group_id
        if not validate_object_id(group_id):
            return {"status": "error", "message": "Invalid group ID format"}
        
        # Check if user can modify group
        if not await can_user_modify_group(user_id, group_id):
            return {"status": "error", "message": "Access denied: Only admins can delete groups"}
        
        # Get group
        group = await groups_col.find_one({"_id": ObjectId(group_id), "is_active": True})
        
        if not group:
            return {"status": "error", "message": "Group not found"}
        
        # Cannot delete personal groups
        if group.get("group_type") == "personal":
            return {"status": "error", "message": "Cannot delete personal groups"}
        
        # Soft delete group
        await groups_col.update_one(
            {"_id": ObjectId(group_id)},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        
        # Deactivate all memberships
        await group_members_col.update_many(
            {"group_id": group_id, "is_active": True},
            {"$set": {"is_active": False, "left_at": datetime.utcnow()}}
        )
        
        return {
            "status": "success",
            "message": f"Group '{group['name']}' deleted successfully"
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to delete group: {str(e)}"}

# ============================================================================
# PHASE 2: GROUP MEMBER MANAGEMENT
# ============================================================================

@mcp.tool()
async def add_group_member(user_id: str, group_id: str, member_email: str, role: str = "member"):
    """
    Add a new member to a group.
    Only admins can add members.
    
    Args:
        user_id: User ID (injected by FastAPI)
        group_id: Group ID
        member_email: Email of user to add
        role: Role for new member ("admin" or "member", default "member")
        
    Returns:
        Success status and member details
    """
    try:
        # Validate inputs
        if not validate_object_id(group_id):
            return {"status": "error", "message": "Invalid group ID format"}
        
        if not member_email or "@" not in member_email:
            return {"status": "error", "message": "Valid email address required"}
        
        if role not in ["admin", "member"]:
            return {"status": "error", "message": "Role must be 'admin' or 'member'"}
        
        # Check if requesting user can add members
        if not await can_user_add_members(user_id, group_id):
            return {"status": "error", "message": "Access denied: Only admins can add members"}
        
        # Check if group exists
        if not await verify_group_exists(group_id):
            return {"status": "error", "message": "Group not found"}
        
        # Find user by email
        new_user = await get_user_by_email(member_email)
        if not new_user:
            return {"status": "error", "message": f"User with email '{member_email}' not found"}
        
        new_user_id = str(new_user["_id"])
        
        # Check if already a member
        existing_member = await group_members_col.find_one({
            "group_id": group_id,
            "user_id": new_user_id,
            "is_active": True
        })
        
        if existing_member:
            return {"status": "error", "message": "User is already a member of this group"}
        
        # Add member
        member_doc = {
            "group_id": group_id,
            "user_id": new_user_id,
            "role": role,
            "is_active": True,
            "joined_at": datetime.utcnow()
        }
        
        await group_members_col.insert_one(member_doc)
        
        return {
            "status": "success",
            "message": f"User '{member_email}' added to group as {role}",
            "member": {
                "user_id": new_user_id,
                "email": new_user.get("email"),
                "full_name": new_user.get("full_name", "Unknown User"),
                "role": role
            }
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to add member: {str(e)}"}

@mcp.tool()
async def remove_group_member(user_id: str, group_id: str, member_user_id: str):
    """
    Remove a member from a group.
    Only admins can remove members.
    Cannot remove yourself or the last admin.
    
    Args:
        user_id: User ID (injected by FastAPI)
        group_id: Group ID
        member_user_id: User ID of member to remove
        
    Returns:
        Success/error status
    """
    try:
        # Validate inputs
        if not validate_object_id(group_id):
            return {"status": "error", "message": "Invalid group ID format"}
        
        # Check if user can remove members
        if not await can_user_remove_members(user_id, group_id):
            return {"status": "error", "message": "Access denied: Only admins can remove members"}
        
        # Cannot remove yourself (use leave_group instead)
        if member_user_id == user_id:
            return {"status": "error", "message": "Cannot remove yourself. Use leave_group instead"}
        
        # Check if member exists
        member = await group_members_col.find_one({
            "group_id": group_id,
            "user_id": member_user_id,
            "is_active": True
        })
        
        if not member:
            return {"status": "error", "message": "Member not found in this group"}
        
        # Check if removing last admin
        if member["role"] == "admin":
            admin_count = await group_members_col.count_documents({
                "group_id": group_id,
                "role": "admin",
                "is_active": True
            })
            
            if admin_count <= 1:
                return {"status": "error", "message": "Cannot remove the last admin. Promote another member first"}
        
        # Remove member (soft delete)
        await group_members_col.update_one(
            {"_id": member["_id"]},
            {"$set": {"is_active": False, "left_at": datetime.utcnow()}}
        )
        
        # Get user details for response
        user = await users_col.find_one({"_id": ObjectId(member_user_id)})
        user_email = user.get("email", "Unknown") if user else "Unknown"
        
        return {
            "status": "success",
            "message": f"Member '{user_email}' removed from group"
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to remove member: {str(e)}"}

@mcp.tool()
async def leave_group(user_id: str, group_id: str):
    """
    Leave a group.
    Cannot leave personal groups.
    If last admin, must promote someone else first.
    
    Args:
        user_id: User ID (injected by FastAPI)
        group_id: Group ID to leave
        
    Returns:
        Success/error status
    """
    try:
        # Validate group_id
        if not validate_object_id(group_id):
            return {"status": "error", "message": "Invalid group ID format"}
        
        # Check if member of group
        member = await group_members_col.find_one({
            "group_id": group_id,
            "user_id": user_id,
            "is_active": True
        })
        
        if not member:
            return {"status": "error", "message": "You are not a member of this group"}
        
        # Get group
        group = await groups_col.find_one({"_id": ObjectId(group_id)})
        
        if not group:
            return {"status": "error", "message": "Group not found"}
        
        # Cannot leave personal groups
        if group.get("group_type") == "personal":
            return {"status": "error", "message": "Cannot leave personal groups"}
        
        # If admin, check if last admin
        if member["role"] == "admin":
            admin_count = await group_members_col.count_documents({
                "group_id": group_id,
                "role": "admin",
                "is_active": True
            })
            
            if admin_count <= 1:
                return {"status": "error", "message": "Cannot leave: You are the last admin. Promote another member or delete the group"}
        
        # Leave group
        await group_members_col.update_one(
            {"_id": member["_id"]},
            {"$set": {"is_active": False, "left_at": datetime.utcnow()}}
        )
        
        return {
            "status": "success",
            "message": f"You have left the group '{group['name']}'"
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to leave group: {str(e)}"}

@mcp.tool()
async def get_group_members(user_id: str, group_id: str):
    """
    Get list of all members in a group.
    User must be a member of the group.
    
    Args:
        user_id: User ID (injected by FastAPI)
        group_id: Group ID
        
    Returns:
        List of group members with details
    """
    try:
        # Validate group_id
        if not validate_object_id(group_id):
            return {"status": "error", "message": "Invalid group ID format"}
        
        # Check if user is member
        if not await is_user_in_group(user_id, group_id):
            return {"status": "error", "message": "Access denied: You are not a member of this group"}
        
        # Get memberships
        memberships = await group_members_col.find({
            "group_id": group_id,
            "is_active": True
        }).to_list(None)
        
        if not memberships:
            return []
        
        # Get user details
        user_ids = [ObjectId(m["user_id"]) for m in memberships]
        users = await users_col.find({"_id": {"$in": user_ids}}).to_list(None)
        user_map = {str(u["_id"]): u for u in users}
        
        # Build member list
        members = []
        for membership in memberships:
            uid = membership["user_id"]
            user = user_map.get(uid, {})
            
            members.append({
                "user_id": uid,
                "email": user.get("email", "Unknown"),
                "full_name": user.get("full_name", "Unknown User"),
                "role": membership["role"],
                "joined_at": membership["joined_at"].isoformat() if membership.get("joined_at") else None,
                "is_you": uid == user_id
            })
        
        # Sort: admins first, then by name
        members.sort(key=lambda m: (m["role"] != "admin", m.get("full_name", "")))
        
        return members
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to get group members: {str(e)}"}


# ============================================================================
# SERVER STARTUP
# ============================================================================

# Phase 3 Tools - Add these to server.py before setup_database()

# Place this section before "# ADMIN TOOLS" section

# ============================================================================
# PHASE 3: MULTI-USER EXPENSE SPLITTING
# ============================================================================

@mcp.tool()
async def add_group_expense(
    user_id: str,
    group_id: str,
    amount: float,
    description: str,
    category: str,
    date: str,
    split_type: str,
    participants: list,
    user_amounts: dict = None,
    user_percentages: dict = None,
    subcategory: str = "",
    note: str = ""
):
    """
    Add an expense to a group with automatic splitting among participants.
    
    Split types:
    - "equal": Divide equally among all participants
    - "exact": Specific amounts for each (provide user_amounts)
    - "percentage": Percentage-based (provide user_percentages)
    """
    try:
        # Validate inputs
        if not validate_object_id(group_id):
            return {"status": "error", "message": "Invalid group ID format"}
        
        if not await is_user_in_group(user_id, group_id):
            return {"status": "error", "message": "Access denied: You are not a member of this group"}
        
        if amount <= 0:
            return {"status": "error", "message": "Amount must be greater than zero"}
        
        if split_type not in ["equal", "exact", "percentage"]:
            return {"status": "error", "message": "split_type must be 'equal', 'exact', or 'percentage'"}
        
        if not participants or len(participants) == 0:
            return {"status": "error", "message": "At least one participant is required"}
        
        if user_id not in participants:
            return {"status": "error", "message": "Payer must be included in participants"}
        
        # Validate all participants are group members
        for participant_id in participants:
            if not await is_user_in_group(participant_id, group_id):
                return {"status": "error", "message": f"Participant {participant_id} is not a member of this group"}
        
        # Prepare split data
        split_data = {}
        if split_type == "exact":
            if not user_amounts:
                return {"status": "error", "message": "user_amounts required for exact split"}
            split_data["user_amounts"] = user_amounts
        elif split_type == "percentage":
            if not user_percentages:
                return {"status": "error", "message": "user_percentages required for percentage split"}
            split_data["user_percentages"] = user_percentages
        
        # Calculate splits
        try:
            splits = calculate_splits(
                total_amount=amount,
                split_type=split_type,
                participants=participants,
                paid_by=user_id,
                split_data=split_data
            )
        except ValueError as ve:
            return {"status": "error", "message": f"Split calculation failed: {str(ve)}"}
        
        # Create expense document
        expense_doc = {
            "group_id": group_id,
            "paid_by": user_id,
            "user_id": user_id,
            "amount": float(amount),
            "description": description,
            "category": category,
            "subcategory": subcategory or "",
            "note": note or "",
            "date": date,
            "split_type": split_type,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert expense
        expense_result = await expenses_col.insert_one(expense_doc)
        expense_id = str(expense_result.inserted_id)
        
        # Create participant records
        participant_docs = []
        for participant_id, share_amount in splits.items():
            participant_doc = {
                "expense_id": expense_id,
                "user_id": participant_id,
                "share_amount": float(share_amount),
                "created_at": datetime.utcnow()
            }
            
            if split_type == "exact":
                participant_doc["exact_amount"] = float(user_amounts.get(participant_id, 0))
            elif split_type == "percentage":
                participant_doc["share_percentage"] = float(user_percentages.get(participant_id, 0))
            
            participant_docs.append(participant_doc)
        
        # Insert all participants
        await expense_participants_col.insert_many(participant_docs)
        
        # Format response
        expense_doc["id"] = expense_id
        del expense_doc["_id"]
        
        # Create split summary
        split_summary = []
        for participant_id, share_amount in splits.items():
            user = await users_col.find_one({"_id": ObjectId(participant_id)})
            split_summary.append({
                "user_id": participant_id,
                "email": user.get("email", "Unknown") if user else "Unknown",
                "full_name": user.get("full_name", "Unknown") if user else "Unknown",
                "share": float(share_amount),
                "is_payer": participant_id == user_id
            })
        
        return {
            "status": "success",
            "expense_id": expense_id,
            "expense": expense_doc,
            "splits": split_summary,
            "message": f"Expense added and split among {len(participants)} participants"
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to add group expense: {str(e)}"}

@mcp.tool()
async def list_group_expenses(user_id: str, group_id: str, start_date: str = None, end_date: str = None):
    """
    List all expenses in a group with split details.
    """
    try:
        if not validate_object_id(group_id):
            return {"status": "error", "message": "Invalid group ID format"}
        
        if not await is_user_in_group(user_id, group_id):
            return {"status": "error", "message": "Access denied: You are not a member of this group"}
        
        # Build query
        query = {"group_id": group_id}
        if start_date and end_date:
            query["date"] = {"$gte": start_date, "$lte": end_date}
        elif start_date:
            query["date"] = {"$gte": start_date}
        elif end_date:
            query["date"] = {"$lte": end_date}
        
        # Get expenses
        expenses = await expenses_col.find(query).sort("date", -1).to_list(None)
        
        if not expenses:
            return []
        
        # Get expense IDs
        expense_ids = [str(e["_id"]) for e in expenses]
        
        # Get all participants
        participants = await expense_participants_col.find({
            "expense_id": {"$in": expense_ids}
        }).to_list(None)
        
        # Group participants by expense
        participants_by_expense = {}
        for p in participants:
            expense_id = p["expense_id"]
            if expense_id not in participants_by_expense:
                participants_by_expense[expense_id] = []
            participants_by_expense[expense_id].append(p)
        
        # Get all user IDs
        all_user_ids = set()
        for e in expenses:
            all_user_ids.add(e.get("paid_by", e.get("user_id")))
        for p in participants:
            all_user_ids.add(p["user_id"])
        
        # Get user details
        users = await users_col.find({
            "_id": {"$in": [ObjectId(uid) for uid in all_user_ids if validate_object_id(uid)]}
        }).to_list(None)
        user_map = {str(u["_id"]): u for u in users}
        
        # Build response
        result = []
        for expense in expenses:
            expense_id = str(expense["_id"])
            paid_by = expense.get("paid_by", expense.get("user_id"))
            payer = user_map.get(paid_by, {})
            
            # Get participants for this expense
            expense_participants_list = participants_by_expense.get(expense_id, [])
            
            splits = []
            for p in expense_participants_list:
                participant_user = user_map.get(p["user_id"], {})
                splits.append({
                    "user_id": p["user_id"],
                    "email": participant_user.get("email", "Unknown"),
                    "full_name": participant_user.get("full_name", "Unknown"),
                    "share": p.get("share_amount", 0),
                    "is_payer": p["user_id"] == paid_by
                })
            
            expense_data = serialize(expense)
            expense_data["payer"] = {
                "user_id": paid_by,
                "email": payer.get("email", "Unknown"),
                "full_name": payer.get("full_name", "Unknown")
            }
            expense_data["splits"] = splits
            expense_data["participant_count"] = len(splits)
            
            result.append(expense_data)
        
        return result
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to list group expenses: {str(e)}"}

@mcp.tool()
async def get_expense_details(user_id: str, expense_id: str):
    """
    Get detailed information about a specific expense including all splits.
    """
    try:
        if not validate_object_id(expense_id):
            return {"status": "error", "message": "Invalid expense ID format"}
        
        # Get expense
        expense = await expenses_col.find_one({"_id": ObjectId(expense_id)})
        
        if not expense:
            return {"status": "error", "message": "Expense not found"}
        
        # Check access
        group_id = expense.get("group_id")
        if group_id:
            if not await is_user_in_group(user_id, group_id):
                return {"status": "error", "message": "Access denied"}
        else:
            if expense.get("user_id") != user_id and expense.get("paid_by") != user_id:
                return {"status": "error", "message": "Access denied"}
        
        # Get participants
        participants = await expense_participants_col.find({
            "expense_id": expense_id
        }).to_list(None)
        
        # Get user details
        if participants:
            user_ids = [ObjectId(p["user_id"]) for p in participants]
            users = await users_col.find({"_id": {"$in": user_ids}}).to_list(None)
            user_map = {str(u["_id"]): u for u in users}
            
            splits = []
            for p in participants:
                participant_user = user_map.get(p["user_id"], {})
                splits.append({
                    "user_id": p["user_id"],
                    "email": participant_user.get("email", "Unknown"),
                    "full_name": participant_user.get("full_name", "Unknown"),
                    "share": p.get("share_amount", 0),
                    "share_percentage": p.get("share_percentage"),
                    "exact_amount": p.get("exact_amount"),
                    "is_payer": p["user_id"] == expense.get("paid_by", expense.get("user_id"))
                })
        else:
            splits = []
        
        # Get payer details
        paid_by = expense.get("paid_by", expense.get("user_id"))
        payer = await users_col.find_one({"_id": ObjectId(paid_by)})
        
        expense_data = serialize(expense)
        expense_data["payer"] = {
            "user_id": paid_by,
            "email": payer.get("email", "Unknown") if payer else "Unknown",
            "full_name": payer.get("full_name", "Unknown") if payer else "Unknown"
        }
        expense_data["splits"] = splits
        expense_data["participant_count"] = len(splits)
        
        return expense_data
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to get expense details: {str(e)}"}

# ============================================================================
# ADMIN TOOLS
# ============================================================================

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

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
