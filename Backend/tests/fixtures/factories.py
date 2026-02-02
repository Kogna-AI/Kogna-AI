"""
Factory Boy factories for generating test data.

These factories create realistic test data for various models
used throughout the Kogna-AI application.
"""

import factory
from datetime import datetime, timedelta
from typing import List
import uuid


class UserFactory(factory.Factory):
    """Factory for creating user test data."""

    class Meta:
        model = dict

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    supabase_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    second_name = factory.Faker("last_name")
    organization_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    role = "member"
    created_at = factory.LazyFunction(datetime.utcnow)


class AdminUserFactory(UserFactory):
    """Factory for creating admin user test data."""
    role = "admin"
    email = factory.Sequence(lambda n: f"admin{n}@example.com")


class OrganizationFactory(factory.Factory):
    """Factory for creating organization test data."""

    class Meta:
        model = dict

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    name = factory.Faker("company")
    industry = factory.Faker("random_element", elements=["Technology", "Finance", "Healthcare", "Retail"])
    created_at = factory.LazyFunction(datetime.utcnow)


class TeamFactory(factory.Factory):
    """Factory for creating team test data."""

    class Meta:
        model = dict

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    name = factory.Faker("random_element", elements=["Engineering", "Product", "Sales", "Marketing", "Design"])
    organization_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    created_at = factory.LazyFunction(datetime.utcnow)


class ObjectiveFactory(factory.Factory):
    """Factory for creating objective test data."""

    class Meta:
        model = dict

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    name = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("paragraph")
    organization_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    team_responsible = factory.LazyFunction(lambda: str(uuid.uuid4()))
    status = factory.Faker("random_element", elements=["not_started", "in_progress", "completed", "at_risk"])
    progress = factory.Faker("pyfloat", min_value=0, max_value=100)
    due_date = factory.LazyFunction(lambda: (datetime.utcnow() + timedelta(days=90)).isoformat())
    created_at = factory.LazyFunction(datetime.utcnow)


class KPIFactory(factory.Factory):
    """Factory for creating KPI test data."""

    class Meta:
        model = dict

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    name = factory.Faker("random_element", elements=[
        "Monthly Revenue", "Customer Acquisition Cost", "Net Promoter Score",
        "Employee Satisfaction", "Sprint Velocity", "Bug Resolution Time"
    ])
    value = factory.Faker("pyfloat", min_value=0, max_value=1000000)
    unit = factory.Faker("random_element", elements=["USD", "%", "count", "days", "points"])
    trend = factory.Faker("pyfloat", min_value=-20, max_value=20)
    organization_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    team_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    period = factory.LazyFunction(lambda: datetime.utcnow().strftime("%Y-%m"))
    created_at = factory.LazyFunction(datetime.utcnow)


class InsightFactory(factory.Factory):
    """Factory for creating insight test data."""

    class Meta:
        model = dict

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    title = factory.Faker("sentence", nb_words=6)
    content = factory.Faker("paragraph", nb_sentences=3)
    category = factory.Faker("random_element", elements=["revenue", "performance", "risk", "opportunity"])
    priority = factory.Faker("random_element", elements=["low", "medium", "high", "critical"])
    organization_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    created_at = factory.LazyFunction(datetime.utcnow)


class JiraIssueFactory(factory.Factory):
    """Factory for creating Jira issue test data."""

    class Meta:
        model = dict

    key = factory.Sequence(lambda n: f"PROJ-{n}")
    id = factory.Sequence(lambda n: str(10000 + n))

    @factory.lazy_attribute
    def fields(self):
        return {
            "summary": factory.Faker("sentence", nb_words=5).generate(),
            "description": factory.Faker("paragraph").generate(),
            "status": {"name": factory.Faker("random_element", elements=["To Do", "In Progress", "Done"]).generate(), "id": "3"},
            "assignee": {"displayName": factory.Faker("name").generate(), "emailAddress": factory.Faker("email").generate()},
            "reporter": {"displayName": factory.Faker("name").generate(), "emailAddress": factory.Faker("email").generate()},
            "priority": {"name": factory.Faker("random_element", elements=["Low", "Medium", "High", "Critical"]).generate(), "id": "2"},
            "issuetype": {"name": "Story", "id": "10001"},
            "project": {"key": "PROJ", "name": "Project Alpha"},
            "created": datetime.utcnow().isoformat() + "+0000",
            "updated": datetime.utcnow().isoformat() + "+0000",
        }


class GoogleDriveFileFactory(factory.Factory):
    """Factory for creating Google Drive file test data."""

    class Meta:
        model = dict

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    name = factory.Faker("file_name", extension="docx")
    mimeType = "application/vnd.google-apps.document"
    createdTime = factory.LazyFunction(lambda: datetime.utcnow().isoformat() + "Z")
    modifiedTime = factory.LazyFunction(lambda: datetime.utcnow().isoformat() + "Z")
    size = factory.Faker("random_int", min=1000, max=1000000)

    @factory.lazy_attribute
    def owners(self):
        return [{"displayName": factory.Faker("name").generate(), "emailAddress": factory.Faker("email").generate()}]


class ConnectorTokenFactory(factory.Factory):
    """Factory for creating OAuth connector token test data."""

    class Meta:
        model = dict

    access_token = factory.LazyFunction(lambda: f"access-{uuid.uuid4()}")
    refresh_token = factory.LazyFunction(lambda: f"refresh-{uuid.uuid4()}")
    token_type = "Bearer"
    expires_in = 3600
    expires_at = factory.LazyFunction(lambda: (datetime.utcnow() + timedelta(hours=1)).isoformat())


class TeamMemberFactory(factory.Factory):
    """Factory for creating team member test data."""

    class Meta:
        model = dict

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    team_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    user_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    role = factory.Faker("random_element", elements=["member", "lead", "manager"])
    performance = factory.Faker("pyfloat", min_value=0, max_value=100)
    capacity = factory.Faker("pyfloat", min_value=0, max_value=100)
    joined_at = factory.LazyFunction(datetime.utcnow)


class ConversationFactory(factory.Factory):
    """Factory for creating conversation test data."""

    class Meta:
        model = dict

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    user_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    title = factory.Faker("sentence", nb_words=4)
    messages = factory.LazyFunction(lambda: [])
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class MessageFactory(factory.Factory):
    """Factory for creating message test data."""

    class Meta:
        model = dict

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    conversation_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    role = factory.Faker("random_element", elements=["user", "assistant"])
    content = factory.Faker("paragraph")
    created_at = factory.LazyFunction(datetime.utcnow)


# Batch creation helpers
def create_users(count: int = 5, **kwargs) -> List[dict]:
    """Create multiple user records."""
    return [UserFactory(**kwargs) for _ in range(count)]


def create_teams(count: int = 3, organization_id: str = None, **kwargs) -> List[dict]:
    """Create multiple team records."""
    if organization_id:
        kwargs["organization_id"] = organization_id
    return [TeamFactory(**kwargs) for _ in range(count)]


def create_kpis(count: int = 10, organization_id: str = None, **kwargs) -> List[dict]:
    """Create multiple KPI records."""
    if organization_id:
        kwargs["organization_id"] = organization_id
    return [KPIFactory(**kwargs) for _ in range(count)]


def create_objectives(count: int = 5, organization_id: str = None, **kwargs) -> List[dict]:
    """Create multiple objective records."""
    if organization_id:
        kwargs["organization_id"] = organization_id
    return [ObjectiveFactory(**kwargs) for _ in range(count)]
