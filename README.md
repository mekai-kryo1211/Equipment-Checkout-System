# Equipment Checkout System

## Project Description
The Equipment Checkout System centralizes inventory tracking and enforces accountability through role-based access and activity logging. Staff can see at any time what equipment is available and who is responsible for each item that is checked out. The system is a web application built on a layered client-server architecture.

## Team Members
- Mekai Randolph
- Mia McMillian

Team: Group 8

## Major Features
- Role-based accounts and access control for students, staff, and administrators
- Equipment catalog with name, category, condition, and availability status
- Checkout request and approval workflow
- Return logging with item condition
- Automatic overdue flagging and optional email notices
- Prevention of double-booking the same item
- Inventory and user role management for administrators
- Checkout and return history log

## Technologies Used
- Language: Python 3
- Framework: Flask
- Database: SQLite
- Front end: HTML and CSS
- Version control: Git and GitHub

## Repository Structure
- `docs/`: architecture document, requirements, and design notes
- `src/presentation/`: browser pages
- `src/controllers/`: routing, input validation, and sessions
- `src/services/`: authentication, checkout, inventory, and reporting logic
- `src/integrations/email/`: optional email notices
- `src/repositories/`: database queries
- `tests/`: unit and repository tests
- `diagrams/`: architecture diagrams
- `database/`: schema and sample data

## Setup and Installation
1. Install Python 3.10 or later.
2. Clone the repository:
   ```
   git clone https://github.com/mekai-kryo1211/Equipment-Checkout-System.git
   cd Equipment-Checkout-System
   ```
3. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate        (Windows: venv\Scripts\activate)
   ```
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Create the database from the schema:
   ```
   sqlite3 equipment.db < database/schema.sql
   ```

## How to Run
```
flask --app src/app run
```
Then open http://127.0.0.1:5000 in a browser.

## Current Status
The architecture design is complete, and the repository, issue tracking, and design documentation are in place. Implementation of the authentication, catalog, and checkout features is in progress.

## Known Issues and Limitations
- The application is not yet fully implemented, so some features listed above are planned rather than working.
- The design targets a single department or club and runs on one server and one database, so it does not scale to a whole campus.
- Email notices are optional and depend on a configured email service.
- Automated tests are not yet written for all components.
