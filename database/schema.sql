CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('student', 'staff', 'admin'))
);

CREATE TABLE IF NOT EXISTS equipment (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    item_condition TEXT NOT NULL DEFAULT 'good',
    status TEXT NOT NULL DEFAULT 'available'
        CHECK (status IN ('available', 'checked_out', 'maintenance'))
);

CREATE TABLE IF NOT EXISTS checkout_requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    requested_return_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'denied', 'returned')),
    approved_at TEXT,
    due_date TEXT,
    overdue INTEGER NOT NULL DEFAULT 0,
    review_notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (item_id) REFERENCES equipment(item_id)
);

CREATE TABLE IF NOT EXISTS return_records (
    return_id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL UNIQUE,
    item_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    condition TEXT NOT NULL,
    notes TEXT,
    returned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES checkout_requests(request_id),
    FOREIGN KEY (item_id) REFERENCES equipment(item_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_id INTEGER,
    action TEXT NOT NULL,
    details TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (actor_id) REFERENCES users(user_id)
);
