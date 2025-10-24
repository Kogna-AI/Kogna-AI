# This is a simulation file, and this is where we start ai_agent to analyze data
import requests
from typing import Dict, Any
from core.database import get_db

def run_ai_analysis(organization_id: int, analysis_type: str, parameters: Dict[str, Any]):
    """
    """
    payload = {
        "organization_id": organization_id,
        "analysis_type": analysis_type,
        "parameters": parameters
    }
    try:
        response = requests.post("http://localhost:4001/analyze", json=payload) 
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}



def fetch_org_data(org_id : int):
    """Collect data from multiple tables for one organization."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Metrics
        cursor.execute("""
            SELECT name, value, unit, change_from_last, last_updated
            FROM metrics
            WHERE organization_id = %s
            ORDER BY last_updated DESC
            LIMIT 20
        """, (org_id,))
        metrics = cursor.fetchall()

        # Objectives
        cursor.execute("""
            SELECT title, progress, status, team_responsible
            FROM objectives
            WHERE organization_id = %s
        """, (org_id,))
        objectives = cursor.fetchall()

        # Insights / Recommendations
        cursor.execute("""
            SELECT category, title, description, confidence, level
            FROM ai_insights
            WHERE organization_id = %s
            ORDER BY created_at DESC
            LIMIT 10
        """, (org_id,))
        insights = cursor.fetchall()

    return {
        "metrics": metrics,
        "objectives": objectives,
        "insights": insights
    }
    

