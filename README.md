# Equipment Checkout System

## Project Description

The Equipment Checkout System centralizes inventory tracking and enforces accountability through role-based access and activity logging. Staff can see what equipment is available and who is responsible for each checked-out item. The system is a Flask web application backed by SQLite.

## Team Members

- Mekai Randolph
- Mia McMillian

Team: Group 8

## Major Features

- Role-based accounts and access control for students, staff, and administrators
- Equipment catalog with name, category, condition, and availability
- Student checkout requests
- Staff and administrator approval or denial workflow
- Return logging with item condition
- Overdue checkout flagging
- Double-booking prevention
- Inventory and user role administration
- Checkout, return, and audit history

## Technologies Used

- Language: Python 3.10 or later
- Framework: Flask
- Database: SQLite
- Front end: HTML and CSS
- Testing: pytest
- Version control: Git and GitHub

## Repository Structure

- `docs/`: architecture documents and meeting notes
- `src/presentation/`: HTML templates and CSS
- `src/controllers/`: request input validation
- `src/services/`: authentication and role helpers
- `src/repositories/`: database access is implemented through SQLite in the application
- `src/integrations/email/`: optional email notice extension area
- `tests/`: pytest suite and test documentation
- `diagrams/`: architecture diagrams
- `database/`: SQLite schema

## Demo Accounts

| Role | Email | Password |
|---|---|---|
| Student | `student@example.com` | `student123` |
| Staff | `staff@example.com` | `staff123` |
| Admin | `admin@example.com` | `admin123` |

## Setup and Installation

1. Install Python 3.10 or later.
2. Clone the repository:
   ```powershell
   git clone https://github.com/mekai-kryo1211/Equipment-Checkout-System.git
   cd Equipment-Checkout-System
   ```
3. Create and activate a virtual environment:
   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
4. Install dependencies:
   ```powershell
   py -m pip install -r requirements.txt
   ```

The SQLite database at `equipment.db` and its seeded demo users/equipment are created automatically when the Flask app starts. The schema is maintained in `database/schema.sql`.

## How to Run

```powershell
py -m flask --app src.app run --debug
```

Open http://127.0.0.1:5000 in a browser.

For a stable session key outside development, set `SECRET_KEY` before starting the app:

```powershell
$env:SECRET_KEY="replace-with-a-random-secret"
py -m flask --app src.app run
```

## Validation and Testing

Run the automated suite:

```powershell
py -m pytest -q
```

Current tests cover login and logout, invalid credentials, role authorization, catalog access, return-date validation, duplicate requests, approval and return workflows, denial and audit logging, and concurrent-style submission prevention.

## Current Status

The architecture design and repository structure are complete. A working Flask/SQLite demonstration now includes authentication, role control, catalog browsing, checkout requests, staff approval or denial, return logging, overdue flags, and audit history.

## Known Issues and Limitations

- The demo uses seeded accounts and an SQLite database on one server.
- Email notices are not sent; the email integration area is a planned extension.
- Automated tests cover core workflows but do not cover every UI and operational scenario.
- The design targets one department or club and is not horizontally scaled.
- This implementation is intended for demonstration and assignment use, not production deployment.

## Future Enhancements

- Configurable SMTP email notices
- Scheduled overdue notifications
- More complete inventory and administrator management
- Expanded automated UI and repository tests
- Deployment to a shared hosted database
