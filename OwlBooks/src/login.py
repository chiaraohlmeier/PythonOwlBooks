from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json

USERS_FILE = os.path.join(os.getcwd(), "src", "users.json")
ADMIN_USER = "admin"
ADMIN_PASSWORD = "admin_pass"

def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

def register_login_routes(app):
    from functools import wraps
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user" not in session:
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        return decorated_function

    app.login_required = login_required

    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = None
        users = load_users()
        # Passwort-Ändern-Flow
        if session.get("must_change_pw") and "user" in session:
            if request.method == "POST":
                new_pw = request.form.get("new_password", "")
                new_pw2 = request.form.get("new_password2", "")
                if not new_pw or new_pw != new_pw2:
                    error = "Passwörter stimmen nicht überein!"
                else:
                    user = session["user"]
                    users[user]["password"] = generate_password_hash(new_pw)
                    users[user]["must_change_pw"] = False
                    save_users(users)
                    session.pop("must_change_pw", None)
                    flash("Passwort erfolgreich geändert.", "success")
                    return redirect(url_for("home"))
            return render_template("login.html", error=error)
        # Normales Login
        if request.method == "POST":
            user = request.form["username"]
            pw = request.form["password"]
            if user == ADMIN_USER:
                if pw == ADMIN_PASSWORD:
                    session["user"] = user
                    return redirect(url_for("home"))
                else:
                    error = "Benutzername oder Passwort falsch!"
            elif user in users:
                if users[user].get("must_change_pw", False):
                    session["user"] = user
                    session["must_change_pw"] = True
                    return redirect(url_for("login"))
                elif check_password_hash(users[user]["password"], pw):
                    session["user"] = user
                    session.pop("must_change_pw", None)
                    return redirect(url_for("home"))
                else:
                    error = "Benutzername oder Passwort falsch!"
            else:
                error = "Benutzername oder Passwort falsch!"
        return render_template("login.html", error=error)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        error = None
        if request.method == "POST":
            users = load_users()
            username = request.form["username"].strip()
            password = request.form["password"]
            if not username or not password:
                error = "Bitte Benutzername und Passwort angeben."
            elif username in users or username == ADMIN_USER:
                error = "Benutzer existiert bereits."
            else:
                users[username] = {
                    "password": generate_password_hash(password),
                    "must_change_pw": False
                }
                save_users(users)
                flash("Benutzer erfolgreich angelegt. Bitte einloggen.", "success")
                return redirect(url_for("login"))
        return render_template("register.html", error=error)

    @app.route("/logout")
    def logout():
        session.pop("user", None)
        session.pop("must_change_pw", None)
        return redirect(url_for("login"))