import os
import json
import random
from datetime import datetime, timedelta

# === CONFIG ===
OUTPUT_DIR = "Backend/Ai_agents/mock_data_large"
COMPANY_NAME = "AstraNova Technologies"
random.seed(45)
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

# === 10. OBJECTIVES ===
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

# === 15. EXTERNAL MARKET DATA ===
# (Improved Section with deeper realism)

# --- Market Trends ---
market_trends = [
    {
        "id": 1,
        "industry": "AI & Data Analytics",
        "trend": "Enterprise-wide adoption of AI-assisted decision-making and predictive modeling is accelerating across industries.",
        "growth_projection": round(random.uniform(14, 18), 2),
        "investment_volume_billion": round(random.uniform(280, 350), 1),
        "regional_leaders": ["North America", "Western Europe"],
        "emerging_markets": ["Southeast Asia", "India"],
        "key_drivers": [
            "Demand for real-time analytics and business automation",
            "Falling cost of model deployment via cloud platforms",
            "Maturity of MLOps ecosystems"
        ],
        "risk_factor": "Increased competition, rising cloud infrastructure costs, and data privacy regulations tightening.",
        "source": "Gartner Q3 2025 AI Adoption Report",
        "last_updated": datetime(2025, 9, 30).isoformat()
    },
    {
        "id": 2,
        "industry": "Cloud Infrastructure & Edge Computing",
        "trend": "Organizations are decentralizing compute workloads through hybrid cloud and edge computing for latency-sensitive applications.",
        "growth_projection": round(random.uniform(10, 14), 2),
        "investment_volume_billion": round(random.uniform(150, 200), 1),
        "key_drivers": [
            "5G rollout enabling near-real-time data processing",
            "AI model deployment closer to user endpoints",
            "Growing IoT ecosystem in logistics and healthcare"
        ],
        "risk_factor": "Vendor lock-in, security vulnerabilities at the edge, and cost unpredictability.",
        "source": "IDC Market Watch 2025: Edge-to-Cloud Integration",
        "last_updated": datetime(2025, 9, 22).isoformat()
    },
    {
        "id": 3,
        "industry": "AI Ethics, Governance & Compliance",
        "trend": "Global regulatory bodies are enacting stricter transparency and accountability frameworks for generative AI models.",
        "growth_projection": round(random.uniform(6, 9), 2),
        "key_policies": [
            "EU AI Act (2025)",
            "US Algorithmic Accountability Expansion Bill",
            "OECD AI Governance Framework"
        ],
        "impact_on_market": "Compliance-related costs projected to rise by 12% in 2026, prompting firms to invest in explainability tools.",
        "risk_factor": "Regulatory uncertainty in cross-border AI deployment.",
        "source": "World Economic Forum Insight Brief, October 2025",
        "last_updated": datetime(2025, 10, 10).isoformat()
    },
    {
        "id": 4,
        "industry": "Cybersecurity in AI Systems",
        "trend": "Data poisoning and adversarial attacks are emerging as critical vulnerabilities in ML pipelines.",
        "growth_projection": round(random.uniform(9, 12), 2),
        "key_drivers": [
            "AI model dependency in financial decision-making",
            "Rise of model extraction attacks",
            "Corporate liability for breached data models"
        ],
        "risk_factor": "Security talent shortage and fragmented defensive standards.",
        "source": "McKinsey Cyber Resilience 2025 Outlook",
        "last_updated": datetime(2025, 10, 5).isoformat()
    },
    {
        "id": 5,
        "industry": "Automation & Workforce Transformation",
        "trend": "Automation of repetitive data tasks and AI copilots are reshaping workforce roles and productivity baselines.",
        "growth_projection": round(random.uniform(8, 13), 2),
        "displaced_jobs_million": round(random.uniform(15, 25), 1),
        "new_roles_created_million": round(random.uniform(20, 28), 1),
        "risk_factor": "Skill gap in data literacy and AI supervision.",
        "source": "World Bank Digital Labor Report 2025",
        "last_updated": datetime(2025, 9, 27).isoformat()
    },
    {
        "id": 6,
        "industry": "Fintech & AI Risk Management",
        "trend": "Financial institutions are deploying generative AI to model fraud patterns, automate credit scoring, and detect bias in models.",
        "growth_projection": round(random.uniform(11, 16), 2),
        "key_drivers": [
            "Increased digital transaction volumes",
            "Pressure for fair lending and explainable AI",
            "Integration of AI into core banking APIs"
        ],
        "risk_factor": "Data governance complexity and ethical model deployment challenges.",
        "source": "Accenture Fintech Intelligence Index 2025",
        "last_updated": datetime(2025, 9, 25).isoformat()
    }
]
json.dump(market_trends, open(f"{OUTPUT_DIR}/external_market_trends.json", "w"), indent=2)

# --- Competitors (Enriched) ---
competitors = [
    {
        "id": 1,
        "company_name": "NeuraEdge Analytics",
        "focus_area": "Predictive Analytics",
        "annual_revenue_million": 118.3,
        "profit_margin_percent": 17.2,
        "employees": 640,
        "market_share_percent": 13.2,
        "r_and_d_investment_percent": 5.3,
        "ai_patent_count": 28,
        "global_presence": ["North America", "EU", "India"],
        "recent_initiatives": [
            "Launched low-code analytics for SMEs",
            "Expanded into EU data compliance consulting"
        ],
        "strength": "Enterprise trust, broad partner network",
        "weakness": "Limited innovation pipeline",
        "last_updated": datetime(2025, 10, 12).isoformat()
    },
    {
        "id": 2,
        "company_name": "Cognitix Systems",
        "focus_area": "AI Infrastructure & Cloud Tools",
        "annual_revenue_million": 231.4,
        "profit_margin_percent": 21.5,
        "employees": 1200,
        "market_share_percent": 25.1,
        "r_and_d_investment_percent": 11.7,
        "ai_patent_count": 54,
        "global_presence": ["North America", "Europe", "APAC"],
        "recent_initiatives": [
            "Partnered with telecoms for edge AI integration",
            "Invested in workforce AI upskilling programs"
        ],
        "strength": "Robust R&D and global reach",
        "weakness": "High operational cost and complex hierarchy",
        "last_updated": datetime(2025, 10, 8).isoformat()
    },
    {
        "id": 3,
        "company_name": "InsightForge Labs",
        "focus_area": "Data Visualization & AI Dashboards",
        "annual_revenue_million": 89.6,
        "profit_margin_percent": 13.9,
        "employees": 420,
        "market_share_percent": 11.5,
        "r_and_d_investment_percent": 7.8,
        "ai_patent_count": 15,
        "global_presence": ["North America", "Japan"],
        "recent_initiatives": [
            "Released cross-platform data storytelling suite",
            "Acquired BI firm focusing on healthcare analytics"
        ],
        "strength": "Agile innovation cycles",
        "weakness": "Dependence on niche clients",
        "last_updated": datetime(2025, 10, 5).isoformat()
    }
]
json.dump(competitors, open(f"{OUTPUT_DIR}/competitor_data.json", "w"), indent=2)

# --- Regional Sentiment (Expanded) ---
regions = ["North America", "Europe", "Asia-Pacific", "South America", "Middle East"]
regional_sentiment = []
for i, region in enumerate(regions, 1):
    regional_sentiment.append({
        "id": i,
        "region": region,
        "business_confidence_index": round(random.uniform(65, 90), 2),
        "consumer_sentiment_score": round(random.uniform(60, 85), 2),
        "market_activity_level": random.choice(["High", "Moderate", "Emerging"]),
        "investment_flow": random.choice(["Inbound ↑", "Stable ↔", "Outbound ↓"]),
        "industry_focus": random.choice(["AI", "Fintech", "Healthcare", "Retail", "Energy"]),
        "talent_availability": round(random.uniform(0.5, 1.0), 2),
        "notes": random.choice([
            "Increased venture capital inflows into AI startups.",
            "Corporate restructuring due to AI-driven automation.",
            "Positive hiring momentum in data and analytics roles.",
            "Local regulation tightening for AI model transparency."
        ]),
        "last_updated": datetime(2025, 10, 16).isoformat()
    })
json.dump(regional_sentiment, open(f"{OUTPUT_DIR}/regional_sentiment.json", "w"), indent=2)