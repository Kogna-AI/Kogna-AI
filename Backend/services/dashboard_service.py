from core.database import get_db

def get_dashboard_data(org_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM organization_dashboard WHERE id = %s", (org_id,))
        overview = cursor.fetchone()

        cursor.execute("""
            SELECT name, value, unit, change_from_last
            FROM metrics WHERE organization_id = %s
            ORDER BY last_updated DESC LIMIT 10
        """, (org_id,))
        metrics = cursor.fetchall()

        cursor.execute("""
            SELECT id, title, progress, status
            FROM objectives WHERE organization_id = %s AND status = 'at-risk'
            ORDER BY progress ASC LIMIT 5
        """, (org_id,))
        objectives = cursor.fetchall()

        return {
            "overview": overview,
            "recent_metrics": metrics,
            "at_risk_objectives": objectives
        }
