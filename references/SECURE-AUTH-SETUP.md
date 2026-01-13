# Secure Authentication System - Setup Guide

## Overview

Your authentication system has been upgraded with enterprise-grade security:

- **httpOnly cookies** for refresh tokens (XSS-proof)
- **In-memory access tokens** (no localStorage vulnerability)
- **Automatic token refresh** (seamless UX)
- **Token revocation** (logout security)
- **Server-side password validation**
- **Timing attack mitigation** (login security)
- **Token type enforcement** (prevents token confusion attacks)

## Setup Instructions

### Step 1: Run Database Migration

Execute the SQL migration to create the `refresh_tokens` table:

```bash
# If using Supabase:
psql $DATABASE_URL < Backend/migrations/001_create_refresh_tokens_table.sql

# Or through Supabase dashboard:
# 1. Go to SQL Editor
# 2. Paste contents of Backend/migrations/001_create_refresh_tokens_table.sql
# 3. Run the query
```

### Step 2: Update Environment Variables

**Backend** (`Backend/.env`):

```env
# IMPORTANT: Keep your existing SECRET_KEY
SECRET_KEY=your-existing-secret-key

# Database
DATABASE_URL=your-database-url

# Optional: Adjust token expiration (defaults are secure)
# ACCESS_TOKEN_EXPIRE_MINUTES=15  # Already set in code
# REFRESH_TOKEN_EXPIRE_DAYS=30    # Already set in code
```

**Frontend** (`frontend/.env.local`):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000

# For production:
# NEXT_PUBLIC_API_URL=https://your-api-domain.com
```

### Step 3: Local Development Setup

**Important: Disable `secure` cookie flag for local HTTP testing**

Edit `Backend/routers/auth.py` line 233:

```python
# FOR LOCAL DEVELOPMENT ONLY:
secure=False,  # Change to False if testing on http://localhost

# FOR PRODUCTION (HTTPS):
secure=True,   # Keep this True in production
```

### Step 4: Test the System

**Start backend:**

```bash
cd Backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Start frontend:**

```bash
cd frontend
npm run dev
```

**Test flow:**

1. Register a new account (password validation enforced)
2. Login (refresh token set as httpOnly cookie)
3. Navigate around (access token used from memory)
4. Wait 15 minutes (access token auto-refreshes)
5. Logout (refresh token revoked in DB)

## Security Features Explained

### 1. Token Architecture

```
Login Flow:
┌─────────┐                  ┌─────────┐                 ┌──────────┐
│ Browser │                  │ Backend │                 │ Database │
└────┬────┘                  └────┬────┘                 └────┬─────┘
     │                            │                           │
     │ POST /auth/login           │                           │
     │ {email, password}          │                           │
     ├───────────────────────────>│                           │
     │                            │                           │
     │                            │ Verify password           │
     │                            │ (Argon2 + timing safety)  │
     │                            │                           │
     │                            │ Store refresh token hash  │
     │                            ├──────────────────────────>│
     │                            │                           │
     │<───────────────────────────┤                           │
     │ Set-Cookie: refresh_token  │                           │
     │ (httpOnly, secure, 30d)    │                           │
     │                            │                           │
     │ {access_token: "..."}      │                           │
     │ (15 min, stored in memory) │                           │
```

### 2. Automatic Token Refresh

```
API Request with Expired Token:
┌─────────┐                  ┌─────────┐
│ Browser │                  │ Backend │
└────┬────┘                  └────┬────┘
     │ GET /api/metrics           │
     │ Authorization: Bearer ...  │
     ├───────────────────────────>│
     │                            │ Token expired!
     │<───────────────────────────┤
     │ 401 Token expired          │
     │                            │
     │ POST /auth/refresh         │
     │ (Cookie: refresh_token)    │
     ├───────────────────────────>│
     │                            │ Validate refresh token
     │<───────────────────────────┤
     │ {access_token: "new..."}   │
     │                            │
     │ GET /api/metrics [RETRY]   │
     │ Authorization: Bearer new  │
     ├───────────────────────────>│
     │<───────────────────────────┤
     │ 200 OK                     │
```

### 3. Why This Is Secure

| Attack Vector        | Old System                                                | New System                                                                                       |
| -------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| **XSS token theft**  | Token in localStorage, easily stolen                      | Access token in memory (lost on page close), refresh token in httpOnly cookie (JS cannot access) |
| **Token replay**     | Long-lived token, reusable if stolen                      | Short-lived access token (15 min), refresh token can be revoked                                  |
| **User enumeration** | Different errors for "user not found" vs "wrong password" | Same error message + dummy hash to equalize timing                                               |
| **Weak passwords**   | No server-side validation                                 | Server enforces 8+ chars with letters + digits                                                   |
| **Token confusion**  | Any JWT signed with same key accepted                     | Token type claim enforced (access vs refresh)                                                    |
| **CSRF**             | Depends on implementation                                 | Auth via Bearer token (header), not cookie-based auth                                            |

## Production Deployment

### Required Changes for Production

1. **Enable secure cookies** (`Backend/routers/auth.py`):

   ```python
   secure=True,  # Line 233 - MUST be True in production
   ```

2. **HTTPS only**: Deploy backend behind HTTPS (AWS ALB, Cloudflare, etc.)

3. **CORS configuration** (`Backend/.env`):

   ```env
   ALLOWED_ORIGINS=https://your-frontend-domain.com
   ```

4. **Cookie domain** (if frontend/backend on different domains):
   ```python
   response.set_cookie(
       key=REFRESH_TOKEN_COOKIE_NAME,
       value=refresh_token,
       domain=".yourdomain.com",  # Add this for subdomain sharing
       ...
   )
   ```

### AWS/ECS Deployment Considerations

- **Health check**: Existing `/health` endpoint still works
- **Cookie path**: Refresh tokens only sent to `/api/auth/*` (reduces exposure)
- **Load balancer**: Ensure sticky sessions if using multiple backend instances
- **Database**: Cleanup old refresh tokens periodically:
  ```sql
  DELETE FROM refresh_tokens
  WHERE expires_at < NOW() OR revoked_at IS NOT NULL;
  ```

## Testing Checklist

- [ ] User can register with strong password
- [ ] User cannot register with weak password (< 8 chars or no digits)
- [ ] User can login and see dashboard
- [ ] Refresh happens automatically after 15 minutes
- [ ] User can logout (refresh token revoked)
- [ ] After logout, user cannot access protected routes
- [ ] After logout, refresh token cannot be reused
- [ ] Token works across multiple tabs (same session)
- [ ] On page refresh, user stays logged in (via refresh cookie)

## Monitoring & Security

### Recommended Monitoring

1. **Failed login attempts** (add to your backend logs):

   ```python
   logger.warning(f"Failed login attempt for email: {email}")
   ```

2. **Refresh token usage**:

   ```sql
   SELECT user_agent, ip_address, created_at
   FROM refresh_tokens
   WHERE user_id = $1
   ORDER BY created_at DESC;
   ```

3. **Revoke all sessions for a user** (security incident):
   ```sql
   UPDATE refresh_tokens
   SET revoked_at = NOW()
   WHERE user_id = $1;
   ```

### Security Maintenance

**Monthly**: Clean up expired tokens:

```sql
DELETE FROM refresh_tokens
WHERE expires_at < NOW() - INTERVAL '7 days';
```

**On password change**: Revoke all sessions:

```python
cursor.execute(
    "UPDATE refresh_tokens SET revoked_at = NOW() WHERE user_id = %s",
    (user_id,)
)
```

## Troubleshooting

### Issue: "No refresh token provided" on API calls

**Cause**: Cookies not being sent (likely CORS or `secure` flag mismatch)

**Fix**:

- Ensure `credentials: "include"` in all frontend fetch calls (already done)
- Check `secure=False` for local HTTP testing
- Verify CORS allows credentials

### Issue: Session lost on page refresh

**Cause**: Refresh token not persisting or refresh endpoint failing

**Fix**:

- Check browser DevTools → Application → Cookies for `refresh_token`
- Verify `httponly` flag is set
- Check backend logs for `/api/auth/refresh` errors

### Issue: Token refresh loop (infinite 401s)

**Cause**: Refresh token expired or revoked

**Fix**:

- User must log in again
- Check `refresh_tokens` table for `revoked_at` or `expires_at`

## Migration Notes

### What Changed

- **No localStorage usage** (tokens never persisted client-side)
- **New DB table** (`refresh_tokens` - must run migration)
- **New endpoints**: `/api/auth/refresh`, `/api/auth/logout`
- **Breaking change**: `access_token` now expires in 15 min (was 60 min)
- **Existing passwords**: Still work! No rehashing needed

### Backward Compatibility

**Existing users**: Can log in immediately with existing passwords (Argon2 hashes unchanged)

**Old tokens**: Will expire after 15-60 minutes (depending on when issued). Users will auto-refresh or need to log in again.

## Next Steps (Optional Enhancements)

1. **Refresh token rotation**: Issue new refresh token on each refresh (extra security)
2. **Multi-device management**: Show user all active sessions in UI
3. **Rate limiting**: Limit login/refresh attempts per IP
4. **2FA**: Add TOTP second factor for high-security accounts
5. **Password reset flow**: Secure email-based reset with time-limited tokens

---

## Need Help?

- Check `Backend/routers/auth.py` for all auth endpoints
- Review `frontend/src/services/api.ts` for token handling
- See `Backend/migrations/001_create_refresh_tokens_table.sql` for schema

**Your auth system is now production-ready and secure! **
