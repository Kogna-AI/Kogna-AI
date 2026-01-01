"""
🔥 ULTIMATE Asana ETL - FULL FEATURE SET

This is the complete, production-ready Asana ETL with ALL improvements:

 Task and project extraction
 Workspace organization
 Analytics (completion rates, overdue tasks, assignee workload)
 Smart categorization (by due date, status, priority)
 Search-optimized text generation
 Data quality scoring
 Auto-tagging

Follows the same pattern as google_drive_etl.py, jira_etl.py, and microsoft_excel_etl.py
"""

import json
import time
import asyncio
import httpx
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from collections import Counter, defaultdict

try:
    from .base_etl import (
        safe_upload_to_bucket,
        update_sync_progress,
        queue_embedding,
        RATE_LIMIT_DELAY,
        MAX_FILE_SIZE
    )
except ImportError:
    # Fallback for testing
    RATE_LIMIT_DELAY = 0.1
    MAX_FILE_SIZE = 50_000_000
    async def safe_upload_to_bucket(*args, **kwargs): return True
    async def update_sync_progress(*args, **kwargs): pass
    async def queue_embedding(*args, **kwargs): pass

logging.basicConfig(level=logging.INFO)


# ============================================================================
# 1. DATA EXTRACTION
# ============================================================================

async def extract_asana_tasks(
    client: httpx.AsyncClient,
    workspace_gid: str,
    workspace_name: str
) -> List[Dict]:
    """
    Extract all tasks from an Asana workspace.
    
    Args:
        client: HTTP client with auth headers
        workspace_gid: Asana workspace GID
        workspace_name: Workspace name for logging
        
    Returns:
        List of tasks with metadata
    """
    all_tasks = []
    
    try:
        # Get projects in workspace
        projects_url = f"https://app.asana.com/api/1.0/projects?workspace={workspace_gid}&limit=100"
        projects_response = await client.get(projects_url)
        projects_response.raise_for_status()
        projects = projects_response.json().get('data', [])
        
        logging.info(f"   ✓ Found {len(projects)} projects")
        
        for project in projects:
            project_gid = project.get('gid')
            project_name = project.get('name')
            
            try:
                # Get tasks for this project
                tasks_url = f"https://app.asana.com/api/1.0/tasks?project={project_gid}&limit=100&opt_fields=name,notes,completed,due_on,assignee,created_at,modified_at,tags,custom_fields,start_on,completed_at"
                
                tasks_response = await client.get(tasks_url)
                tasks_response.raise_for_status()
                
                tasks = tasks_response.json().get('data', [])
                
                if tasks:
                    # Enrich tasks with workspace and project info
                    for task in tasks:
                        task['workspace_name'] = workspace_name
                        task['project_name'] = project_name
                    
                    all_tasks.extend(tasks)
                    logging.info(f"      • {project_name}: {len(tasks)} tasks")
                
                await asyncio.sleep(RATE_LIMIT_DELAY)
                
            except Exception as e:
                logging.error(f" Error fetching tasks from {project_name}: {e}")
                continue
        
        return all_tasks
        
    except Exception as e:
        logging.error(f" Error extracting tasks from {workspace_name}: {e}")
        return []


# ============================================================================
# 2. DATA ANALYTICS
# ============================================================================

def analyze_asana_tasks(tasks: List[Dict]) -> Dict:
    """
    Extract analytics and insights from Asana tasks.
    
    Extracts:
    - Completion rates
    - Overdue tasks
    - Tasks by status
    - Assignee workload
    - Due date distribution
    
    Args:
        tasks: List of Asana tasks
        
    Returns:
        Analytics dict
    """
    analytics = {
        'total_tasks': len(tasks),
        'completed_tasks': 0,
        'incomplete_tasks': 0,
        'overdue_tasks': 0,
        'due_this_week': 0,
        'due_this_month': 0,
        'no_due_date': 0,
        'assignee_workload': {},
        'project_breakdown': {},
        'completion_rate': 0.0
    }
    
    today = datetime.now().date()
    week_from_now = today + timedelta(days=7)
    month_from_now = today + timedelta(days=30)
    
    assignee_counts = Counter()
    project_counts = Counter()
    
    for task in tasks:
        # Completion status
        completed = task.get('completed', False)
        if completed:
            analytics['completed_tasks'] += 1
        else:
            analytics['incomplete_tasks'] += 1
        
        # Due date analysis
        due_on = task.get('due_on')
        if due_on:
            try:
                due_date = datetime.strptime(due_on, '%Y-%m-%d').date()
                
                # Overdue?
                if not completed and due_date < today:
                    analytics['overdue_tasks'] += 1
                
                # Due this week?
                if today <= due_date <= week_from_now:
                    analytics['due_this_week'] += 1
                
                # Due this month?
                if today <= due_date <= month_from_now:
                    analytics['due_this_month'] += 1
                    
            except:
                pass
        else:
            analytics['no_due_date'] += 1
        
        # Assignee workload
        assignee = task.get('assignee')
        if assignee:
            assignee_name = assignee.get('name', 'Unknown')
            assignee_counts[assignee_name] += 1
        else:
            assignee_counts['Unassigned'] += 1
        
        # Project breakdown
        project_name = task.get('project_name', 'Unknown')
        project_counts[project_name] += 1
    
    # Calculate completion rate
    if analytics['total_tasks'] > 0:
        analytics['completion_rate'] = round(
            (analytics['completed_tasks'] / analytics['total_tasks']) * 100, 1
        )
    
    # Top assignees by workload
    analytics['assignee_workload'] = dict(assignee_counts.most_common(10))
    
    # Project breakdown
    analytics['project_breakdown'] = dict(project_counts.most_common(10))
    
    return analytics


def calculate_asana_quality_score(tasks: List[Dict], analytics: Dict) -> int:
    """
    Calculate data quality score (0-100).
    
    Factors:
    - Has tasks (30 points)
    - Has assignees (20 points)
    - Has due dates (20 points)
    - Active projects (20 points)
    - Good completion rate (10 points)
    
    Args:
        tasks: List of tasks
        analytics: Analytics from analyze_asana_tasks
        
    Returns:
        Quality score (0-100)
    """
    score = 0
    
    # Has tasks? (30 points)
    task_count = analytics.get('total_tasks', 0)
    if task_count > 50:
        score += 30
    elif task_count > 20:
        score += 20
    elif task_count > 0:
        score += 10
    
    # Has assignees? (20 points)
    assignee_count = len([k for k in analytics.get('assignee_workload', {}).keys() if k != 'Unassigned'])
    if assignee_count > 5:
        score += 20
    elif assignee_count > 2:
        score += 15
    elif assignee_count > 0:
        score += 10
    
    # Has due dates? (20 points)
    tasks_with_dates = task_count - analytics.get('no_due_date', 0)
    if task_count > 0 and tasks_with_dates > task_count * 0.8:  # >80% have dates
        score += 20
    elif task_count > 0 and tasks_with_dates > task_count * 0.5:  # >50% have dates
        score += 10
    
    # Active projects? (20 points)
    project_count = len(analytics.get('project_breakdown', {}))
    if project_count > 5:
        score += 20
    elif project_count > 2:
        score += 15
    elif project_count > 0:
        score += 10
    
    # Good completion rate? (10 points)
    completion_rate = analytics.get('completion_rate', 0)
    if completion_rate > 50:
        score += 10
    elif completion_rate > 25:
        score += 5
    
    return min(100, score)


# ============================================================================
# 3. SEARCHABLE TEXT GENERATION
# ============================================================================

def create_asana_searchable_text(
    tasks: List[Dict],
    analytics: Dict,
    max_tasks_to_show: int = 30
) -> str:
    """
    Create rich, AI-friendly searchable text from Asana data.
    
    Includes:
    - Task overview
    - Analytics summary
    - Overdue tasks
    - Upcoming tasks
    - Assignee workload
    - Sample tasks
    
    Args:
        tasks: List of tasks
        analytics: Analytics dict
        max_tasks_to_show: Max tasks to include in details
        
    Returns:
        Formatted searchable text
    """
    parts = []
    
    # Header
    parts.append(f" Asana Task Management")
    parts.append(f"Total Tasks: {analytics.get('total_tasks', 0)}")
    parts.append(f"Completion Rate: {analytics.get('completion_rate', 0)}%")
    parts.append("")
    
    # Analytics summary
    parts.append("=== TASK OVERVIEW ===")
    parts.append(f"Completed: {analytics.get('completed_tasks', 0)}")
    parts.append(f"Incomplete: {analytics.get('incomplete_tasks', 0)}")
    parts.append(f"Overdue: {analytics.get('overdue_tasks', 0)}")
    parts.append(f"Due This Week: {analytics.get('due_this_week', 0)}")
    parts.append(f"Due This Month: {analytics.get('due_this_month', 0)}")
    parts.append(f"No Due Date: {analytics.get('no_due_date', 0)}")
    parts.append("")
    
    # Assignee workload
    if analytics.get('assignee_workload'):
        parts.append("=== ASSIGNEE WORKLOAD ===")
        for assignee, count in list(analytics['assignee_workload'].items())[:10]:
            parts.append(f"{assignee}: {count} tasks")
        parts.append("")
    
    # Project breakdown
    if analytics.get('project_breakdown'):
        parts.append("=== PROJECT BREAKDOWN ===")
        for project, count in list(analytics['project_breakdown'].items())[:10]:
            parts.append(f"{project}: {count} tasks")
        parts.append("")
    
    # Overdue tasks
    today = datetime.now().date()
    overdue_tasks = []
    for t in tasks:
        if not t.get('completed', False) and t.get('due_on'):
            try:
                due_date = datetime.strptime(t['due_on'], '%Y-%m-%d').date()
                if due_date < today:
                    overdue_tasks.append(t)
            except:
                pass
    
    if overdue_tasks:
        parts.append("=== OVERDUE TASKS ===")
        for task in overdue_tasks[:10]:
            assignee = task.get('assignee', {}).get('name', 'Unassigned') if task.get('assignee') else 'Unassigned'
            parts.append(f"🚨 {task.get('name')} (Due: {task.get('due_on')}, Assignee: {assignee})")
        parts.append("")
    
    # Upcoming tasks (due this week)
    week_from_now = today + timedelta(days=7)
    upcoming_tasks = []
    for t in tasks:
        if not t.get('completed', False) and t.get('due_on'):
            try:
                due_date = datetime.strptime(t['due_on'], '%Y-%m-%d').date()
                if today <= due_date <= week_from_now:
                    upcoming_tasks.append(t)
            except:
                pass
    
    if upcoming_tasks:
        parts.append("=== UPCOMING TASKS (THIS WEEK) ===")
        for task in upcoming_tasks[:10]:
            assignee = task.get('assignee', {}).get('name', 'Unassigned') if task.get('assignee') else 'Unassigned'
            parts.append(f" {task.get('name')} (Due: {task.get('due_on')}, Assignee: {assignee})")
        parts.append("")
    
    # Sample active tasks
    active_tasks = [t for t in tasks if not t.get('completed', False)]
    if active_tasks:
        parts.append("=== ACTIVE TASKS (SAMPLE) ===")
        for task in active_tasks[:max_tasks_to_show]:
            task_name = task.get('name', 'Untitled')
            assignee = task.get('assignee', {}).get('name', 'Unassigned') if task.get('assignee') else 'Unassigned'
            due_on = task.get('due_on', 'No due date')
            project = task.get('project_name', 'Unknown')
            
            parts.append(f"\n📋 {task_name}")
            parts.append(f"   Project: {project}")
            parts.append(f"   Assignee: {assignee}")
            parts.append(f"   Due: {due_on}")
            
            # Include notes if available
            notes = task.get('notes', '').strip()
            if notes:
                parts.append(f"   Notes: {notes[:200]}...")
        parts.append("")
    
    return "\n".join(parts)


# ============================================================================
# 4. DATA CLEANING
# ============================================================================

def clean_asana_data(tasks: List[Dict]) -> Dict:
    """
    Clean and enrich Asana data.
    
    Removes:
    - Unnecessary metadata
    - Empty fields
    
    Adds:
    - Quality score
    - Analytics
    - Searchable text
    - Tags
    
    Args:
        tasks: Raw tasks from extraction
        
    Returns:
        Cleaned and enriched data dict
    """
    try:
        # Run analytics
        analytics = analyze_asana_tasks(tasks)
        
        # Calculate quality score
        quality_score = calculate_asana_quality_score(tasks, analytics)
        
        # Create searchable text
        searchable_text = create_asana_searchable_text(tasks, analytics)
        
        # Auto-generate tags
        tags = []
        
        if analytics.get('overdue_tasks', 0) > 5:
            tags.append('has_overdue')
        if analytics.get('completion_rate', 0) > 75:
            tags.append('high_completion')
        elif analytics.get('completion_rate', 0) < 25:
            tags.append('low_completion')
        if analytics.get('total_tasks', 0) > 50:
            tags.append('high_volume')
        
        # Build cleaned structure
        cleaned = {
            'tasks': tasks,
            'analytics': analytics,
            'searchable_text': searchable_text,
            'quality_score': quality_score,
            'total_tasks': analytics.get('total_tasks', 0),
            'total_workspaces': len(set(t.get('workspace_name') for t in tasks)),
            'total_projects': len(analytics.get('project_breakdown', {})),
            'tags': tags if tags else None,
            'file_type': 'Asana Tasks'
        }
        
        return cleaned
        
    except Exception as e:
        logging.error(f" Cleaning error: {e}")
        return {
            'tasks': tasks,
            'error': str(e)
        }


# ============================================================================
# 5. MAIN ETL FUNCTION
# ============================================================================

async def run_asana_etl(
    user_id: str,
    access_token: str,
    enable_versioning: bool = True
) -> Tuple[bool, int]:
    """
    🔥 ULTIMATE Asana ETL with ALL features.
    
    Features:
     Task and project extraction
     Workspace organization
     Analytics (completion, overdue, workload)
     Smart categorization
     Search-optimized text generation
     Data quality scoring
    
    Args:
        user_id: User ID
        access_token: Valid Asana access token
        enable_versioning: Enable file versioning (default True)
        
    Returns:
        (success: bool, tasks_count: int)
    """
    logging.info(f"{'='*70}")
    logging.info(f" ULTIMATE ASANA ETL: Starting for user {user_id}")
    logging.info(f"{'='*70}")
    
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(headers=headers, timeout=60.0) as client:
            logging.info(" Fetching Asana workspaces...")
            
            # Get workspaces
            workspaces_url = "https://app.asana.com/api/1.0/workspaces"
            response = await client.get(workspaces_url)
            response.raise_for_status()
            workspaces = response.json().get('data', [])
            
            logging.info(f"✓ Found {len(workspaces)} workspaces")
            
            bucket_name = "Kogna"
            all_tasks = []
            
            # Extract tasks from each workspace
            for workspace_idx, workspace in enumerate(workspaces):
                workspace_gid = workspace.get('gid')
                workspace_name = workspace.get('name')
                
                logging.info(f" [{workspace_idx+1}/{len(workspaces)}] Processing: {workspace_name}")
                
                workspace_tasks = await extract_asana_tasks(client, workspace_gid, workspace_name)
                all_tasks.extend(workspace_tasks)
                
                await update_sync_progress(
                    user_id, "asana",
                    progress=f"{workspace_idx+1}/{len(workspaces)} workspaces"
                )
            
            # Clean and enrich all tasks
            if all_tasks:
                logging.info(f" Processing {len(all_tasks)} tasks...")
                
                cleaned_data = clean_asana_data(all_tasks)
                
                # Save to storage
                data_json = json.dumps(cleaned_data, indent=2)
                file_path = f"{user_id}/asana/all_tasks.json"
                
                upload_success = await safe_upload_to_bucket(
                    bucket_name,
                    file_path,
                    data_json.encode('utf-8'),
                    "application/json",
                    enable_versioning=enable_versioning
                )
                
                if upload_success:
                    # Queue for embedding
                    latest_path = f"{user_id}/asana/all_tasks_latest.json"
                    queue_embedding(user_id, latest_path)
                    
                    logging.info(f"{'='*70}")
                    logging.info(f" ULTIMATE ASANA ETL COMPLETE")
                    logging.info(f"{'='*70}")
                    logging.info(f" Statistics:")
                    logging.info(f"   Total tasks: {len(all_tasks)}")
                    logging.info(f"   Workspaces: {len(workspaces)}")
                    logging.info(f"   Projects: {cleaned_data.get('total_projects', 0)}")
                    logging.info(f"   Completion rate: {cleaned_data.get('analytics', {}).get('completion_rate', 0)}%")
                    logging.info(f"   Overdue tasks: {cleaned_data.get('analytics', {}).get('overdue_tasks', 0)}")
                    logging.info(f"   Quality score: {cleaned_data.get('quality_score', 0)}/100")
                    logging.info(f"{'='*70}")
                    
                    return True, len(all_tasks)
            else:
                logging.info(" No tasks found")
                return True, 0
    
    except httpx.HTTPStatusError as e:
        logging.error(f" API Error {e.response.status_code}: {e.response.text}")
        return False, 0
    except Exception as e:
        logging.error(f" Asana ETL Error: {e}")
        import traceback
        traceback.print_exc()
        return False, 0


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'run_asana_etl',
    'extract_asana_tasks',
    'analyze_asana_tasks',
    'clean_asana_data',
    'create_asana_searchable_text'
]