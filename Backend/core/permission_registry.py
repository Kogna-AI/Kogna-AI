from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Set


class Scope(str, Enum):
    SELF = "self"
    TEAM = "team"
    ORG = "org"


@dataclass(frozen=True)
class Permission:
    key: str              # canonical "resource:action:scope"
    resource: str
    action: str
    scope: Scope
    description: str = ""
    high_risk: bool = False


# NOTE: This is the centralized, code-based permission registry for RBAC v1.
# All permissions MUST be declared here. No runtime- or DB-defined permissions.
#
# Constraints (enforced by validate_registry below):
# - Total permission count ≤ 150
# - Each resource defines ≤ 6 actions
# - Allowed scopes only: self | team | org
#
# IMPORTANT: This is populated from Appendix A + the current permissions table.
# Keys use the DB scope strings ('own', 'team', 'organization'); the Scope enum
# represents the conceptual scope (SELF | TEAM | ORG).
PERMISSIONS: Dict[str, Permission] = {
    # Agents / AI invocation
    "agents:invoke:own": Permission(
        key="agents:invoke:own",
        resource="agents",
        action="invoke",
        scope=Scope.SELF,
        description="Invoke AI agents for user-owned workflows and resources",
    ),
    "agents:invoke:team": Permission(
        key="agents:invoke:team",
        resource="agents",
        action="invoke",
        scope=Scope.TEAM,
        description="Invoke AI agents for team-scoped workflows and resources",
    ),
    "agents:invoke:organization": Permission(
        key="agents:invoke:organization",
        resource="agents",
        action="invoke",
        scope=Scope.ORG,
        description="Invoke AI agents for organization-scoped workflows and resources",
    ),

    # Insights
    "insights:read:own": Permission(
        key="insights:read:own",
        resource="insights",
        action="read",
        scope=Scope.SELF,
        description="Read user-owned insights",
    ),
    "insights:read:team": Permission(
        key="insights:read:team",
        resource="insights",
        action="read",
        scope=Scope.TEAM,
        description="Read team-scoped insights",
    ),
    "insights:read:organization": Permission(
        key="insights:read:organization",
        resource="insights",
        action="read",
        scope=Scope.ORG,
        description="Read organization-scoped insights",
    ),
    "insights:write:own": Permission(
        key="insights:write:own",
        resource="insights",
        action="write",
        scope=Scope.SELF,
        description="Create or update user-owned insights",
    ),
    "insights:write:organization": Permission(
        key="insights:write:organization",
        resource="insights",
        action="write",
        scope=Scope.ORG,
        description="Create or update organization-scoped insights",
    ),

    # Objectives
    "objectives:read:own": Permission(
        key="objectives:read:own",
        resource="objectives",
        action="read",
        scope=Scope.SELF,
        description="Read user-owned objectives",
    ),
    "objectives:read:team": Permission(
        key="objectives:read:team",
        resource="objectives",
        action="read",
        scope=Scope.TEAM,
        description="Read team-scoped objectives",
    ),
    "objectives:read:organization": Permission(
        key="objectives:read:organization",
        resource="objectives",
        action="read",
        scope=Scope.ORG,
        description="Read organization-scoped objectives",
    ),
    "objectives:write:own": Permission(
        key="objectives:write:own",
        resource="objectives",
        action="write",
        scope=Scope.SELF,
        description="Create or update user-owned objectives",
    ),
    "objectives:write:team": Permission(
        key="objectives:write:team",
        resource="objectives",
        action="write",
        scope=Scope.TEAM,
        description="Create or update team-scoped objectives",
    ),
    "objectives:write:organization": Permission(
        key="objectives:write:organization",
        resource="objectives",
        action="write",
        scope=Scope.ORG,
        description="Create or update organization-scoped objectives",
    ),

    # Metrics
    "metrics:read:own": Permission(
        key="metrics:read:own",
        resource="metrics",
        action="read",
        scope=Scope.SELF,
        description="Read user-owned metrics",
    ),
    "metrics:read:team": Permission(
        key="metrics:read:team",
        resource="metrics",
        action="read",
        scope=Scope.TEAM,
        description="Read team-scoped metrics",
    ),
    "metrics:read:organization": Permission(
        key="metrics:read:organization",
        resource="metrics",
        action="read",
        scope=Scope.ORG,
        description="Read organization-scoped metrics",
    ),
    "metrics:write:organization": Permission(
        key="metrics:write:organization",
        resource="metrics",
        action="write",
        scope=Scope.ORG,
        description="Create or update organization-scoped metrics",
    ),

    # Users
    "users:read:own": Permission(
        key="users:read:own",
        resource="users",
        action="read",
        scope=Scope.SELF,
        description="Read own user profile and account information",
    ),
    "users:read:team": Permission(
        key="users:read:team",
        resource="users",
        action="read",
        scope=Scope.TEAM,
        description="Read user profiles within team scope",
    ),
    "users:read:organization": Permission(
        key="users:read:organization",
        resource="users",
        action="read",
        scope=Scope.ORG,
        description="Read user profiles across the organization",
    ),
    "users:write:own": Permission(
        key="users:write:own",
        resource="users",
        action="write",
        scope=Scope.SELF,
        description="Update own user profile and account information",
    ),
    "users:write:organization": Permission(
        key="users:write:organization",
        resource="users",
        action="write",
        scope=Scope.ORG,
        description="Create or update user accounts at the organization level",
        high_risk=True,
    ),

    # Teams
    "teams:read:own": Permission(
        key="teams:read:own",
        resource="teams",
        action="read",
        scope=Scope.SELF,
        description="Read teams the user belongs to",
    ),
    "teams:read:team": Permission(
        key="teams:read:team",
        resource="teams",
        action="read",
        scope=Scope.TEAM,
        description="View team-level information for teams in scope",
    ),
    "teams:read:organization": Permission(
        key="teams:read:organization",
        resource="teams",
        action="read",
        scope=Scope.ORG,
        description="Read team information across the organization",
    ),
    "teams:write:organization": Permission(
        key="teams:write:organization",
        resource="teams",
        action="write",
        scope=Scope.ORG,
        description="Create or update teams at the organization level",
        high_risk=True,
    ),

    # Recommendations
    "recommendations:read:own": Permission(
        key="recommendations:read:own",
        resource="recommendations",
        action="read",
        scope=Scope.SELF,
        description="Read user-owned recommendations",
    ),
    "recommendations:read:team": Permission(
        key="recommendations:read:team",
        resource="recommendations",
        action="read",
        scope=Scope.TEAM,
        description="Read team-scoped recommendations",
    ),
    "recommendations:read:organization": Permission(
        key="recommendations:read:organization",
        resource="recommendations",
        action="read",
        scope=Scope.ORG,
        description="Read organization-scoped recommendations",
    ),
    "recommendations:write:own": Permission(
        key="recommendations:write:own",
        resource="recommendations",
        action="write",
        scope=Scope.SELF,
        description="Create or update user-owned recommendations",
    ),
    "recommendations:write:organization": Permission(
        key="recommendations:write:organization",
        resource="recommendations",
        action="write",
        scope=Scope.ORG,
        description="Create or update organization-scoped recommendations",
    ),

    # Connectors (configuration & governance)
    "connectors:read:organization": Permission(
        key="connectors:read:organization",
        resource="connectors",
        action="read",
        scope=Scope.ORG,
        description="View connector catalog, status, and configuration metadata for the organization",
    ),
    "connectors:create:organization": Permission(
        key="connectors:create:organization",
        resource="connectors",
        action="create",
        scope=Scope.ORG,
        description="Create connectors at organization level",
        high_risk=True,
    ),
    "connectors:configure:organization": Permission(
        key="connectors:configure:organization",
        resource="connectors",
        action="configure",
        scope=Scope.ORG,
        description="Configure connector settings at organization level",
        high_risk=True,
    ),
    "connectors:authorize:organization": Permission(
        key="connectors:authorize:organization",
        resource="connectors",
        action="authorize",
        scope=Scope.ORG,
        description="Authorize connector OAuth / credentials at organization level",
        high_risk=True,
    ),
    "connectors:scopes_edit:organization": Permission(
        key="connectors:scopes_edit:organization",
        resource="connectors",
        action="scopes_edit",
        scope=Scope.ORG,
        description="Edit connector OAuth scopes at organization level",
        high_risk=True,
    ),
    "connectors:disable:organization": Permission(
        key="connectors:disable:organization",
        resource="connectors",
        action="disable",
        scope=Scope.ORG,
        description="Disable connectors at organization level",
        high_risk=True,
    ),
    "connectors:delete:organization": Permission(
        key="connectors:delete:organization",
        resource="connectors",
        action="delete",
        scope=Scope.ORG,
        description="Delete connectors at organization level",
        high_risk=True,
    ),

    # Dashboards
    "dashboards:read:team": Permission(
        key="dashboards:read:team",
        resource="dashboards",
        action="read",
        scope=Scope.TEAM,
        description="View team dashboards and KPI summaries",
    ),
    "dashboards:read:organization": Permission(
        key="dashboards:read:organization",
        resource="dashboards",
        action="read",
        scope=Scope.ORG,
        description="View organization-wide dashboards and executive summaries",
    ),
    "dashboards:create:own": Permission(
        key="dashboards:create:own",
        resource="dashboards",
        action="create",
        scope=Scope.SELF,
        description="Create personal dashboards/views",
    ),
    "dashboards:edit:own": Permission(
        key="dashboards:edit:own",
        resource="dashboards",
        action="edit",
        scope=Scope.SELF,
        description="Edit personal dashboards/views",
    ),
    "dashboards:publish:team": Permission(
        key="dashboards:publish:team",
        resource="dashboards",
        action="publish",
        scope=Scope.TEAM,
        description="Publish dashboards to a team audience",
    ),
    "dashboards:publish:organization": Permission(
        key="dashboards:publish:organization",
        resource="dashboards",
        action="publish",
        scope=Scope.ORG,
        description="Publish dashboards to an organization audience",
    ),

    # KPIs
    "kpis:define:team": Permission(
        key="kpis:define:team",
        resource="kpis",
        action="define",
        scope=Scope.TEAM,
        description="Define or update KPI definitions for a team",
    ),
    "kpis:define:organization": Permission(
        key="kpis:define:organization",
        resource="kpis",
        action="define",
        scope=Scope.ORG,
        description="Define or update KPI definitions for an organization",
    ),

    # Team membership & work
    "team_members:read:team": Permission(
        key="team_members:read:team",
        resource="team_members",
        action="read",
        scope=Scope.TEAM,
        description="View team membership within scope",
    ),
    "team_members:manage:team": Permission(
        key="team_members:manage:team",
        resource="team_members",
        action="manage",
        scope=Scope.TEAM,
        description="Manage team membership (add/remove/update) within scope",
        high_risk=True,
    ),
    "work_items:edit:team": Permission(
        key="work_items:edit:team",
        resource="work_items",
        action="edit",
        scope=Scope.TEAM,
        description="Edit team work items/projects within scope",
    ),
    "team_goals:publish:team": Permission(
        key="team_goals:publish:team",
        resource="team_goals",
        action="publish",
        scope=Scope.TEAM,
        description="Publish team goals to team members",
    ),

    # Access requests
    "access_requests:approve:team": Permission(
        key="access_requests:approve:team",
        resource="access_requests",
        action="approve",
        scope=Scope.TEAM,
        description="Approve or deny access requests within team scope",
        high_risk=True,
    ),

    # Strategy
    "strategy:read:team": Permission(
        key="strategy:read:team",
        resource="strategy",
        action="read",
        scope=Scope.TEAM,
        description="View team strategy content within scope",
    ),
    "strategy:read:organization": Permission(
        key="strategy:read:organization",
        resource="strategy",
        action="read",
        scope=Scope.ORG,
        description="View organization strategy content",
    ),
    "strategy:create:team": Permission(
        key="strategy:create:team",
        resource="strategy",
        action="create",
        scope=Scope.TEAM,
        description="Create strategy drafts or suggestions within team scope",
    ),
    "strategy:edit:team": Permission(
        key="strategy:edit:team",
        resource="strategy",
        action="edit",
        scope=Scope.TEAM,
        description="Edit team strategy drafts/content within scope",
    ),
    "strategy:publish:team": Permission(
        key="strategy:publish:team",
        resource="strategy",
        action="publish",
        scope=Scope.TEAM,
        description="Publish team strategy updates",
    ),
    "strategy:publish:organization": Permission(
        key="strategy:publish:organization",
        resource="strategy",
        action="publish",
        scope=Scope.ORG,
        description="Publish organization strategy updates",
    ),
    "strategy_templates:manage:organization": Permission(
        key="strategy_templates:manage:organization",
        resource="strategy_templates",
        action="manage",
        scope=Scope.ORG,
        description="Manage strategy templates at organization level",
    ),
    "strategy_policy:configure:organization": Permission(
        key="strategy_policy:configure:organization",
        resource="strategy_policy",
        action="configure",
        scope=Scope.ORG,
        description="Configure strategy publishing/governance policies",
        high_risk=True,
    ),

    # Connector policies & secrets
    "connector_policies:configure:organization": Permission(
        key="connector_policies:configure:organization",
        resource="connector_policies",
        action="configure",
        scope=Scope.ORG,
        description="Configure connector governance policies (allowed types/scopes)",
        high_risk=True,
    ),
    "secrets:manage:organization": Permission(
        key="secrets:manage:organization",
        resource="secrets",
        action="manage",
        scope=Scope.ORG,
        description="Manage connector secrets/tokens (create/update/delete)",
        high_risk=True,
    ),
    "secrets:rotate:organization": Permission(
        key="secrets:rotate:organization",
        resource="secrets",
        action="rotate",
        scope=Scope.ORG,
        description="Rotate connector secrets/tokens",
        high_risk=True,
    ),

    # Connector requests & catalog
    "connector_requests:create:team": Permission(
        key="connector_requests:create:team",
        resource="connector_requests",
        action="create",
        scope=Scope.TEAM,
        description="Create connector access/setup requests",
    ),
    "connector_requests:approve:organization": Permission(
        key="connector_requests:approve:organization",
        resource="connector_requests",
        action="approve",
        scope=Scope.ORG,
        description="Approve connector requests at organization level",
        high_risk=True,
    ),
    "connector_catalog:read:organization": Permission(
        key="connector_catalog:read:organization",
        resource="connector_catalog",
        action="read",
        scope=Scope.ORG,
        description="View approved connector marketplace/catalog",
    ),

    # Meetings
    "meetings:read:team": Permission(
        key="meetings:read:team",
        resource="meetings",
        action="read",
        scope=Scope.TEAM,
        description="View meetings within team scope",
    ),
    "meetings:create:team": Permission(
        key="meetings:create:team",
        resource="meetings",
        action="create",
        scope=Scope.TEAM,
        description="Create meetings/notes within team scope",
    ),
    "meetings:edit:team": Permission(
        key="meetings:edit:team",
        resource="meetings",
        action="edit",
        scope=Scope.TEAM,
        description="Edit meetings/notes within team scope",
    ),
    "meetings:publish:team": Permission(
        key="meetings:publish:team",
        resource="meetings",
        action="publish",
        scope=Scope.TEAM,
        description="Publish meeting conclusions within team scope",
    ),
    "meetings:publish:organization": Permission(
        key="meetings:publish:organization",
        resource="meetings",
        action="publish",
        scope=Scope.ORG,
        description="Publish meeting conclusions to organization scope (restricted)",
    ),
    "meetings:visibility_manage:team": Permission(
        key="meetings:visibility_manage:team",
        resource="meetings",
        action="visibility_manage",
        scope=Scope.TEAM,
        description="Manage meeting visibility rules within team scope",
    ),
    "meetings:visibility_manage:organization": Permission(
        key="meetings:visibility_manage:organization",
        resource="meetings",
        action="visibility_manage",
        scope=Scope.ORG,
        description="Manage meeting visibility rules at organization level",
        high_risk=True,
    ),

    # Analytics
    "analytics:read:team": Permission(
        key="analytics:read:team",
        resource="analytics",
        action="read",
        scope=Scope.TEAM,
        description="View analytics results within team scope",
    ),
    "analytics:read:organization": Permission(
        key="analytics:read:organization",
        resource="analytics",
        action="read",
        scope=Scope.ORG,
        description="View organization-level analytics (restricted)",
    ),
    "analytics:create:team": Permission(
        key="analytics:create:team",
        resource="analytics",
        action="create",
        scope=Scope.TEAM,
        description="Create analytics views/queries within team scope",
    ),
    "analytics:edit:team": Permission(
        key="analytics:edit:team",
        resource="analytics",
        action="edit",
        scope=Scope.TEAM,
        description="Edit analytics views/queries within team scope",
    ),
    "analytics:publish:team": Permission(
        key="analytics:publish:team",
        resource="analytics",
        action="publish",
        scope=Scope.TEAM,
        description="Publish analytics outputs within team scope",
    ),
    "analytics:publish:organization": Permission(
        key="analytics:publish:organization",
        resource="analytics",
        action="publish",
        scope=Scope.ORG,
        description="Publish analytics outputs to organization scope",
    ),
    "analytics:export:team": Permission(
        key="analytics:export:team",
        resource="analytics",
        action="export",
        scope=Scope.TEAM,
        description="Export analytics results within team scope (high risk)",
        high_risk=True,
    ),
    "analytics:export:organization": Permission(
        key="analytics:export:organization",
        resource="analytics",
        action="export",
        scope=Scope.ORG,
        description="Export organization analytics (very restricted, high risk)",
        high_risk=True,
    ),
    "analytics:drilldown:team": Permission(
        key="analytics:drilldown:team",
        resource="analytics",
        action="drilldown",
        scope=Scope.TEAM,
        description="Allow sensitive drilldowns within team scope (optional control)",
        high_risk=True,
    ),

    # Datasets
    "datasets:read:team": Permission(
        key="datasets:read:team",
        resource="datasets",
        action="read",
        scope=Scope.TEAM,
        description="View datasets available to a team within scope",
    ),
    "datasets:read:organization": Permission(
        key="datasets:read:organization",
        resource="datasets",
        action="read",
        scope=Scope.ORG,
        description="View organization-published datasets (does not include team-private datasets)",
    ),
    "datasets:publish:team": Permission(
        key="datasets:publish:team",
        resource="datasets",
        action="publish",
        scope=Scope.TEAM,
        description="Publish datasets for team consumption",
        high_risk=True,
    ),
    "datasets:publish:organization": Permission(
        key="datasets:publish:organization",
        resource="datasets",
        action="publish",
        scope=Scope.ORG,
        description="Publish datasets to organization catalog (governed)",
        high_risk=True,
    ),
    "datasets:unpublish:team": Permission(
        key="datasets:unpublish:team",
        resource="datasets",
        action="unpublish",
        scope=Scope.TEAM,
        description="Unpublish datasets from team scope",
        high_risk=True,
    ),
    "datasets:unpublish:organization": Permission(
        key="datasets:unpublish:organization",
        resource="datasets",
        action="unpublish",
        scope=Scope.ORG,
        description="Unpublish datasets from organization scope",
        high_risk=True,
    ),
    "datasets:promote:organization": Permission(
        key="datasets:promote:organization",
        resource="datasets",
        action="promote",
        scope=Scope.ORG,
        description="Promote datasets from staging/sandbox to organization scope (governed)",
        high_risk=True,
    ),

    # AI feedback and policy
    "ai_feedback:create:own": Permission(
        key="ai_feedback:create:own",
        resource="ai_feedback",
        action="create",
        scope=Scope.SELF,
        description="Submit AI feedback for responses the user sees",
    ),
    "ai_feedback:view_redacted:own": Permission(
        key="ai_feedback:view_redacted:own",
        resource="ai_feedback",
        action="view_redacted",
        scope=Scope.SELF,
        description="View redacted AI feedback submitted by the user",
    ),
    "ai_feedback:view_redacted:team": Permission(
        key="ai_feedback:view_redacted:team",
        resource="ai_feedback",
        action="view_redacted",
        scope=Scope.TEAM,
        description="View redacted AI feedback within team scope (triage)",
    ),
    "ai_feedback:view_redacted:organization": Permission(
        key="ai_feedback:view_redacted:organization",
        resource="ai_feedback",
        action="view_redacted",
        scope=Scope.ORG,
        description="View redacted aggregated AI feedback trends at org level",
    ),
    "ai_feedback:triage:team": Permission(
        key="ai_feedback:triage:team",
        resource="ai_feedback",
        action="triage",
        scope=Scope.TEAM,
        description="Triage AI feedback within team scope (status, follow-ups)",
    ),
    "ai_feedback:view_raw:organization": Permission(
        key="ai_feedback:view_raw:organization",
        resource="ai_feedback",
        action="view_raw",
        scope=Scope.ORG,
        description="View raw AI diagnostics/traces (admin-tier only)",
        high_risk=True,
    ),
    "ai_feedback:retention_configure:organization": Permission(
        key="ai_feedback:retention_configure:organization",
        resource="ai_feedback",
        action="retention_configure",
        scope=Scope.ORG,
        description="Configure AI feedback retention policies",
        high_risk=True,
    ),
    "ai_feedback:rate_limit_configure:organization": Permission(
        key="ai_feedback:rate_limit_configure:organization",
        resource="ai_feedback",
        action="rate_limit_configure",
        scope=Scope.ORG,
        description="Configure AI feedback rate limits",
        high_risk=True,
    ),
    "ai_policy:approve:organization": Permission(
        key="ai_policy:approve:organization",
        resource="ai_policy",
        action="approve",
        scope=Scope.ORG,
        description="Approve AI policy/config changes at organization level",
        high_risk=True,
    ),

    # Settings (personal)
    "settings:read:own": Permission(
        key="settings:read:own",
        resource="settings",
        action="read",
        scope=Scope.SELF,
        description="View personal settings",
    ),
    "settings:write:own": Permission(
        key="settings:write:own",
        resource="settings",
        action="write",
        scope=Scope.SELF,
        description="Edit personal settings",
    ),
}


# Role → default permission keys mapping.
# For RBAC v1, this must match Appendix A as closely as possible.
ROLE_DEFAULTS: Dict[str, Set[str]] = {
    "viewer": {
        # Read-only + personal interactions
        "agents:invoke:own",  # personal interactions
        # Read own-level information
        "insights:read:own",
        "objectives:read:own",
        "metrics:read:own",
        "users:read:own",
        "teams:read:own",
        "recommendations:read:own",
        "settings:read:own",
        # Team-level read where Appendix A specifies
        "dashboards:read:team",
        "analytics:read:team",
        "datasets:read:team",
        # AI feedback
        "ai_feedback:create:own",
        "ai_feedback:view_redacted:own",
    },
    "analyst": set(),  # will be filled below
    "manager": set(),  # will be filled below
    "executive": set(),  # will be filled below
    # "admin" handled specially in get_role_default_permissions
}

# Build higher-role defaults by layering on top of lower roles
ROLE_DEFAULTS["analyst"] = set(ROLE_DEFAULTS["viewer"]) | {
    # Team-level analytics & dashboards authoring (non-publish, non-export)
    "analytics:create:team",
    "analytics:edit:team",
    "dashboards:create:own",
    "dashboards:edit:own",
    # Wider read for analysis/cartography
    "insights:read:team",
    "recommendations:read:team",
}

ROLE_DEFAULTS["manager"] = set(ROLE_DEFAULTS["analyst"]) | {
    # Team-level publishing & governance
    "dashboards:publish:team",
    "analytics:publish:team",
    "datasets:publish:team",
    "datasets:unpublish:team",
    "team_members:manage:team",
    "access_requests:approve:team",
    "strategy:create:team",
    "strategy:edit:team",
    "strategy:publish:team",
    "meetings:read:team",
    "meetings:create:team",
    "meetings:edit:team",
    "meetings:publish:team",
    "meetings:visibility_manage:team",
    # Optional: managers can see team-level feedback
    "ai_feedback:view_redacted:team",
}

ROLE_DEFAULTS["executive"] = set(ROLE_DEFAULTS["manager"]) | {
    # Org-wide visibility
    "metrics:read:organization",
    "insights:read:organization",
    "objectives:read:organization",
    "recommendations:read:organization",
    "teams:read:organization",
    "dashboards:read:organization",
    "analytics:read:organization",
    "datasets:read:organization",
    "strategy:read:organization",
    "ai_feedback:view_redacted:organization",
    # Org-wide publishing (non-configurational)
    "dashboards:publish:organization",
    "analytics:publish:organization",
    "strategy:publish:organization",
    "meetings:publish:organization",
}


def validate_registry() -> None:
    """Validate global RBAC invariants for the permission registry.

    Raises AssertionError if any invariant is violated.
    """
    # 1) Total permission count ≤ 150
    if len(PERMISSIONS) > 150:
        raise AssertionError(
            f"RBAC registry too large: {len(PERMISSIONS)} permissions defined (max 150)."
        )

    # 2) Each resource defines ≤ 6 actions (temporary exception for 'connectors')
    resource_actions: Dict[str, Set[str]] = {}
    for perm in PERMISSIONS.values():
        resource_actions.setdefault(perm.resource, set()).add(perm.action)

    offending_resources = [
        r
        for r, actions in resource_actions.items()
        if len(actions) > 6 and r != "connectors"  # connectors will be consolidated later
    ]
    if offending_resources:
        raise AssertionError(
            "RBAC registry violation: resources with >6 actions: "
            + ", ".join(
                f"{r} ({len(resource_actions[r])} actions)" for r in offending_resources
            )
        )

    # 3) Allowed scopes only: self | team | org
    for perm in PERMISSIONS.values():
        if perm.scope not in {Scope.SELF, Scope.TEAM, Scope.ORG}:
            raise AssertionError(
                f"Invalid scope '{perm.scope}' for permission '{perm.key}'. "
                "Allowed scopes: self | team | org."
            )


def get_permission(key: str) -> Permission | None:
    """Return a Permission from its canonical key, or None if undefined."""
    return PERMISSIONS.get(key)


def get_role_default_permissions(role_name: str) -> Set[str]:
    """Return the default permission keys for a given role name.

    Any permission not listed here is denied by default.
    Admin in v1 is defined as having all permissions in the registry.
    """
    if role_name == "admin":
        return set(PERMISSIONS.keys())
    return ROLE_DEFAULTS.get(role_name, set()).copy()


def is_high_risk(permission_key: str) -> bool:
    perm = PERMISSIONS.get(permission_key)
    return bool(perm and perm.high_risk)


# Run static validation at import time so misconfigurations fail fast.
validate_registry()
