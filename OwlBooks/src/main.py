from flask import Flask, render_template, request
from login import register_login_routes
from admin import register_admin_routes
import os
import json

# Absolute path for templates and static files
TEMPLATE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))
app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.secret_key = "geheim"

register_login_routes(app)
register_admin_routes(app)

@app.route('/')
@app.login_required
def main():
    """Einfache Startseite nach Login."""
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)