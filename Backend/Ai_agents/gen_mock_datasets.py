import json
import random
import os
from datetime import datetime, timedelta

# -------- CONFIG --------
NUM_EMPLOYEES = 200
NUM_PROJECTS = 20
AVG_TASKS_PER_PROJECT = 6
AVG_EMAILS_PER_DAY = 35
SIM_DAYS = 30
OUTPUT_DIR = "Backend/Ai_agents/mock_data_large"
random.seed(42)
# ------------------------

DEPARTMENTS = ["Engineering", "Product", "Finance", "HR", "Marketing", "Operations"]
ROLES = {
    "Engineering": ["Head of Engineering", "Software Engineer", "Data Engineer", "AI Researcher"],
    "Product": ["Head of Product", "Product Manager", "UX Designer", "Product Analyst"],
    "Finance": ["Head of Finance", "Financial Analyst", "Accountant"],
    "HR": ["Head of HR", "HR Specialist", "Recruiter"],
    "Marketing": ["Head of Marketing", "Marketing Manager", "Content Strategist"],
    "Operations": ["Head of Operations", "Ops Lead", "Analyst"]
}

def random_name():
    first = random.choice(["Alex", "Jamie", "Taylor", "Jordan", "Morgan", "Casey", "Riley", "Cameron", "Quinn", "Avery"])
    last = random.choice(["Smith", "Johnson", "Lee", "Zhang", "Patel", "Garcia", "Brown", "Davis", "Wilson", "Martinez"])
    return f"{first} {last}"

# ---------------- EMPLOYEES ----------------
def generate_employees(n):
    employees = []
    # CEO
    employees.append({
        "unique_id": "E001",
        "name": "Romeo Willis",
        "role": "CEO",
        "department": "Executive",
        "direct_reports": ""
    })

    # Department Heads
    heads = []
    emp_counter = 2
    for dept in DEPARTMENTS:
        head = {
            "unique_id": f"E{emp_counter:03d}",
            "name": random_name(),
            "role": f"Head of {dept}",
            "department": dept,
            "direct_reports": ""
        }
        employees[0]["direct_reports"] += ("," if employees[0]["direct_reports"] else "") + head["unique_id"]
        heads.append(head)
        emp_counter += 1

    # Regular Employees
    for _ in range(emp_counter, n + 2):
        dept = random.choice(DEPARTMENTS)
        role = random.choice(ROLES[dept][1:])  # skip Head role
        employees.append({
            "unique_id": f"E{emp_counter:03d}",
            "name": random_name(),
            "role": role,
            "department": dept,
            "direct_reports": ""
        })
        emp_counter += 1

    # Assign team members to department heads
    for emp in employees:
        if emp["role"].startswith("Head of"):
            subordinates = random.sample(
                [e for e in employees if e["department"] == emp["department"] and not e["role"].startswith("Head")],
                k=random.randint(5, 10)
            )
            emp["direct_reports"] = ",".join([s["unique_id"] for s in subordinates])

    return employees

# ---------------- PROJECTS & TASKS ----------------
def generate_projects(employees):
    projects = []
    for p in range(1, NUM_PROJECTS + 1):
        project_name = f"Project {p:03d}"
        dept = random.choice(DEPARTMENTS)
        owner = random.choice([e for e in employees if e["department"] == dept])
        start_date = datetime(2025, 9, random.randint(20, 25))
        deadline = start_date + timedelta(days=random.randint(10, 20))
        actual_completion = deadline + timedelta(days=random.choice([-3, 0, 2, 5]))  # simulate delay
        num_tasks = random.randint(AVG_TASKS_PER_PROJECT - 2, AVG_TASKS_PER_PROJECT + 2)

        for t in range(1, num_tasks + 1):
            assignee = random.choice([e for e in employees if e["department"] == dept])
            status = random.choices(["Completed", "In Progress", "Blocked"], weights=[0.6, 0.3, 0.1])[0]
            projects.append({
                "project_id": f"P{p:03d}",
                "project_name": project_name,
                "department": dept,
                "owner_id": owner["unique_id"],
                "task_id": f"T{p:03d}-{t:02d}",
                "task_name": f"Task {t} for {project_name}",
                "assignee_id": assignee["unique_id"],
                "status": status,
                "start_date": start_date.isoformat(),
                "deadline": deadline.isoformat(),
                "completed_at": actual_completion.isoformat() if status == "Completed" else "",
            })
    return projects

# ---------------- EMAILS ----------------
def generate_emails(employees):
    subjects = [
        "Budget Update", "Deadline Extension", "Team Sync", "Urgent Issue",
        "Project Delay", "Client Feedback", "System Alert", "Recruitment Update"
    ]
    body_templates = [
        "Hi {receiver}, please review the latest {topic} update for {project}.",
        "{receiver}, we're facing delays in {project} due to {reason}.",
        "Please confirm resource allocation for {project} ASAP.",
        "Reminder: {meeting} scheduled at {time}."
    ]
    emails = []
    for i in range(AVG_EMAILS_PER_DAY * SIM_DAYS):
        sender = random.choice(employees)
        receiver = random.choice([e for e in employees if e != sender])
        topic = random.choice(["budget", "planning", "QA", "deployment"])
        reason = random.choice(["resource shortage", "scope change", "technical issue"])
        project = f"Project {random.randint(1, NUM_PROJECTS):03d}"
        meeting = random.choice(["Weekly Sync", "Budget Review", "All Hands"])
        timestamp = (datetime(2025, 10, 1) + timedelta(days=random.randint(0, SIM_DAYS))).isoformat()
        body = random.choice(body_templates).format(receiver=receiver["name"], topic=topic, reason=reason, project=project, meeting=meeting, time="10:00 AM")

        emails.append({
            "email_id": f"EM{i+1:05d}",
            "from_employee_id": sender["unique_id"],
            "to_employee_id": receiver["unique_id"],
            "subject": random.choice(subjects),
            "body": body,
            "timestamp": timestamp
        })
    return emails

# ---------------- MEETINGS ----------------
def generate_meetings(employees):
    meetings = []
    topics = [
        "Executive Review", "Cross-Department Sync", "Budget Planning",
        "Engineering Standup", "Marketing Campaign Review", "Product Roadmap", "HR Policy Update"
    ]
    for i in range(1, NUM_PROJECTS + 10):
        organizer = random.choice(employees)
        attendees = random.sample(employees, random.randint(4, 10))
        title = random.choice(topics)
        start = datetime(2025, 10, random.randint(1, 28), random.randint(9, 16))
        end = start + timedelta(minutes=random.choice([30, 45, 60]))
        meetings.append({
            "meeting_id": f"M{i:04d}",
            "title": title,
            "organizer_id": organizer["unique_id"],
            "attendees": ",".join([a["unique_id"] for a in attendees]),
            "start_time": start.isoformat(),
            "end_time": end.isoformat()
        })
    return meetings

# ---------------- WRITE FILES ----------------
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    employees = generate_employees(NUM_EMPLOYEES)
    projects = generate_projects(employees)
    emails = generate_emails(employees)
    meetings = generate_meetings(employees)

    with open(os.path.join(OUTPUT_DIR, "employees.json"), "w") as f:
        json.dump(employees, f, indent=2)
    with open(os.path.join(OUTPUT_DIR, "projects_and_tasks.json"), "w") as f:
        json.dump(projects, f, indent=2)
    with open(os.path.join(OUTPUT_DIR, "emails.json"), "w") as f:
        json.dump(emails, f, indent=2)
    with open(os.path.join(OUTPUT_DIR, "meetings.json"), "w") as f:
        json.dump(meetings, f, indent=2)

    print(f"✅ Generated realistic dataset under '{OUTPUT_DIR}'")
    print(f"Employees: {len(employees)}, Projects: {NUM_PROJECTS}, Tasks: {len(projects)}, Emails: {len(emails)}, Meetings: {len(meetings)}")

if __name__ == "__main__":
    main()
