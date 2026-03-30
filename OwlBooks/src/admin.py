# ...imports and constants...

# ...existing code...

# Add this route after the other @app.route definitions (e.g. after admin_required is defined)
import json
import os
import sys
from urllib.parse import unquote
from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash
from datetime import datetime

# Füge src zum Pfad hinzu, damit Importe funktionieren
if os.path.dirname(__file__) not in sys.path:
    sys.path.insert(0, os.path.dirname(__file__))
try:
    from src.login import get_next_month_first
except ModuleNotFoundError:
    from login import get_next_month_first

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")
BOOKS_FILE = os.path.join(os.path.dirname(__file__), "books.json")
BORROWING_FILE = os.path.join(os.path.dirname(__file__), "ausleihe.json")
GENRES_FILE = os.path.join(os.path.dirname(__file__), "genres.json")
ADMIN_USER = "admin"

def load_genres():
    """Lädt die Liste aller Genres."""
    if not os.path.exists(GENRES_FILE):
        default_genres = ["Fantasy", "Science Fiction", "Krimi", "Roman", "Sachbuch", "Kinderbuch", "Sonstiges"]
        save_genres(default_genres)
    with open(GENRES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("genres", [])

def save_genres(genres):
    """Speichert die Liste aller Genres."""
    with open(GENRES_FILE, "w", encoding="utf-8") as f:
        json.dump({"genres": genres}, f, indent=4, ensure_ascii=False)

def load_users():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)


def load_books():
    if not os.path.exists(BOOKS_FILE):
        with open(BOOKS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4, ensure_ascii=False)
    with open(BOOKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_books(books):
    with open(BOOKS_FILE, "w", encoding="utf-8") as f:
        json.dump(books, f, indent=4, ensure_ascii=False)


def load_borrowings():
    if not os.path.exists(BORROWING_FILE):
        with open(BORROWING_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4, ensure_ascii=False)
    with open(BORROWING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_borrowings(borrowings):
    with open(BORROWING_FILE, "w", encoding="utf-8") as f:
        json.dump(borrowings, f, indent=4, ensure_ascii=False)

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
        borrowings = load_borrowings()
        
        # Berechne aktive Ausleihen pro User
        active_borrowings_per_user = {}
        for b in borrowings:
            if not b.get('returned', False):
                username = b.get('username', 'Unbekannt')
                active_borrowings_per_user[username] = active_borrowings_per_user.get(username, 0) + 1
        
        return render_template("admin.html", users=users, userlist=userlist, admin=session.get("user"), active_borrowings_per_user=active_borrowings_per_user)

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

    @app.route('/admin/books', methods=['GET'])
    @admin_required
    def admin_books():
        books = load_books()
        borrowings = load_borrowings()
        genres = load_genres()

        # Gruppiere Bücher nach title, author, genre (neuere Struktur mit total/available)
        grouped_books = {}
        for book in books:
            key = (book['title'], book['author'], book['genre'])
            if key not in grouped_books:
                grouped_books[key] = {
                    'title': book['title'],
                    'author': book['author'],
                    'genre': book['genre'],
                    'total': book.get('total', 1),
                    'available': book.get('available', 0),
                    'ids': [book['id']]
                }
            else:
                # Add to existing group
                grouped_books[key]['total'] += book.get('total', 1)
                grouped_books[key]['available'] += book.get('available', 0)
                grouped_books[key]['ids'].append(book['id'])

        grouped_books_list = list(grouped_books.values())

        # --- Pagination logic ---
        PER_PAGE = 10
        try:
            page = int(request.args.get('page', 1))
            if page < 1:
                page = 1
        except ValueError:
            page = 1
        total_books = len(grouped_books_list)
        total_pages = (total_books + PER_PAGE - 1) // PER_PAGE
        start = (page - 1) * PER_PAGE
        end = start + PER_PAGE
        paginated_books = grouped_books_list[start:end]

        return render_template(
            'admin_books.html',
            grouped_books=paginated_books,
            genres=genres,
            page=page,
            total_pages=total_pages,
            per_page=PER_PAGE
        )

    @app.route('/admin/books/add', methods=['POST'])
    @admin_required
    def admin_books_add():
        books = load_books()
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        genre = request.form.get('genre', '').strip()
        quantity_str = request.form.get('quantity', '1')
        try:
            quantity = int(quantity_str)
        except ValueError:
            quantity = 1
        if not title or not author or not genre or quantity < 1:
            flash('Titel, Autor, Genre und gültige Anzahl müssen angegeben werden.', 'error')
            return redirect(url_for('admin_books'))
        
        # Check if book with same title/author/genre exists
        existing = None
        for b in books:
            if b['title'] == title and b['author'] == author and b['genre'] == genre:
                existing = b
                break
        if existing:
            existing['total'] = existing.get('total', 1) + quantity
            existing['available'] = existing.get('available', 0) + quantity
        else:
            # Neue ID bestimmen (maximal vorhandene ID + 1)
            max_id = 0
            for b in books:
                try:
                    max_id = max(max_id, int(b.get('id', 0)))
                except Exception:
                    continue
            new_book = {
                'id': str(max_id + 1),
                'title': title,
                'author': author,
                'genre': genre,
                'total': quantity,
                'available': quantity
            }
            books.append(new_book)
            save_books(books)
            flash(f"{quantity} Exemplar(e) von '{title}' hinzugefügt.", 'success')
            return redirect(url_for('admin_books'))
        # Finde das Buch eindeutig
        book = None
        for b in books:
            if b['title'] == title and b['author'] == author and b['genre'] == genre:
                book = b
                break
        if not book:
            flash('Buch nicht gefunden.', 'error')
            return redirect(url_for('admin_books'))
        total = book.get('total', 1)
        available = book.get('available', 0)
        if request.method == 'POST':
            new_title = request.form.get('title', '').strip()
            new_author = request.form.get('author', '').strip()
            new_genre = request.form.get('genre', '').strip()
            new_quantity_str = request.form.get('quantity', str(total))
            try:
                new_quantity = int(new_quantity_str)
            except ValueError:
                new_quantity = total
            if new_quantity < (total - available):
                flash('Anzahl kann nicht kleiner sein als die Anzahl ausgeliehener Exemplare.', 'error')
                return render_template('admin_books_edit.html', book={'title': new_title, 'author': new_author, 'genre': new_genre, 'total': total, 'available': available}, genres=genres)
            # Prüfe, ob die neue Kombination schon existiert (außer das aktuelle Buch)
            for b in books:
                if b is not book and b['title'] == new_title and b['author'] == new_author and b['genre'] == new_genre:
                    flash('Ein Buch mit diesen Daten existiert bereits.', 'error')
                    return render_template('admin_books_edit.html', book={'title': new_title, 'author': new_author, 'genre': new_genre, 'total': total, 'available': available}, genres=genres)
            # Aktualisiere Buchdaten
            book['title'] = new_title
            book['author'] = new_author
            book['genre'] = new_genre
            book['total'] = new_quantity
            # Passe available an, falls reduziert wird
            if available > new_quantity:
                book['available'] = new_quantity - (total - available)
            else:
                book['available'] = available + (new_quantity - total)
            save_books(books)
            flash(f"Buch '{new_title}' aktualisiert.", 'success')
            return redirect(url_for('admin_books'))
        return render_template('admin_books_edit.html', book={'title': title, 'author': author, 'genre': genre, 'total': total, 'available': available}, genres=genres)
        
        # Überfälligkeit prüfen
        return_date = datetime.fromisoformat(borrowing['return_date'])
        today = datetime.now()
        
        fine = 0.0
        if today > return_date:
            overdue_days = (today - return_date).days
            fine = overdue_days * 2.0
        
        borrowing['returned'] = True
        borrowing['fine'] = fine
        borrowing['actual_return_date'] = today.isoformat()
        
        # Increment available count
        book = next((b for b in books if b['id'] == borrowing['book_id']), None)
        if book:
            book['available'] = book.get('available', 0) + 1
        
        save_borrowings(borrowings)
        save_books(books)
        
        flash(f"Buch '{borrowing['book_title']}' als zurückgegeben markiert.", 'success')
        return redirect(url_for('admin'))

    @app.route('/admin/borrowing/delete/<borrowing_id>', methods=['POST'])
    @admin_required
    def admin_borrowing_delete(borrowing_id):
        borrowings = load_borrowings()
        books = load_books()
        
        borrowing = next((b for b in borrowings if b['id'] == borrowing_id), None)
        if not borrowing:
            flash('Ausleihe nicht gefunden.', 'error')
            return redirect(url_for('admin'))
        
        # Increment available count
        book = next((b for b in books if b['id'] == borrowing['book_id']), None)
        if book:
            book['available'] = book.get('available', 0) + 1
        
        borrowings = [b for b in borrowings if b['id'] != borrowing_id]
        
        save_borrowings(borrowings)
        save_books(books)
        
        flash(f"Ausleihe gelöscht.", 'success')
        return redirect(url_for('admin'))

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

    @app.route("/admin/reset-fines/all", methods=["POST"])
    @admin_required
    def admin_reset_all_fines():
        """Setzt die Mahngebühren UND alle Ausleihen für alle Benutzer zurück."""
        users = load_users()
        reset_count = 0
        for username, user_data in users.items():
            if isinstance(user_data, dict) and username != ADMIN_USER:
                user_data['outstanding_fines'] = 0.0
                user_data['fines_reset_date'] = get_next_month_first().isoformat()
                reset_count += 1
        save_users(users)
        
        # Alle Ausleihen löschen und Bücher wieder verfügbar machen
        borrowings = load_borrowings()
        books = load_books()
        for borrowing in borrowings:
            if not borrowing.get('returned', False):
                for book in books:
                    if book['id'] == borrowing.get('book_id'):
                        book['available'] = book.get('available', 0) + 1
                        break
        save_borrowings([])
        save_books(books)
        
        flash(f"Mahngebühren und Ausleihen für {reset_count} Benutzer zurückgesetzt.", "success")
        return redirect(url_for("admin"))

    @app.route("/admin/reset-fines/<username>", methods=["POST"])
    @admin_required
    def admin_reset_user_fines(username):
        """Setzt die Mahngebühren UND alle Ausleihen für einen bestimmten Benutzer zurück."""
        users = load_users()
        borrowings = load_borrowings()
        books = load_books()
        
        if username in users and username != ADMIN_USER:
            # Mahngebühren zurücksetzen
            users[username]['outstanding_fines'] = 0.0
            users[username]['fines_reset_date'] = get_next_month_first().isoformat()
            save_users(users)
            
            # Ausleihen dieses Benutzers löschen und Bücher wieder verfügbar machen
            remaining_borrowings = []
            for borrowing in borrowings:
                if borrowing.get('username') == username:
                    # Buch wieder verfügbar machen
                    for book in books:
                        if book['id'] == borrowing.get('book_id'):
                            book['available'] = book.get('available', 0) + 1
                            break
                else:
                    remaining_borrowings.append(borrowing)
            
            save_borrowings(remaining_borrowings)
            save_books(books)
            
            flash(f"Mahngebühren und Ausleihen für '{username}' zurückgesetzt.", "success")
        else:
            flash("Benutzer nicht gefunden oder Admin kann nicht zurückgesetzt werden.", "error")
        return redirect(url_for("admin"))

    @app.route('/admin/statistics', methods=['GET'])
    @admin_required
    def admin_statistics():
        stats = create_statistics()
        return render_template('admin_statistics.html', stats=stats)

    @app.route('/admin/statistics/genres', methods=['GET'])
    @admin_required
    def admin_statistics_genres():
        books = load_books()
        borrowings = load_borrowings()
        
        genre_borrow_counts = {}
        for b in borrowings:
            if b.get('returned', False):
                book_id = b.get('book_id')
                book = next((bk for bk in books if bk['id'] == book_id), None)
                if book:
                    genre = book.get('genre', 'Unbekannt')
                    genre_borrow_counts[genre] = genre_borrow_counts.get(genre, 0) + 1
        
        all_genres = sorted(genre_borrow_counts.items(), key=lambda x: x[1], reverse=True)
        top_50_genres = all_genres[:50]
        bottom_50_genres = all_genres[-50:] if len(all_genres) > 50 else all_genres[50:]
        
        return render_template('admin_statistics_genres.html', top_genres=top_50_genres, bottom_genres=bottom_50_genres)

    @app.route('/admin/statistics/books', methods=['GET'])
    @admin_required
    def admin_statistics_books():
        books = load_books()
        borrowings = load_borrowings()
        
        book_borrow_counts = {}
        for b in borrowings:
            if b.get('returned', False):
                book_id = b.get('book_id')
                book = next((bk for bk in books if bk['id'] == book_id), None)
                if book:
                    title = book.get('title')
                    book_borrow_counts[title] = book_borrow_counts.get(title, 0) + 1
        
        all_books = sorted(book_borrow_counts.items(), key=lambda x: x[1], reverse=True)
        top_50_books = all_books[:50]
        bottom_50_books = all_books[-50:] if len(all_books) > 50 else all_books[50:]
        
        return render_template('admin_statistics_books.html', top_books=top_50_books, bottom_books=bottom_50_books)

    @app.route('/admin/books/edit/<title>/<author>/<genre>', methods=['GET', 'POST'])
    @admin_required
    def admin_books_edit(title, author, genre):
        books = load_books()
        genres = load_genres()
        # URL decode
        title = unquote(title)
        author = unquote(author)
        genre = unquote(genre)
        # Finde das Buch eindeutig
        book = None
        for b in books:
            if b['title'] == title and b['author'] == author and b['genre'] == genre:
                book = b
                break
        if not book:
            flash('Buch nicht gefunden.', 'error')
            return redirect(url_for('admin_books'))
        total = book.get('total', 1)
        available = book.get('available', 0)
        if request.method == 'POST':
            new_title = request.form.get('title', '').strip()
            new_author = request.form.get('author', '').strip()
            new_genre = request.form.get('genre', '').strip()
            new_quantity_str = request.form.get('quantity', str(total))
            try:
                new_quantity = int(new_quantity_str)
            except ValueError:
                new_quantity = total
            if new_quantity < (total - available):
                flash('Anzahl kann nicht kleiner sein als die Anzahl ausgeliehener Exemplare.', 'error')
                return render_template('admin_books_edit.html', book={'title': new_title, 'author': new_author, 'genre': new_genre, 'total': total, 'available': available}, genres=genres)
            # Prüfe, ob die neue Kombination schon existiert (außer das aktuelle Buch)
            for b in books:
                if b is not book and b['title'] == new_title and b['author'] == new_author and b['genre'] == new_genre:
                    flash('Ein Buch mit diesen Daten existiert bereits.', 'error')
                    return render_template('admin_books_edit.html', book={'title': new_title, 'author': new_author, 'genre': new_genre, 'total': total, 'available': available}, genres=genres)
            # Aktualisiere Buchdaten
            book['title'] = new_title
            book['author'] = new_author
            book['genre'] = new_genre
            book['total'] = new_quantity
            # Passe available an, falls reduziert wird
            if available > new_quantity:
                book['available'] = new_quantity - (total - available)
            else:
                book['available'] = available + (new_quantity - total)
            save_books(books)
            flash(f"Buch '{new_title}' aktualisiert.", 'success')
            return redirect(url_for('admin_books'))
        return render_template('admin_books_edit.html', book={'title': title, 'author': author, 'genre': genre, 'total': total, 'available': available}, genres=genres)
        
    @app.route('/admin/books/delete/<title>/<author>/<genre>', methods=['POST'])
    @admin_required
    def admin_books_delete(title, author, genre):
        title = unquote(title)
        author = unquote(author)
        genre = unquote(genre)
        books = load_books()
        before = len(books)
        books = [b for b in books if not (b['title'] == title and b['author'] == author and b['genre'] == genre)]
        if len(books) == before:
            flash('Buch nicht gefunden.', 'error')
        else:
            save_books(books)
            flash(f"Alle Exemplare von '{title}' gelöscht.", 'success')
        return redirect(url_for('admin_books'))
        
    @app.route('/admin/borrowings', methods=['GET'])
    @admin_required
    def admin_borrowings():
        borrowings = load_borrowings()
        users = load_users()
        books = load_books()
        # Optional: Sort borrowings by returned status and date
        borrowings_sorted = sorted(borrowings, key=lambda b: (b.get('returned', False), b.get('borrow_date', '')), reverse=True)
        return render_template('admin_borrowings.html', borrowings=borrowings_sorted, users=users, books=books)

def create_statistics():
    """Erstellt Statistiken für die Admin-Seite."""
    books = load_books()
    borrowings = load_borrowings()
    users = load_users()
    
    # Anzahl ausgeliehener Bücher (aktive Ausleihen)
    active_borrowings = [b for b in borrowings if not b.get('returned', False)]
    total_borrowed = len(active_borrowings)
    
    # Anzahl überfälliger Bücher
    overdue = []
    for b in active_borrowings:
        try:
            return_date = datetime.fromisoformat(b['return_date'])
            if datetime.now() > return_date:
                days_overdue = (datetime.now() - return_date).days
                overdue.append({
                    'borrowing': b,
                    'days_overdue': days_overdue,
                    'fine': days_overdue * 2.0
                })
        except (KeyError, ValueError):
            continue
    total_overdue = len(overdue)
    
    # Beliebteste Genres (nach Ausleihen)
    genre_borrow_counts = {}
    for b in borrowings:
        if b.get('returned', False):  # Nur zurückgegebene zählen für Historie
            book_id = b.get('book_id')
            book = next((bk for bk in books if bk['id'] == book_id), None)
            if book:
                genre = book.get('genre', 'Unbekannt')
                genre_borrow_counts[genre] = genre_borrow_counts.get(genre, 0) + 1
    popular_genres = sorted(genre_borrow_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    
    # Beliebteste Bücher (nach Ausleihen)
    book_borrow_counts = {}
    for b in borrowings:
        if b.get('returned', False):
            book_id = b.get('book_id')
            book = next((bk for bk in books if bk['id'] == book_id), None)
            if book:
                title = book.get('title')
                book_borrow_counts[title] = book_borrow_counts.get(title, 0) + 1
    top_books = sorted(book_borrow_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    
    # Anzahl pünktlicher vs. verspäteter Rückgaben
    on_time_returns = 0
    late_returns = 0
    for b in borrowings:
        if b.get('returned', False):
            try:
                return_date = datetime.fromisoformat(b['return_date'])
                actual_return = datetime.fromisoformat(b['actual_return_date'])
                if actual_return <= return_date:
                    on_time_returns += 1
                else:
                    late_returns += 1
            except (KeyError, ValueError):
                continue
    
    # Benutzeraktivität (Anzahl Ausleihen pro Benutzer)
    user_activity = {}
    for b in borrowings:
        username = b.get('username', 'Unbekannt')
        user_activity[username] = user_activity.get(username, 0) + 1
    top_users = sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Gesamteinnahmen aus Mahngebühren
    total_fines = sum(user.get('outstanding_fines', 0.0) for user in users.values() if isinstance(user, dict))
    
    # Durchschnittliche Ausleihdauer (nur zurückgegebene Bücher)
    total_duration_days = 0
    duration_count = 0
    for b in borrowings:
        if b.get('returned', False) and b.get('actual_return_date'):
            try:
                borrow_date = datetime.fromisoformat(b['borrow_date'])
                return_date = datetime.fromisoformat(b['actual_return_date'])
                duration = (return_date - borrow_date).days
                total_duration_days += duration
                duration_count += 1
            except (KeyError, ValueError):
                continue
    
    avg_duration = round(total_duration_days / duration_count, 1) if duration_count > 0 else 0
    
    # Anzahl Mahnungen pro Nutzer (basierend auf tardy returns)
    fines_per_user = {}
    for b in borrowings:
        if b.get('returned', False) and b.get('fine', 0) > 0:
            username = b.get('username', 'Unbekannt')
            fines_per_user[username] = fines_per_user.get(username, 0) + 1
    
    top_fined_users = sorted(fines_per_user.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Gesamte Mahngebühren aus Historie
    total_fines_collected = sum(b.get('fine', 0) for b in borrowings if b.get('returned', False) and b.get('fine', 0) > 0)
    
    return {
        'total_books': len(books),
        'total_users': len([u for u in users if u != ADMIN_USER]),
        'total_borrowed': total_borrowed,
        'total_overdue': total_overdue,
        'popular_genres': popular_genres,
        'top_books': top_books,
        'on_time_returns': on_time_returns,
        'late_returns': late_returns,
        'top_users': top_users,
        'total_fines': total_fines,
        'avg_duration': avg_duration,
        'top_fined_users': top_fined_users,
        'total_fines_collected': total_fines_collected,
        'total_returns': on_time_returns + late_returns
    }
