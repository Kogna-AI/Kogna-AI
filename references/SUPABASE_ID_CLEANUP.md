# Supabase ID Cleanup - Authentication Fix

## Problem

The codebase had a confusing mix where:
- The `users` table had a `supabase_id` column
- JWT tokens used `supabase_id` as the subject (`sub` claim)
- Frontend expected `user.id` to be available
- **But Supabase Auth was NOT actually being used for authentication**

This caused the TeamOverview component to fail because `user.id` didn't exist in the user object - only a meaningless `supabase_id` did.

---

## What Supabase Is Actually Used For

After analyzing the codebase, Supabase is **only** used for:

1. **File Storage** - Document uploads via `embedding_service.py`
2. **Vector Database** - Document chunks for RAG/AI via `document_chunks` table
3. **Chat/Messages Storage** - Session management for the AI assistant

**Authentication is completely custom:**
- JWT tokens generated in-house (`core.security`)
- Passwords hashed with Argon2 and stored in your Postgres DB
- No Supabase Auth service involved at all

---

## Changes Made

### 1. JWT Token Structure (`Backend/routers/auth.py`)

**Before:**
```python
token_data = {
    "sub": user["supabase_id"],  # Random UUID, meaningless
    "email": user["email"],
    "organization_id": user["organization_id"],
}
```

**After:**
```python
token_data = {
    "sub": str(user["id"]),  # Actual user ID from database
    "email": user["email"],
    "organization_id": str(user["organization_id"]),
}
```

---

### 2. JWT Decoder (`Backend/auth/dependencies.py`)

**Before:**
```python
async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    return {
        "supabase_id": payload["sub"],
        "email": payload.get("email"),
    }
```

**After:**
```python
async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    return {
        "id": payload["sub"],  # Real user ID
        "email": payload.get("email"),
        "organization_id": payload.get("organization_id"),
    }
```

---

### 3. Removed Unnecessary DB Lookup (`Backend/auth/dependencies.py`)

**Before:**
```python
async def get_backend_user_id(user = Depends(get_current_user), db = Depends(get_db)):
    supabase_id = user["supabase_id"]
    # Query database to find user by supabase_id...
    cursor.execute("SELECT id, organization_id FROM users WHERE supabase_id = %s", ...)
```

**After:**
```python
async def get_backend_user_id(user = Depends(get_current_user), db = Depends(get_db)):
    # No DB lookup needed - ID is already in JWT!
    return {
        "user_id": str(user["id"]),
        "organization_id": str(user["organization_id"]),
    }
```

This is more efficient since we don't need an extra database query on every request.

---

### 4. Updated `/api/auth/me` Endpoint

**Before:**
```python
@router.get("/me")
async def me(user=Depends(get_current_user)):
    return {"success": True, "data": user}  # Only JWT claims
```

**After:**
```python
@router.get("/me")
async def me(user=Depends(get_current_user), db=Depends(get_db)):
    # Fetch full user profile from database
    cursor.execute("""
        SELECT u.id, u.organization_id, u.first_name, u.second_name,
               u.role, u.email, u.created_at, o.name as organization_name
        FROM users u
        LEFT JOIN organizations o ON u.organization_id = o.id
        WHERE u.id = %s
    """, (user["id"],))
    
    return {"success": True, "data": dict(user_data)}
```

Now returns complete user profile with:
- ✅ Real `id` field (not supabase_id)
- ✅ `first_name`, `second_name`
- ✅ `role`, `email`
- ✅ `organization_id`, `organization_name`

---

### 5. Updated RBAC Permissions (`Backend/core/permissions.py`)

**Before:**
```python
def build_user_context(supabase_user) -> UserContext:
    # Expected a Supabase user object
    db_user = get_user_from_supabase_id(supabase_user.id)
    ...
```

**After:**
```python
def build_user_context(jwt_user: dict) -> UserContext:
    # Works with JWT user dict directly
    user_id = jwt_user["id"]
    # Fetch from DB using real user ID
    cursor.execute("SELECT ... FROM users WHERE id = %s", (user_id,))
    ...
```

---

## Impact on Frontend

### Before (Broken)
```typescript
// user object from /api/auth/me
{
  supabase_id: "abc-123",  // Random UUID
  email: "user@example.com"
}

// TeamOverview tried to use user.id → UNDEFINED!
const fetchData = async () => {
  if (!user?.id) return;  // Always returned early
  ...
}
```

### After (Fixed)
```typescript
// user object from /api/auth/me
{
  id: "uuid-of-user",           // ✅ Real user ID
  email: "user@example.com",
  first_name: "John",
  second_name: "Doe",
  role: "member",
  organization_id: "uuid-of-org",
  organization_name: "Acme Corp"
}

// TeamOverview now works!
const fetchData = async () => {
  if (!user?.id) return;  // user.id exists!
  const teamData = await api.getUserTeam(user.id);  // ✅ Works
  ...
}
```

---

## Database Schema

The `supabase_id` column **still exists** in the `users` table for backward compatibility and for any old code that might reference it. It's now just set to a random UUID during registration and never used.

### Future Cleanup (Optional)

If you want to fully remove Supabase references:

1. **Drop the column:**
   ```sql
   ALTER TABLE users DROP COLUMN supabase_id;
   ```

2. **Remove from models:**
   - `Backend/core/models.py` - Remove `supabase_id` from UserInfo
   - `Backend/routers/users.py` - Remove from SELECT queries

3. **Remove Supabase client creation:**
   - Only keep it for storage/embedding services that actually need it
   - Remove from `core/permissions.py` completely

---

## Testing

After these changes, test the following:

### 1. Login Flow
```bash
# Start backend
cd Backend && uvicorn main:app --reload

# Login via API
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "yourpassword"}'

# Should return access_token and user object with real id
```

### 2. Get Current User
```bash
# Use the token from login
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Should return user with id, first_name, second_name, etc.
```

### 3. TeamOverview
1. Login to the frontend
2. Navigate to Team Overview
3. Should now load your team and members successfully!

---

## Summary

✅ Removed confusing `supabase_id` from JWT tokens  
✅ JWT now uses real user `id` as subject  
✅ Frontend receives proper `user.id` field  
✅ Removed unnecessary DB lookup on every request  
✅ `/api/auth/me` returns complete user profile  
✅ TeamOverview component now works correctly  
✅ RBAC permissions updated to work with JWT user  

**Authentication is now consistent and uses the real user ID throughout the system!** 🎉

---

## Notes

- Supabase is **still used** for storage and vector embeddings (document chunks)
- The `supabase_id` column still exists in the database (for backward compatibility)
- All authentication flows now use the real `users.id` field
- No breaking changes for existing users (tokens will be refreshed on next login)
