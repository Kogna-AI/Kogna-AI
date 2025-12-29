# Deployment Checklist

Follow these steps in order to deploy your secure authentication system.

## Pre-Deployment (Do This Now)

### Step 1: Run Database Migration

**Copy and run this SQL in your database:**

```bash
# Option A: Via psql command line
psql $DATABASE_URL < Backend/migrations/001_create_refresh_tokens_table.sql

# Option B: Via Supabase Dashboard
# 1. Go to https://supabase.com → Your Project → SQL Editor
# 2. Copy contents of Backend/migrations/001_create_refresh_tokens_table.sql
# 3. Paste and run
```

**Verify it worked:**

```sql
SELECT * FROM refresh_tokens LIMIT 1;
-- Should return empty result (no error)
```

### Step 2: Configure Local Development

**Edit `Backend/routers/auth.py` line 233:**

```python
# Change this line for local testing:
secure=False,  # <-- Change True to False
```

This allows cookies to work on `http://localhost` during development.

### Step 3: Test Locally

**Terminal 1 - Start Backend:**

```bash
cd Backend
source venv/bin/activate  # or: venv\Scripts\activate on Windows
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Start Frontend:**

```bash
cd frontend
npm run dev
```

**Browser - Test Flow:**

1. Go to `http://localhost:3000`
2. Click "Sign up" and create account with password like `Test1234`
3. Try weak password like `weak` → Should be rejected
4. Login with your new account
5. Open DevTools → Application → Cookies
6. Verify you see `refresh_token` cookie with `HttpOnly` flag
7. Navigate around the app
8. Logout and verify cookie is gone

## Production Deployment

### Step 1: Update Code for Production

**Edit `Backend/routers/auth.py` line 233:**

```python
# Change back to True for production:
secure=True,  # <-- REQUIRED for HTTPS
```

### Step 2: Verify Environment Variables

**Backend (`Backend/.env`):**

```env
SECRET_KEY=<your-existing-secret-key-dont-change>
DATABASE_URL=<your-database-url>
ALLOWED_ORIGINS=https://your-frontend-domain.com
```

**Frontend (`frontend/.env` or in Vercel/AWS):**

```env
NEXT_PUBLIC_API_URL=https://your-api-domain.com
```

### Step 3: Deploy Backend

**If using AWS ECS (existing setup):**

```bash
# Your existing CI/CD should work
git add .
git commit -m "Secure auth implementation"
git push origin main
```

**Verify deployment:**

```bash
curl https://your-api-domain.com/health
# Should return 200 OK
```

### Step 4: Deploy Frontend

**If using Vercel/Next.js:**

```bash
cd frontend
npm run build  # Test build locally first
# Then push to trigger deployment
git push origin main
```

### Step 5: Production Smoke Test

1. Visit your production frontend
2. Register a new account
3. Login
4. Check cookies (should see `refresh_token` with `Secure` flag)
5. Refresh page → Should stay logged in
6. Logout → Should clear session

## Verification Checklist

After deployment, verify these:

- [ ] **Health check works**: `curl https://api.example.com/health`
- [ ] **Register works**: Strong password accepted, weak rejected
- [ ] **Login works**: Returns access token + sets refresh cookie
- [ ] **Refresh works**: After 15 min, token auto-refreshes
- [ ] **Logout works**: Cookie cleared, cannot reuse refresh token
- [ ] **HTTPS enforced**: Cookies have `Secure` flag in production
- [ ] **CORS configured**: Frontend can call backend
- [ ] **Database migrated**: `refresh_tokens` table exists

## Rollback Plan (If Needed)

If something goes wrong:

### Quick Rollback (5 minutes)

1. **Revert backend code:**

   ```bash
   git revert HEAD
   git push origin main
   ```

2. **Users can still login** with existing passwords (Argon2 unchanged)

3. **Old tokens** will continue to work until they expire

### Database Rollback (Optional)

If you need to remove the refresh_tokens table:

```sql
DROP TABLE IF EXISTS refresh_tokens;
```

**Note**: This is safe because the old auth system didn't use it.

## Post-Deployment Monitoring

### Week 1: Watch These Metrics

1. **Failed logins**: Should see rejections for weak passwords

   ```sql
   -- Add this query to your monitoring
   SELECT COUNT(*) FROM refresh_tokens
   WHERE created_at > NOW() - INTERVAL '1 day';
   ```

2. **Token refresh rate**: Should see `/api/auth/refresh` calls every ~15 min per active user

3. **Error logs**: Watch for 401 errors (should be rare after refresh implementation)

### Monthly Maintenance

**Clean up expired tokens:**

```sql
DELETE FROM refresh_tokens
WHERE expires_at < NOW() - INTERVAL '7 days';
```

**Optional: Set up cron job:**

```python
# Add to your backend scheduled tasks
@scheduler.scheduled_job('cron', day='1')
def cleanup_tokens():
    cursor.execute(
        "DELETE FROM refresh_tokens WHERE expires_at < NOW() - INTERVAL '7 days'"
    )
```

## Troubleshooting

### Issue: Cookies not working locally

**Symptom**: "No refresh token provided" error

**Fix**:

- Verify `secure=False` in `Backend/routers/auth.py` line 233
- Check browser DevTools → Application → Cookies
- Try clearing all cookies and logging in again

### Issue: CORS errors in production

**Symptom**: Network errors, CORS policy blocks

**Fix**:

```env
# Backend/.env - Add your frontend domain
ALLOWED_ORIGINS=https://your-frontend.com,https://www.your-frontend.com
```

### Issue: "Session expired" immediately after login

**Symptom**: User logs in but gets logged out on next request

**Fix**:

- Check `credentials: "include"` in all fetch calls (already done in api.ts)
- Verify CORS `allow_credentials=True` (already set in config.py)
- Ensure frontend and backend are both HTTPS in production

## What Changed (For Your Team)

**User-facing:**

- No visible changes! Auth works the same
- Sessions last longer (30 days vs needing to log in every hour)
- Logout is more secure (can't reuse old sessions)

**Developer-facing:**

- Access tokens expire in 15 min (was 60 min)
- Automatic refresh happens transparently
- No more localStorage for tokens
- New endpoints: `/api/auth/refresh`, `/api/auth/logout`

**Infrastructure:**

- New database table: `refresh_tokens`
- Cookies must be enabled (already required for most apps)
- Backend must be HTTPS in production (should already be the case)

## Success Criteria

You've successfully deployed when:

1. New users can register with strong passwords
2. Weak passwords are rejected server-side
3. Users can login and stay logged in across page refreshes
4. Users can logout and session is fully terminated
5. No tokens in localStorage (check DevTools)
6. `refresh_token` cookie exists with `HttpOnly` flag

---

## You're Done!

Your authentication system is now:

- Protected against XSS token theft
- Immune to CSRF attacks
- Hardened against timing attacks
- Enforcing strong passwords
- Supporting proper session revocation

**Next Steps**: Monitor for 1 week, then consider optional enhancements in `SECURE-AUTH-SETUP.md`.
