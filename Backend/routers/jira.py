# Jira Router - Fetch Jira data for dashboard display
import os
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from supabase_connect import get_supabase_manager
from auth.dependencies import get_backend_user_id
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/jira", tags=["Jira"])
supabase = get_supabase_manager().client

# ============================================================================
# Pydantic Models
# ============================================================================

class JiraIssue(BaseModel):
    key: str
    summary: str
    status: str
    priority: Optional[str] = None
    assignee: Optional[str] = None
    created: str
    updated: str
    project_key: Optional[str] = None
    issue_type: Optional[str] = None

class JiraProject(BaseModel):
    key: str
    name: str
    issues_count: int = 0
    completed_issues: int = 0
    in_progress_issues: int = 0
    todo_issues: int = 0

class JiraKPIs(BaseModel):
    total_issues: int = 0
    completed_issues: int = 0
    in_progress_issues: int = 0
    todo_issues: int = 0
    completion_rate: float = 0.0
    projects_count: int = 0
    avg_completion_time_days: Optional[float] = None
    high_priority_count: int = 0
    blocked_issues: int = 0

class JiraDashboardData(BaseModel):
    kpis: JiraKPIs
    projects: List[JiraProject]
    recent_issues: List[JiraIssue]
    issues_by_status: Dict[str, int]
    issues_by_priority: Dict[str, int]

# ============================================================================
# Helper Functions
# ============================================================================

async def fetch_jira_file_from_storage(user_id: str, file_path: str) -> Optional[Dict]:
    """Fetch Jira data from Supabase storage"""
    try:
        bucket_name = os.getenv("SUPABASE_BUCKET_NAME", "kogna-etl-data")

        # Download file from storage
        response = supabase.storage.from_(bucket_name).download(file_path)

        if response:
            # Parse JSON data
            data = json.loads(response.decode('utf-8'))
            return data

        return None

    except Exception as e:
        logging.error(f"Error fetching Jira file {file_path}: {e}")
        return None

def calculate_completion_rate(completed: int, total: int) -> float:
    """Calculate completion percentage"""
    if total == 0:
        return 0.0
    return round((completed / total) * 100, 2)

def parse_jira_issues(issues_data: List[Dict]) -> tuple[List[JiraIssue], Dict[str, int], Dict[str, int]]:
    """Parse Jira issues and extract status/priority counts"""
    issues = []
    status_counts = {}
    priority_counts = {}

    for issue in issues_data[:20]:  # Get recent 20 issues
        try:
            fields = issue.get('fields', {})

            # Extract issue data
            jira_issue = JiraIssue(
                key=issue.get('key', 'N/A'),
                summary=fields.get('summary', 'No summary'),
                status=fields.get('status', {}).get('name', 'Unknown'),
                priority=fields.get('priority', {}).get('name'),
                assignee=fields.get('assignee', {}).get('displayName') if fields.get('assignee') else 'Unassigned',
                created=fields.get('created', ''),
                updated=fields.get('updated', ''),
                project_key=fields.get('project', {}).get('key'),
                issue_type=fields.get('issuetype', {}).get('name')
            )
            issues.append(jira_issue)

            # Count by status
            status = jira_issue.status
            status_counts[status] = status_counts.get(status, 0) + 1

            # Count by priority
            if jira_issue.priority:
                priority_counts[jira_issue.priority] = priority_counts.get(jira_issue.priority, 0) + 1

        except Exception as e:
            logging.error(f"Error parsing issue: {e}")
            continue

    return issues, status_counts, priority_counts

# ============================================================================
# Endpoints
# ============================================================================

@router.get("/dashboard", response_model=JiraDashboardData)
async def get_jira_dashboard(ids: dict = Depends(get_backend_user_id)):
    """
    Get comprehensive Jira dashboard data including KPIs, projects, and issues
    """
    user_id = ids.get('user_id')

    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    try:
        # Fetch KPIs
        kpis_path = f"{user_id}/jira/kpis_latest.json"
        kpis_data = await fetch_jira_file_from_storage(user_id, kpis_path)

        # Fetch all issues
        issues_path = f"{user_id}/jira/all_issues_latest.json"
        issues_data = await fetch_jira_file_from_storage(user_id, issues_path)

        # If no data found, return empty dashboard
        if not kpis_data and not issues_data:
            return JiraDashboardData(
                kpis=JiraKPIs(),
                projects=[],
                recent_issues=[],
                issues_by_status={},
                issues_by_priority={}
            )

        # Parse KPIs
        kpis = JiraKPIs()
        if kpis_data:
            overview = kpis_data.get('overview', {})
            status_counts = overview.get('status_counts', {})
            priority_counts = overview.get('priority_counts', {})

            kpis = JiraKPIs(
                total_issues=overview.get('total_issues', 0),
                completed_issues=status_counts.get('done', 0),
                in_progress_issues=status_counts.get('in_progress', 0),
                todo_issues=status_counts.get('to_do', 0),
                completion_rate=overview.get('completion_rate', 0.0),
                projects_count=len(kpis_data.get('projects', [])),
                high_priority_count=priority_counts.get('high', 0) + priority_counts.get('highest', 0),
                blocked_issues=overview.get('blocked_issues', 0)
            )

        # Parse projects
        projects = []
        if kpis_data:
            for project_kpi in kpis_data.get('projects', []):
                status_overview = project_kpi.get('status_overview', {})
                status_cnt = status_overview.get('counts', {})

                projects.append(JiraProject(
                    key=project_kpi.get('project_key', ''),
                    name=project_kpi.get('project_name', ''),
                    issues_count=project_kpi.get('total_work_items', 0),
                    completed_issues=status_cnt.get('done', 0),
                    in_progress_issues=status_cnt.get('in_progress', 0),
                    todo_issues=status_cnt.get('to_do', 0)
                ))

        # Parse issues
        recent_issues = []
        issues_by_status = {}
        issues_by_priority = {}

        if issues_data:
            recent_issues, issues_by_status, issues_by_priority = parse_jira_issues(issues_data)

        return JiraDashboardData(
            kpis=kpis,
            projects=projects,
            recent_issues=recent_issues,
            issues_by_status=issues_by_status,
            issues_by_priority=issues_by_priority
        )

    except Exception as e:
        logging.error(f"Error fetching Jira dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch Jira dashboard: {str(e)}")

@router.get("/issues")
async def get_jira_issues(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    ids: dict = Depends(get_backend_user_id)
):
    """
    Get Jira issues with pagination and filtering
    """
    user_id = ids.get('user_id')

    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    try:
        issues_path = f"{user_id}/jira/all_issues_latest.json"
        issues_data = await fetch_jira_file_from_storage(user_id, issues_path)

        if not issues_data:
            return {"success": True, "data": [], "total": 0}

        # Filter by status if provided
        filtered_issues = issues_data
        if status:
            filtered_issues = [
                issue for issue in issues_data
                if issue.get('fields', {}).get('status', {}).get('name') == status
            ]

        # Pagination
        total = len(filtered_issues)
        paginated_issues = filtered_issues[offset:offset + limit]

        # Parse issues
        issues, _, _ = parse_jira_issues(paginated_issues)

        return {
            "success": True,
            "data": issues,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logging.error(f"Error fetching Jira issues: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch Jira issues: {str(e)}")

@router.get("/projects")
async def get_jira_projects(ids: dict = Depends(get_backend_user_id)):
    """
    Get all Jira projects with KPIs
    """
    user_id = ids.get('user_id')

    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    try:
        kpis_path = f"{user_id}/jira/kpis_latest.json"
        kpis_data = await fetch_jira_file_from_storage(user_id, kpis_path)

        if not kpis_data:
            return {"success": True, "data": []}

        projects = []
        for project_key, project_kpis in kpis_data.get('projects', {}).items():
            projects.append({
                "key": project_key,
                "name": project_kpis.get('project_name', project_key),
                "issues_count": project_kpis.get('total_issues', 0),
                "completed_issues": project_kpis.get('completed_issues', 0),
                "in_progress_issues": project_kpis.get('in_progress_issues', 0),
                "todo_issues": project_kpis.get('todo_issues', 0),
                "completion_rate": project_kpis.get('completion_rate', 0.0)
            })

        return {"success": True, "data": projects}

    except Exception as e:
        logging.error(f"Error fetching Jira projects: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch Jira projects: {str(e)}")

@router.get("/sync-status")
async def get_jira_sync_status(ids: dict = Depends(get_backend_user_id)):
    """
    Get the last Jira sync status
    """
    user_id = ids.get('user_id')

    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    try:
        # Check if Jira data exists
        kpis_path = f"{user_id}/jira/kpis_latest.json"
        kpis_data = await fetch_jira_file_from_storage(user_id, kpis_path)

        return {
            "success": True,
            "has_data": kpis_data is not None,
            "last_sync": None  # You can add sync timestamp if stored
        }

    except Exception as e:
        logging.error(f"Error checking Jira sync status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check sync status: {str(e)}")
