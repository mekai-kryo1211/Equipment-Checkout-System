"""Session helpers for role-aware authentication."""

import time

SESSION_TIMEOUT_SECONDS = 30 * 60


def create_session(user, now=None):
    """Create an in-memory session record tied to a user's role."""
    created_at = int(time.time()) if now is None else now
    return {
        "user_id": user["user_id"],
        "role": user["role"],
        "created_at": created_at,
        "last_activity": created_at,
    }


def is_session_active(session, now=None):
    """Return False after the configured period of inactivity."""
    current_time = int(time.time()) if now is None else now
    return current_time - session["last_activity"] <= SESSION_TIMEOUT_SECONDS
