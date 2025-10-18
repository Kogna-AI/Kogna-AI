import os
import json
import random
from datetime import datetime, timedelta

# === CONFIG ===
OUTPUT_DIR = "Backend/Ai_agents/mock_data_enterprise"
COMPANY_NAME = "AstraNova Technologies"
random.seed(42)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === 1. ORGANIZATION ===
organization = {
    "id": 1,
    "Name": COMPANY_NAME,
    "team_size": 125,
    "industry": "AI & Data Analytics",
    "created_at": datetime(2023, 7, 1).isoformat(),
    "project_number": 6
}
json.dump(organization, open(f"{OUTPUT_DIR}/organization.json", "w"), indent=2)

# === 2. TEAMS ===
departments = ["Engineering", "Product", "Finance", "HR", "Marketing", "Operations"]
teams = [
    {
        "id": i + 1,
        "organization_id": 1,
        "name": dept,
        "created_at": (datetime(2023, 7, 1) + timedelta(days=i)).isoformat()
    }
    for i, dept in enumerate(departments)
]
json.dump(teams, open(f"{OUTPUT_DIR}/teams.json", "w"), indent=2)

# === 3. USERS ===
roles = {
    "Engineering": ["Software Engineer", "Data Engineer", "AI Researcher"],
    "Product": ["Product Manager", "UX Designer", "Business Analyst"],
    "Finance": ["Financial Analyst", "Accountant"],
    "HR": ["HR Specialist", "Recruiter"],
    "Marketing": ["Marketing Manager", "Content Strategist"],
    "Operations": ["Ops Lead", "Analyst"]
}

users = []
uid = 1
for team in teams:
    for _ in range(random.randint(8, 15)):
        users.append({
            "id": uid,
            "organization_id": 1,
            "first_name": random.choice(["Alex", "Jordan", "Taylor", "Morgan", "Riley", "Quinn", "Casey", "Jamie", "Avery", "Dylan"]),
            "second_name": random.choice(["Smith", "Lee", "Brown", "Johnson", "Martinez", "Davis", "Zhang", "Nguyen"]),
            "role": random.choice(roles[team["name"]]),
            "created_at": datetime(2024, 1, random.randint(1, 28)).isoformat()
        })
        uid += 1
json.dump(users, open(f"{OUTPUT_DIR}/users.json", "w"), indent=2)

# === 4. TEAM MEMBERS ===
team_members = []
tm_id = 1
for team in teams:
    team_users = [u for u in users if u["role"] in roles[team["name"]]]
    for user in random.sample(team_users, min(8, len(team_users))):
        team_members.append({
            "id": tm_id,
            "team_id": team["id"],
            "user_id": user["id"],
            "role": user["role"],
            "performance": round(random.uniform(0.6, 1.0), 2),
            "capacity": round(random.uniform(0.5, 1.0), 2),
            "project_count": random.randint(1, 5),
            "status": random.choice(["available", "busy"])
        })
        tm_id += 1
json.dump(team_members, open(f"{OUTPUT_DIR}/team_members.json", "w"), indent=2)

# === 5. TEAM SKILLS ===
skills = {
    "Engineering": ["Python", "SQL", "Machine Learning", "Cloud"],
    "Product": ["Market Research", "UX Design", "Prototyping"],
    "Finance": ["Budgeting", "Forecasting", "Excel Modeling"],
    "HR": ["Recruitment", "Training", "Policy Management"],
    "Marketing": ["SEO", "Content Strategy", "Social Media"],
    "Operations": ["Logistics", "Supply Chain", "Data Reporting"]
}
team_skills = []
ts_id = 1
for team in teams:
    for skill in skills[team["name"]]:
        team_skills.append({
            "id": ts_id,
            "team_id": team["id"],
            "skill_name": skill,
            "proficiency": round(random.uniform(0.6, 0.95), 2)
        })
        ts_id += 1
json.dump(team_skills, open(f"{OUTPUT_DIR}/team_skills.json", "w"), indent=2)

# === 6. DATA SOURCES ===
data_sources = [
    {
        "id": 1,
        "organization_id": 1,
        "name": "Internal Metrics DB",
        "type": "internal",
        "connection_info": {"host": "metrics-db.local", "port": 5432},
        "last_updated": datetime(2025, 10, 10).isoformat()
    },
    {
        "id": 2,
        "organization_id": 1,
        "name": "External Market Insights API",
        "type": "external",
        "connection_info": {"api_url": "https://marketdata.api"},
        "last_updated": datetime(2025, 10, 12).isoformat()
    }
]
json.dump(data_sources, open(f"{OUTPUT_DIR}/data_sources.json", "w"), indent=2)

# === 7. DATASETS ===
datasets = [
    {
        "id": 1,
        "data_source_id": 1,
        "name": "Team Performance Metrics",
        "schema": {"columns": ["team_id", "efficiency", "output", "error_rate"]},
        "data_refresh_rate": "weekly",
        "created_at": datetime(2024, 5, 1).isoformat()
    },
    {
        "id": 2,
        "data_source_id": 2,
        "name": "Market Sentiment Trends",
        "schema": {"columns": ["region", "sentiment_score", "trend_index"]},
        "data_refresh_rate": "monthly",
        "created_at": datetime(2024, 6, 10).isoformat()
    }
]
json.dump(datasets, open(f"{OUTPUT_DIR}/datasets.json", "w"), indent=2)

# === 8. DATA RECORDS ===
data_records = []
for i in range(1, 11):
    data_records.append({
        "id": i,
        "dataset_id": 1,
        "record_data": {
            "team_id": random.randint(1, 6),
            "efficiency": round(random.uniform(0.7, 1.0), 2),
            "output": random.randint(70, 120),
            "error_rate": round(random.uniform(0.01, 0.1), 2)
        },
        "imported_at": datetime(2025, 10, 15).isoformat()
    })
json.dump(data_records, open(f"{OUTPUT_DIR}/data_records.json", "w"), indent=2)

# === 9. METRICS ===
metric_names = [
    ("Team Efficiency", "%"), ("Project Delivery Rate", "%"),
    ("Employee Utilization", "%"), ("Customer Retention", "%")
]
metrics = []
for i, (name, unit) in enumerate(metric_names, 1):
    val = round(random.uniform(70, 95), 2)
    metrics.append({
        "id": i,
        "organization_id": 1,
        "name": name,
        "value": val,
        "unit": unit,
        "change_from_last": round(random.uniform(-3, 3), 2),
        "last_updated": datetime(2025, 10, 14).isoformat()
    })
json.dump(metrics, open(f"{OUTPUT_DIR}/metrics.json", "w"), indent=2)

# === 10. OBJECTIVES / MILESTONES ===
objectives = [
    {
        "id": 1,
        "organization_id": 1,
        "title": "Improve Cross-Team Coordination",
        "progress": 0.64,
        "status": "at-risk",
        "team_responsible": "Operations",
        "created_at": datetime(2025, 1, 20).isoformat()
    },
    {
        "id": 2,
        "organization_id": 1,
        "title": "Enhance Data Infrastructure Reliability",
        "progress": 0.85,
        "status": "on-track",
        "team_responsible": "Engineering",
        "created_at": datetime(2025, 2, 10).isoformat()
    }
]
json.dump(objectives, open(f"{OUTPUT_DIR}/objectives.json", "w"), indent=2)

# === 11. MEETINGS ===
meetings = []
for i in range(1, 5):
    dept = random.choice(departments)
    start_time = datetime(2025, 10, random.randint(10, 17), 10, 0)
    content = (
        f"The {dept} department held its bi-weekly progress meeting to review "
        "current project deliverables, discuss internal bottlenecks, and review "
        "collaboration metrics. Emphasis was placed on improving reporting cadence "
        "and aligning communication flows between dependent teams."
    )
    actions = [
        "Summarize deliverables by end of week",
        "Standardize cross-departmental progress updates",
        "Schedule follow-up sync next Wednesday"
    ]
    meetings.append({
        "id": i,
        "organization_id": 1,
        "title": f"{dept} Department Sync - Week {i+40}",
        "category": "team",
        "scheduled_time": start_time.isoformat(),
        "duration": 60,
        "content": content,
        "action_items": actions
    })
json.dump(meetings, open(f"{OUTPUT_DIR}/meetings.json", "w"), indent=2)

# === 12. FEEDBACK ===
feedback = []
for i in range(1, 10):
    uid = random.choice(users)["id"]
    feedback.append({
        "id": i,
        "user_id": uid,
        "rating": random.choice([3, 4, 5]),
        "comment": random.choice([
            "Communication within the product team could improve.",
            "Appreciate the clearer timelines recently introduced.",
            "Would like more structured feedback from project leads.",
            "Great collaboration between Engineering and Marketing this month."
        ]),
        "written_at": datetime(2025, 10, random.randint(10, 17)).isoformat()
    })
json.dump(feedback, open(f"{OUTPUT_DIR}/feedback.json", "w"), indent=2)

# === 13. FEEDBACK TAGS ===
feedback_tags = []
tag_types = ["suggestion", "concern", "praise"]
for fb in feedback:
    feedback_tags.append({
        "id": fb["id"],
        "feedback_id": fb["id"],
        "tag": random.choice(tag_types)
    })
json.dump(feedback_tags, open(f"{OUTPUT_DIR}/feedback_tags.json", "w"), indent=2)

# === 14. FEEDBACK METRICS ===
feedback_metrics = {
    "id": 1,
    "organization_id": 1,
    "clarity_improvement": 0.12,
    "action_rate_increase": 0.08,
    "resolution_speed": 0.91,
    "user_satisfaction": 4.3,
    "updated_at": datetime(2025, 10, 16).isoformat()
}
json.dump(feedback_metrics, open(f"{OUTPUT_DIR}/feedback_metrics.json", "w"), indent=2)

print(f"✅ Mock data successfully generated in {OUTPUT_DIR}")
