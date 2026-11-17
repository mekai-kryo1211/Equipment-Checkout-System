"""Equipment Checkout System web application."""

import sqlite3
from datetime import date, datetime
from functools import wraps
from pathlib import Path
from os import environ

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from .services.authentication.auth_service import authenticate, create_user
from .controllers.checkout_controller import validate_checkout_request

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE = str(BASE_DIR / "equipment.db")
SCHEMA = str(BASE_DIR / "database" / "schema.sql")


def create_app(test_config=None):
    app = Flask(__name__, template_folder="presentation/templates",
                static_folder="presentation/static")
    app.config.update(
        SECRET_KEY=environ.get("SECRET_KEY", "development-only-key"),
        DATABASE=test_config["DATABASE"] if test_config and "DATABASE" in test_config else DEFAULT_DATABASE,
        SESSION_TIMEOUT_SECONDS=30 * 60,
    )
    if test_config:
        app.config.update(test_config)

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"], timeout=5)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
        return g.db

    def close_db(error=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    app.teardown_appcontext(close_db)

    def init_db():
        connection = sqlite3.connect(app.config["DATABASE"], timeout=5)
        with open(SCHEMA, encoding="utf-8") as schema_file:
            connection.executescript(schema_file.read())
        connection.commit()

        seed_users = (
            ("student@example.com", "student123", "student"),
            ("staff@example.com", "staff123", "staff"),
            ("admin@example.com", "admin123", "admin"),
        )
        for email, password, role in seed_users:
            if connection.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone() is None:
                connection.execute(
                    "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
                    (email, generate_password_hash(password), role),
                )
        seed_equipment = (
            ("Canon EOS Rebel", "Camera", "excellent"),
            ("Dell Precision Laptop", "Computer", "good"),
            ("Epson Projector", "Presentation", "good"),
            ("Yamaha Keyboard", "Audio", "fair"),
        )
        for name, category, condition in seed_equipment:
            if connection.execute("SELECT 1 FROM equipment WHERE name = ?", (name,)).fetchone() is None:
                connection.execute(
                    "INSERT INTO equipment (name, category, item_condition, status) VALUES (?, ?, ?, 'available')",
                    (name, category, condition),
                )
        connection.commit()
        connection.close()

    app.init_db = init_db
    init_db()

    def current_user():
        user_id = session.get("user_id")
        if not user_id:
            return None
        return get_db().execute(
            "SELECT user_id, email, role FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if current_user() is None:
                flash("Please log in to continue.", "error")
                return redirect(url_for("login"))
            return view(*args, **kwargs)
        return wrapped

    def role_required(*roles):
        def decorator(view):
            @wraps(view)
            def wrapped(*args, **kwargs):
                user = current_user()
                if user is None:
                    flash("Please log in to continue.", "error")
                    return redirect(url_for("login"))
                if user["role"] not in roles:
                    flash("You do not have permission to access that page.", "error")
                    return redirect(url_for("dashboard"))
                return view(*args, **kwargs)
            return wrapped
        return decorator

    def audit(db, actor_id, action, details):
        db.execute(
            "INSERT INTO audit_logs (actor_id, action, details) VALUES (?, ?, ?)",
            (actor_id, action, details),
        )

    def refresh_overdue(db):
        today = date.today().isoformat()
        db.execute(
            "UPDATE checkout_requests SET overdue = 1 "
            "WHERE status = 'approved' AND due_date < ?",
            (today,),
        )

    @app.route("/")
    def index():
        return redirect(url_for("catalog"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = authenticate(get_db(), email, password)
            if user is None:
                flash("Invalid email or password.", "error")
                return render_template("login.html"), 401
            session.clear()
            session["user_id"] = user["user_id"]
            session["role"] = user["role"]
            flash("Logged in successfully.", "success")
            return redirect(url_for("dashboard"))
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "success")
        return redirect(url_for("login"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        db = get_db()
        refresh_overdue(db)
        db.commit()
        user = current_user()
        requests = db.execute(
            "SELECT r.*, e.name AS item_name, e.category "
            "FROM checkout_requests r JOIN equipment e ON e.item_id = r.item_id "
            "WHERE r.user_id = ? ORDER BY r.created_at DESC",
            (user["user_id"],),
        ).fetchall()
        return render_template("dashboard.html", user=user, requests=requests)

    @app.route("/equipment")
    @login_required
    def catalog():
        db = get_db()
        refresh_overdue(db)
        db.commit()
        equipment = db.execute(
            "SELECT * FROM equipment ORDER BY category, name"
        ).fetchall()
        return render_template("catalog.html", equipment=equipment)

    @app.route("/requests/new/<int:item_id>", methods=["POST"])
    @login_required
    def submit_request(item_id):
        db = get_db()
        return_date = request.form.get("requested_return_date", "")
        try:
            validate_checkout_request(item_id, return_date)
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(url_for("catalog"))

        db.execute("BEGIN IMMEDIATE")
        try:
            equipment = db.execute(
                "SELECT item_id, name, status FROM equipment WHERE item_id = ?", (item_id,)
            ).fetchone()
            if equipment is None:
                raise ValueError("Equipment was not found")
            if equipment["status"] != "available":
                raise ValueError("This item is not available")
            active = db.execute(
                "SELECT 1 FROM checkout_requests "
                "WHERE item_id = ? AND status IN ('pending', 'approved')",
                (item_id,),
            ).fetchone()
            if active:
                raise ValueError("This item already has an active request")
            cursor = db.execute(
                "INSERT INTO checkout_requests (user_id, item_id, requested_return_date) "
                "VALUES (?, ?, ?)",
                (session["user_id"], item_id, return_date),
            )
            audit(db, session["user_id"], "checkout_requested",
                  f"Request {cursor.lastrowid} for {equipment['name']}")
            db.commit()
        except (sqlite3.Error, ValueError) as exc:
            db.rollback()
            flash(str(exc) if isinstance(exc, ValueError) else "The request could not be submitted.", "error")
            return redirect(url_for("catalog"))
        flash("Checkout request submitted.", "success")
        return redirect(url_for("dashboard"))

    @app.route("/staff/requests")
    @role_required("staff", "admin")
    def pending_requests():
        db = get_db()
        refresh_overdue(db)
        db.commit()
        rows = db.execute(
            "SELECT r.*, e.name AS item_name, u.email "
            "FROM checkout_requests r "
            "JOIN equipment e ON e.item_id = r.item_id "
            "JOIN users u ON u.user_id = r.user_id "
            "WHERE r.status = 'pending' ORDER BY r.created_at"
        ).fetchall()
        return render_template("pending.html", requests=rows)

    @app.route("/staff/requests/<int:request_id>/<action>", methods=["POST"])
    @role_required("staff", "admin")
    def review_request(request_id, action):
        if action not in ("approve", "deny"):
            flash("Unknown review action.", "error")
            return redirect(url_for("pending_requests"))
        db = get_db()
        db.execute("BEGIN IMMEDIATE")
        try:
            row = db.execute(
                "SELECT r.*, e.name AS item_name, e.status AS item_status "
                "FROM checkout_requests r JOIN equipment e ON e.item_id = r.item_id "
                "WHERE r.request_id = ?", (request_id,)
            ).fetchone()
            if row is None or row["status"] != "pending":
                raise ValueError("Request is no longer pending")
            if action == "approve":
                if row["item_status"] != "available":
                    raise ValueError("Equipment is no longer available")
                db.execute(
                    "UPDATE equipment SET status = 'checked_out' WHERE item_id = ?",
                    (row["item_id"],),
                )
                db.execute(
                    "UPDATE checkout_requests SET status = 'approved', approved_at = ?, "
                    "due_date = ? WHERE request_id = ?",
                    (datetime.now().isoformat(timespec="seconds"),
                     row["requested_return_date"], request_id),
                )
                audit(db, session["user_id"], "checkout_approved",
                      f"Approved request {request_id} for {row['item_name']}")
                message = "Checkout approved."
            else:
                notes = request.form.get("notes", "").strip()
                db.execute(
                    "UPDATE checkout_requests SET status = 'denied', review_notes = ? "
                    "WHERE request_id = ?", (notes, request_id),
                )
                audit(db, session["user_id"], "checkout_denied",
                      f"Denied request {request_id}; notes: {notes or 'none'}")
                message = "Checkout request denied."
            db.commit()
        except (sqlite3.Error, ValueError) as exc:
            db.rollback()
            flash(str(exc) if isinstance(exc, ValueError) else "Review could not be saved.", "error")
            return redirect(url_for("pending_requests"))
        flash(message, "success")
        return redirect(url_for("pending_requests"))

    @app.route("/staff/returns")
    @role_required("staff", "admin")
    def returns_page():
        db = get_db()
        refresh_overdue(db)
        db.commit()
        rows = db.execute(
            "SELECT r.*, e.name AS item_name, u.email "
            "FROM checkout_requests r "
            "JOIN equipment e ON e.item_id = r.item_id "
            "JOIN users u ON u.user_id = r.user_id "
            "WHERE r.status = 'approved' ORDER BY r.overdue DESC, r.due_date"
        ).fetchall()
        return render_template("returns.html", requests=rows)

    @app.route("/staff/returns/<int:request_id>", methods=["POST"])
    @role_required("staff", "admin")
    def log_return(request_id):
        condition = request.form.get("condition", "").strip().lower()
        notes = request.form.get("notes", "").strip()
        if condition not in ("excellent", "good", "fair", "damaged"):
            flash("Select a valid return condition.", "error")
            return redirect(url_for("returns_page"))
        db = get_db()
        db.execute("BEGIN IMMEDIATE")
        try:
            row = db.execute(
                "SELECT r.*, e.name AS item_name FROM checkout_requests r "
                "JOIN equipment e ON e.item_id = r.item_id "
                "WHERE r.request_id = ?", (request_id,)
            ).fetchone()
            if row is None or row["status"] != "approved":
                raise ValueError("This checkout cannot be returned")
            db.execute(
                "INSERT INTO return_records (request_id, item_id, user_id, condition, notes) "
                "VALUES (?, ?, ?, ?, ?)",
                (request_id, row["item_id"], row["user_id"], condition, notes),
            )
            db.execute("UPDATE checkout_requests SET status = 'returned' WHERE request_id = ?", (request_id,))
            db.execute(
                "UPDATE equipment SET status = 'available', item_condition = ? WHERE item_id = ?",
                (condition, row["item_id"]),
            )
            audit(db, session["user_id"], "equipment_returned",
                  f"Request {request_id} for {row['item_name']} returned; condition: {condition}")
            db.commit()
        except (sqlite3.Error, ValueError) as exc:
            db.rollback()
            flash(str(exc) if isinstance(exc, ValueError) else "Return could not be logged.", "error")
            return redirect(url_for("returns_page"))
        flash("Return logged successfully.", "success")
        return redirect(url_for("returns_page"))

    @app.route("/admin")
    @role_required("admin")
    def admin():
        db = get_db()
        users = db.execute("SELECT user_id, email, role FROM users ORDER BY email").fetchall()
        audit_rows = db.execute(
            "SELECT a.*, u.email AS actor_email FROM audit_logs a "
            "LEFT JOIN users u ON u.user_id = a.actor_id ORDER BY a.created_at DESC, a.log_id DESC LIMIT 100"
        ).fetchall()
        return render_template("admin.html", users=users, audit_rows=audit_rows)

    @app.route("/admin/users/<int:user_id>/role", methods=["POST"])
    @role_required("admin")
    def change_role(user_id):
        role = request.form.get("role", "")
        if role not in ("student", "staff", "admin"):
            flash("Invalid role.", "error")
            return redirect(url_for("admin"))
        db = get_db()
        db.execute("UPDATE users SET role = ? WHERE user_id = ?", (role, user_id))
        audit(db, session["user_id"], "role_changed", f"Changed user {user_id} role to {role}")
        db.commit()
        flash("User role updated.", "success")
        return redirect(url_for("admin"))

    @app.route("/admin/history")
    @role_required("admin", "staff")
    def history():
        db = get_db()
        rows = db.execute(
            "SELECT r.*, e.name AS item_name, u.email, rr.condition, rr.notes AS return_notes, rr.returned_at "
            "FROM checkout_requests r "
            "JOIN equipment e ON e.item_id = r.item_id "
            "JOIN users u ON u.user_id = r.user_id "
            "LEFT JOIN return_records rr ON rr.request_id = r.request_id "
            "ORDER BY r.created_at DESC"
        ).fetchall()
        return render_template("history.html", requests=rows)

    @app.errorhandler(404)
    def not_found(error):
        return render_template("error.html", title="Page not found",
                               message="The requested page does not exist."), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
