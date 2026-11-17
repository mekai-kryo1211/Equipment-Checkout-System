"""Validation helpers for equipment checkout requests."""

from datetime import date


def validate_checkout_request(item_id, requested_return_date):
    """Validate a checkout request before it reaches the service layer."""
    if not isinstance(item_id, int) or item_id <= 0:
        raise ValueError("A valid item ID is required")
    if not isinstance(requested_return_date, str) or not requested_return_date:
        raise ValueError("A requested return date is required")

    try:
        return_date = date.fromisoformat(requested_return_date)
    except ValueError as exc:
        raise ValueError("Return date must use YYYY-MM-DD format") from exc

    if return_date <= date.today():
        raise ValueError("Return date must be in the future")
    return True
