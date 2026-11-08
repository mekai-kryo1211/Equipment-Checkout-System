"""Authentication service: password hashing and credential checks."""

from werkzeug.security import check_password_hash, generate_password_hash

VALID_ROLES = ("student", "staff", "admin")


def create_user(db, email, password, role):
    """Store a new user with a salted password hash."""
    if role not in VALID_ROLES:
        raise ValueError("Invalid role")
    db.execute(
        "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
        (email, generate_password_hash(password), role),
    )
    db.commit()


def authenticate(db, email, password):
    """Return the user row if the credentials are valid, otherwise None."""
    user = db.execute(
        "SELECT user_id, email, password_hash, role FROM users WHERE email = ?",
        (email,),
    ).fetchone()
    if user is None or not check_password_hash(user["password_hash"], password):
        return None
    return user
