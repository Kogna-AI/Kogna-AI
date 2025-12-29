# TeamOverview Backend Connection - Setup Complete

## What We Did

Successfully connected the frontend `TeamOverview` component to the backend API so you can see real team data from your database.

---

## Changes Made

### 1. Backend API Endpoints (`Backend/routers/teams.py`)

Added two new endpoints:

#### Get User's Team
```
GET /api/teams/user/{user_id}
```
Returns the first team a user belongs to.

#### List Organization Teams  
```
GET /api/teams/organization/{org_id}
```
Returns all teams in an organization with member count and average performance.

---

### 2. Frontend API Client (`frontend/src/services/api.ts`)

Added two new methods:

```typescript
api.getUserTeam(userId: string)
api.listOrganizationTeams(orgId: string)
```

---

### 3. Frontend TeamOverview Component (`frontend/src/app/components/dashboard/TeamOverview.tsx`)

Updated to:
- ✅ Fetch real team data from the backend using `api.getUserTeam(user.id)`
- ✅ Fetch real team members from the backend using `api.listTeamMembers(teamId)`
- ✅ Display team name in the header
- ✅ Show loading states while fetching data
- ✅ Gracefully fall back to mock data if the API fails (with a warning message)
- ✅ Support both backend field names (`first_name`, `second_name`, `user_role`) and mock data field names (`name`, `role`)
- ✅ Calculate metrics from real data (performance, capacity, project count)

---

### 4. Auto-Create Team on Signup (`Backend/routers/auth.py`)

**NEW:** When a user registers:
1. Creates the organization (if it doesn't exist)
2. Creates the user
3. **If this is the first user in the organization:**
   - Automatically creates a default team named `"{Organization Name} Team"`
   - Adds the user as a member with default values:
     - Performance: 85%
     - Capacity: 80%
     - Status: available
     - Project count: 0

---

## How to Test

### Option 1: Create a New Account
1. Start the backend: `cd Backend && uvicorn main:app --reload`
2. Start the frontend: `cd frontend && npm run dev`
3. Go to `/signup` and create a new account
4. Login with the new account
5. Navigate to the Team Overview page
6. **You should see your team with yourself as a member!**

### Option 2: Add Existing User to a Team

If you already have a user account, you can manually add them to a team using the API:

```bash
# 1. Create a team
curl -X POST http://localhost:8000/api/teams \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "organization_id": "YOUR_ORG_ID",
    "name": "Engineering Team"
  }'

# 2. Add user to the team
curl -X POST http://localhost:8000/api/teams/members \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "team_id": "TEAM_ID_FROM_STEP_1",
    "user_id": "YOUR_USER_ID",
    "role": "Developer",
    "performance": 90,
    "capacity": 85
  }'
```

---

## Data Flow

```
TeamOverview.tsx
    ↓
api.getUserTeam(user.id)
    ↓
GET /api/teams/user/{user_id}
    ↓
Database: teams + team_members tables
    ↓
Returns team data
    ↓
api.listTeamMembers(teamId)
    ↓
GET /api/teams/{team_id}/members
    ↓
Database: team_members + users tables (JOIN)
    ↓
Returns members with user info
    ↓
Display in TeamOverview
```

---

## Database Schema Reference

The TeamOverview now uses these tables:

### `teams`
- `id` (UUID)
- `name` (varchar)
- `organization_id` (UUID)
- `created_at` (timestamp)

### `team_members`
- `id` (UUID)
- `team_id` (UUID) → teams.id
- `user_id` (UUID) → users.id
- `role` (varchar)
- `performance` (numeric 0-100)
- `capacity` (numeric 0-100)
- `project_count` (integer)
- `status` (varchar: 'available', 'busy', 'unavailable')

### `users`
- `id` (UUID)
- `first_name` (varchar)
- `second_name` (varchar)
- `email` (varchar)
- `role` (varchar)
- `organization_id` (UUID)

---

## Fallback Behavior

If the backend API fails or the user is not a member of any team:
- Shows a yellow warning message: "Using sample data: [error message]"
- Displays mock team members so the UI isn't empty
- All calculations still work correctly

This ensures the app never breaks even if there are database or network issues.

---

## Next Steps (Optional)

If you want to add more features:

1. **Add more team members:** Use the `POST /api/teams/members` endpoint
2. **Update member performance:** Create a PUT endpoint in `teams.py`
3. **Create multiple teams:** Users can belong to multiple teams - modify `getUserTeam` to return all teams
4. **Team analytics:** Add more aggregations in the backend queries
5. **RBAC integration:** Add permission checks to team endpoints (follow the pattern in the WARP.md guide)

---

## Troubleshooting

### "User is not a member of any team"
- Make sure you either:
  - Created a new account (team auto-created), OR
  - Manually added the user to a team via the API

### "Failed to load team data"
- Check backend is running: `http://localhost:8000/api/docs`
- Check user is authenticated (has valid JWT token)
- Check database connection in backend logs

### Frontend shows mock data
- This is expected if there's no real data yet
- Create a team and add members using the API or by signing up a new user

---

## Summary

✅ Backend endpoints created  
✅ Frontend API methods added  
✅ TeamOverview connected to real data  
✅ Auto-team creation on signup  
✅ Graceful error handling and fallback  

**Your TeamOverview is now fully connected to the backend!** 🎉
