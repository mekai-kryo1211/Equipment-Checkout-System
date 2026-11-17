import sqlite3
import threading
from datetime import date, timedelta

import pytest

from src.app import create_app


@pytest.fixture
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "test.db"),
        "SECRET_KEY": "test-secret",
    })
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, email, password):
    return client.post("/login", data={"email": email, "password": password})


def add_request(app, item_id=1, student_email="student@example.com"):
    with app.app_context():
        db = sqlite3.connect(app.config["DATABASE"])
        db.row_factory = sqlite3.Row
        student = db.execute("SELECT user_id FROM users WHERE email = ?", (student_email,)).fetchone()
        due = (date.today() + timedelta(days=7)).isoformat()
        cursor = db.execute(
            "INSERT INTO checkout_requests (user_id, item_id, requested_return_date) VALUES (?, ?, ?)",
            (student["user_id"], item_id, due),
        )
        db.commit()
        return cursor.lastrowid


def test_login_logout_and_invalid_credentials(client):
    response = login(client, "student@example.com", "wrong")
    assert response.status_code == 401
    response = login(client, "student@example.com", "student123")
    assert response.status_code == 302
    assert client.get("/dashboard").status_code == 200
    client.get("/logout")
    assert client.get("/dashboard").status_code == 302


def test_role_access_is_enforced(client):
    login(client, "student@example.com", "student123")
    assert client.get("/staff/requests").status_code == 302
    assert client.get("/admin").status_code == 302

    login(client, "staff@example.com", "staff123")
    assert client.get("/staff/requests").status_code == 200
    assert client.get("/admin").status_code == 302

    login(client, "admin@example.com", "admin123")
    assert client.get("/admin").status_code == 200


def test_catalog_and_request_validation(client, app):
    login(client, "student@example.com", "student123")
    assert b"Canon EOS Rebel" in client.get("/equipment").data

    past = (date.today() - timedelta(days=1)).isoformat()
    response = client.post("/requests/new/1",
                           data={"requested_return_date": past},
                           follow_redirects=True)
    assert b"Return date must be in the future" in response.data

    future = (date.today() + timedelta(days=5)).isoformat()
    response = client.post("/requests/new/1",
                           data={"requested_return_date": future},
                           follow_redirects=True)
    assert b"Checkout request submitted" in response.data

    with app.app_context():
        db = sqlite3.connect(app.config["DATABASE"])
        count = db.execute(
            "SELECT COUNT(*) FROM checkout_requests WHERE item_id = 1 AND status = 'pending'"
        ).fetchone()[0]
        assert count == 1


def test_double_submission_is_blocked(client, app):
    login(client, "student@example.com", "student123")
    future = (date.today() + timedelta(days=3)).isoformat()
    client.post("/requests/new/1", data={"requested_return_date": future})
    client.post("/requests/new/1", data={"requested_return_date": future},
                follow_redirects=True)
    with sqlite3.connect(app.config["DATABASE"]) as db:
        count = db.execute(
            "SELECT COUNT(*) FROM checkout_requests WHERE item_id = 1"
        ).fetchone()[0]
        assert count == 1


def test_approval_checkout_and_return_workflow(client, app):
    login(client, "student@example.com", "student123")
    future = (date.today() + timedelta(days=4)).isoformat()
    client.post("/requests/new/1", data={"requested_return_date": future})
    request_id = add_request(app, item_id=2)

    login(client, "staff@example.com", "staff123")
    pending = client.get("/staff/requests")
    assert b"Canon EOS Rebel" in pending.data

    response = client.post(
        "/staff/requests/1/approve",
        data={},
        follow_redirects=True,
    )
    assert b"Checkout approved" in response.data

    with sqlite3.connect(app.config["DATABASE"]) as db:
        db.row_factory = sqlite3.Row
        checkout = db.execute(
            "SELECT status, due_date FROM checkout_requests WHERE request_id = 1"
        ).fetchone()
        item = db.execute("SELECT status FROM equipment WHERE item_id = 1").fetchone()
        assert checkout["status"] == "approved"
        assert checkout["due_date"] == future
        assert item["status"] == "checked_out"

    response = client.post(
        "/staff/returns/1",
        data={"condition": "good", "notes": "No damage"},
        follow_redirects=True,
    )
    assert b"Return logged successfully" in response.data

    with sqlite3.connect(app.config["DATABASE"]) as db:
        assert db.execute(
            "SELECT status FROM checkout_requests WHERE request_id = 1"
        ).fetchone()[0] == "returned"
        assert db.execute(
            "SELECT status, item_condition FROM equipment WHERE item_id = 1"
        ).fetchone() == ("available", "good")
        assert db.execute(
            "SELECT COUNT(*) FROM return_records WHERE request_id = 1"
        ).fetchone()[0] == 1


def test_denial_and_audit(app, client):
    login(client, "student@example.com", "student123")
    future = (date.today() + timedelta(days=2)).isoformat()
    client.post("/requests/new/1", data={"requested_return_date": future})
    login(client, "staff@example.com", "staff123")
    client.post("/staff/requests/1/deny", data={"notes": "Not available"})
    with sqlite3.connect(app.config["DATABASE"]) as db:
        assert db.execute(
            "SELECT status, review_notes FROM checkout_requests WHERE request_id = 1"
        ).fetchone() == ("denied", "Not available")
        assert db.execute(
            "SELECT COUNT(*) FROM audit_logs WHERE action = 'checkout_denied'"
        ).fetchone()[0] == 1


def test_concurrent_requests_allow_only_one(app):
    future = (date.today() + timedelta(days=5)).isoformat()
    barrier = threading.Barrier(2)
    successes = []

    def submit():
        client = app.test_client()
        login(client, "student@example.com", "student123")
        barrier.wait()
        response = client.post("/requests/new/1",
                               data={"requested_return_date": future})
        with sqlite3.connect(app.config["DATABASE"]) as db:
            count = db.execute(
                "SELECT COUNT(*) FROM checkout_requests WHERE item_id = 1"
            ).fetchone()[0]
        successes.append((response.status_code, count))

    threads = [threading.Thread(target=submit) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    with sqlite3.connect(app.config["DATABASE"]) as db:
        count = db.execute(
            "SELECT COUNT(*) FROM checkout_requests WHERE item_id = 1"
        ).fetchone()[0]
    assert count == 1
