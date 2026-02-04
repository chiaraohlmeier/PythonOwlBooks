import json
import os
from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash

USERS_FILE = os.path.join(os.getcwd(), "src", "users.json")
ADMIN_USER = "admin"  # Passe ggf. an

def load_users():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

def register_admin_routes(app):
    def admin_required(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user" not in session or session["user"] != ADMIN_USER:
                flash("Nur für Administratoren zugänglich.", "error")
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        return decorated_function

    @app.route("/admin", methods=["GET", "POST"])
    @admin_required
    def admin():
        users = load_users()
        userlist = [u for u, v in users.items() if isinstance(v, dict) and "password" in v]
        return render_template("admin.html", users=users, userlist=userlist, admin=session.get("user"))

    @app.route("/admin/add", methods=["POST"])
    @admin_required
    def admin_add():
        users = load_users()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Benutzername und Passwort dürfen nicht leer sein.", "error")
        elif username in users:
            flash("Benutzer existiert bereits.", "error")
        else:
            users[username] = {
                "password": generate_password_hash(password),
                "must_change_pw": False
            }
            save_users(users)
            flash(f"Benutzer '{username}' hinzugefügt.", "success")
        return redirect(url_for("admin"))

    @app.route("/admin/delete/<username>", methods=["POST"])
    @admin_required
    def admin_delete(username):
        users = load_users()
        if username == ADMIN_USER:
            flash("Der Admin-Benutzer kann nicht gelöscht werden.", "error")
        elif username in users:
            del users[username]
            save_users(users)
            flash(f"Benutzer '{username}' gelöscht.", "success")
        else:
            flash("Benutzer nicht gefunden.", "error")
        return redirect(url_for("admin"))

    @app.route("/admin/password/<username>", methods=["POST"])
    @admin_required
    def admin_password(username):
        users = load_users()
        new_password = request.form.get("new_password", "")
        if username in users and new_password:
            users[username]["password"] = generate_password_hash(new_password)
            users[username]["must_change_pw"] = True  # Benutzer muss Passwort beim nächsten Login ändern
            save_users(users)
            flash(f"Passwort für '{username}' geändert. Benutzer muss es beim nächsten Login neu setzen.", "success")
        else:
            flash("Ungültige Eingabe.", "error")
        return redirect(url_for("admin"))

    @app.route("/admin/reset/<username>", methods=["POST"])
    @admin_required
    def admin_reset(username):
        users = load_users()
        if username in users:
            # Setze ein zufälliges Passwort, das niemand kennt
            users[username]["password"] = generate_password_hash(os.urandom(16).hex())
            users[username]["must_change_pw"] = True
            save_users(users)
            flash(f"Passwort für '{username}' wurde zurückgesetzt. Benutzer muss beim nächsten Login ein neues Passwort setzen.", "success")
        else:
            flash("Benutzer nicht gefunden.", "error")
        return redirect(url_for("admin"))