"""Equipment Checkout System - Flask starter application."""

import os
import sqlite3

from flask import Flask, g, render_template_string

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE = os.path.join(BASE_DIR, "equipment.db")
SCHEMA = os.path.join(BASE_DIR, "database", "schema.sql")

app = Flask(__name__)


def init_db():
    """Create the database from the schema if it does not exist yet."""
    if os.path.exists(DATABASE):
        return
    connection = sqlite3.connect(DATABASE)
    with open(SCHEMA, encoding="utf-8") as schema_file:
        connection.executescript(schema_file.read())
    connection.commit()
    connection.close()


def get_db():
    """Open one database connection per request."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.route("/")
def home():
    return "<h1>Equipment Checkout System</h1><p><a href='/equipment'>View equipment catalog</a></p>"


@app.route("/equipment")
def equipment_catalog():
    rows = get_db().execute(
        "SELECT name, category, item_condition, status FROM equipment ORDER BY name"
    ).fetchall()
    page = """
    <h1>Equipment Catalog</h1>
    {% if rows %}
    <table border="1" cellpadding="6">
      <tr><th>Name</th><th>Category</th><th>Condition</th><th>Status</th></tr>
      {% for row in rows %}
      <tr>
        <td>{{ row['name'] }}</td>
        <td>{{ row['category'] }}</td>
        <td>{{ row['item_condition'] }}</td>
        <td>{{ row['status'] }}</td>
      </tr>
      {% endfor %}
    </table>
    {% else %}
    <p>No equipment has been added yet.</p>
    {% endif %}
    """
    return render_template_string(page, rows=rows)


init_db()

if __name__ == "__main__":
    app.run(debug=True)
