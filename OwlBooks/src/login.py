from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
from datetime import datetime

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")
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

def get_next_month_first():
    now = datetime.now()
    if now.month == 12:
        next_month = 1
        next_year = now.year + 1
    else:
        next_month = now.month + 1
        next_year = now.year
    return datetime(next_year, next_month, 1)

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
                    return redirect(url_for("admin"))
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
            full_name = request.form.get("full_name", "").strip()
            address = request.form.get("address", "").strip()
            monthly_fee_str = request.form.get("monthly_fee", "0")
            
            try:
                monthly_fee = float(monthly_fee_str)
            except (ValueError, TypeError):
                monthly_fee = 0.0
            
            if not username or not password or not full_name or not address:
                error = "Bitte alle Felder ausfüllen."
            elif username in users or username == ADMIN_USER:
                error = "Benutzer existiert bereits."
            else:
                users[username] = {
                    "password": generate_password_hash(password),
                    "must_change_pw": False,
                    "full_name": full_name,
                    "address": address,
                    "monthly_fee": monthly_fee,
                    "outstanding_fines": 0.0,
                    "fines_reset_date": get_next_month_first().isoformat()
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