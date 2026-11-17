# Project Title

Equipment Checkout System

# Description

A Flask and SQLite application for tracking equipment, student checkout requests, staff approvals, returns, and audit history.

# Team Members

- Mekai
- Mia

# Major Features

- User authentication and role-based access
- Equipment catalog with availability status
- Student checkout requests
- Staff approval and return workflows
- Audit logging and overdue notifications

# Technologies Used

- Python
- Flask
- SQLite
- Werkzeug password hashing
- GitHub Issues and Projects

# Setup Instructions

1. Install Python 3.
2. Create and activate a virtual environment.
3. Install dependencies with `pip install -r requirements.txt`.

# How to Run

From the repository root, run:

```bash
python src/app.py
```

Open `http://127.0.0.1:5000/` in a browser.

# Current Status

Architecture complete, implementation beginning.

# Known Limitations

- Authentication and role handling are initial implementation stubs.
- The checkout workflow and staff review screens are not complete.
- Email notices and scheduled overdue checks are not configured.