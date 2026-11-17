"""Role-based authorization helpers."""

VALID_ROLE_ACTIONS = {
    "student": {"submit_request", "view_own_request"},
    "staff": {"submit_request", "view_own_request", "review_request", "log_return"},
    "admin": {"submit_request", "view_own_request", "review_request", "log_return", "manage_roles"},
}


def role_can(role, action):
    """Return whether a role is allowed to perform an action."""
    return action in VALID_ROLE_ACTIONS.get(role, ())
