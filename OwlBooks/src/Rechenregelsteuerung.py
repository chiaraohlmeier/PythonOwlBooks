from flask import Flask, render_template, request
from login import register_login_routes
from admin import register_admin_routes
import os
import json

app = Flask(__name__, template_folder="../templates")
app.secret_key = "geheim"

register_login_routes(app)
register_admin_routes(app)

@app.route('/')
@app.login_required
def home():
    """Einfache Startseite nach Login."""
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)