import sys
import os
import json

# Füge src zum Pfad hinzu, damit Importe funktionieren
if os.path.dirname(__file__) not in sys.path:
    sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, request, session, redirect, url_for, flash

# Try to import with package prefix, fall back to local imports
try:
    from src.login import register_login_routes, load_users, save_users, get_next_month_first
    from src.admin import register_admin_routes, load_books
    from src.borrowing import borrow_book, return_book, get_user_borrowings, get_overdue_borrowings, get_user_borrowing_history, get_book_recommendations
except (ModuleNotFoundError, ImportError):
    try:
        from login import register_login_routes, load_users, save_users, get_next_month_first
        from admin import register_admin_routes, load_books
        from borrowing import borrow_book, return_book, get_user_borrowings, get_overdue_borrowings, get_user_borrowing_history, get_book_recommendations
    except ImportError as e:
        print(f"Import error: {e}")
        # Define dummy functions to avoid crashes during testing
        register_login_routes = lambda app: None
        register_admin_routes = lambda app: None
        load_books = lambda: []
        borrow_book = lambda u, b, days=14: (False, "Not available")
        return_book = lambda b: (False, "Not available")
        get_user_borrowings = lambda u: []
        get_overdue_borrowings = lambda: []
        get_user_borrowing_history = lambda u: []
        get_book_recommendations = lambda u, limit=5: []

app = Flask(__name__, template_folder="../templates")
app.secret_key = "geheim"

register_login_routes(app)
register_admin_routes(app)

@app.route('/')
@app.login_required
def home():
    """Startseite nach Login mit optionaler Suche."""
    from datetime import datetime
    try:
        books = load_books()
        if not isinstance(books, list):
            books = []
        
        # Hole Genres für die Suche
        try:
            from src.admin import load_genres
        except ModuleNotFoundError:
            from admin import load_genres
        genres = load_genres()
        
        # Suchfilter aus Query-Parametern
        search_title = request.args.get('search_title', '').strip().lower()
        search_author = request.args.get('search_author', '').strip().lower()
        search_genre = request.args.get('search_genre', '').strip()
        
        # Filtere nach Suchkriterien
        filtered_books = []
        for book in books:
            if search_title and search_title not in book.get('title', '').lower():
                continue
            if search_author and search_author not in book.get('author', '').lower():
                continue
            if search_genre and book.get('genre', '') != search_genre:
                continue
            filtered_books.append(book)
        
        # Pagination
        per_page = 10
        page = request.args.get('page', 1, type=int)
        total_books = len(filtered_books)
        total_pages = max(1, (total_books + per_page - 1) // per_page)
        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages
        
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_books = filtered_books[start_idx:end_idx]
        
        user_borrowings = get_user_borrowings(session.get('user'))
        overdue = get_overdue_borrowings()
        
        # Hole Buchempfehlungen basierend auf dem Lieblingsgenre
        recommendations = get_book_recommendations(session.get('user'), limit=5)
        
        return render_template('index.html', 
                             books=paginated_books, 
                             user_borrowings=user_borrowings, 
                             overdue=overdue, 
                             now=datetime.now().isoformat(),
                             genres=genres,
                             search_title=request.args.get('search_title', ''),
                             search_author=request.args.get('search_author', ''),
                             search_genre=request.args.get('search_genre', ''),
                             recommendations=recommendations,
                             page=page,
                             total_pages=total_pages,
                             total_books=total_books)
    except Exception as e:
        flash(f"Fehler beim Laden: {str(e)}", 'error')
        return render_template('index.html', books=[], user_borrowings=[], overdue=[], now=datetime.now().isoformat(), genres=[], search_title='', search_author='', search_genre='', recommendations=[], page=1, total_pages=1, total_books=0)

@app.route('/borrow/<book_id>', methods=['POST'])
@app.login_required
def borrow(book_id):
    """Buch ausleihen."""
    import traceback
    try:
        days = request.form.get('days', '14')
        try:
            days = int(days)
        except (ValueError, TypeError):
            days = 14
        
        success, message = borrow_book(session.get('user'), book_id, days=days)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
    except Exception as e:
        flash(f"Fehler beim Ausleihen: {str(e)}", 'error')
        import sys
        traceback.print_exc(file=sys.stdout)
    return redirect(url_for('home'))

@app.route('/return/<borrowing_id>', methods=['POST'])
@app.login_required
def return_borrowed(borrowing_id):
    """Buch zurueckgeben."""
    success, message = return_book(borrowing_id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('home'))

@app.route('/history')
@app.login_required
def history():
    """Zeigt die komplette Ausleih-Historie des Benutzers."""
    username = session.get('user')
    history = get_user_borrowing_history(username)
    
    # Sortiere nach neuesten zuerst
    history_sorted = sorted(history, key=lambda x: x.get('borrow_date', ''), reverse=True)
    
    # Statistiken berechnen
    returned_count = len([h for h in history if h.get('returned', False)])
    active_count = len([h for h in history if not h.get('returned', False)])
    total_fines = sum(h.get('fine', 0) for h in history)
    
    return render_template('history.html', 
                         history=history_sorted,
                         returned_count=returned_count,
                         active_count=active_count,
                         total_fines=total_fines)

@app.route('/profile', methods=['GET', 'POST'])
@app.login_required
def profile():
    """Persoenliche Informationen des Benutzers."""
    try:
        from src.login import load_users, save_users
    except ModuleNotFoundError:
        from login import load_users, save_users
    
    username = session.get('user')
    users = load_users()
    
    if request.method == 'POST':
        # Update user information
        full_name = request.form.get('full_name', '').strip()
        address = request.form.get('address', '').strip()
        
        if username in users:
            users[username]['full_name'] = full_name
            users[username]['address'] = address
            save_users(users)
            flash('Persoenliche Informationen aktualisiert.', 'success')
    
    # Get user data
    user_data = users.get(username, {})
    full_name = user_data.get('full_name', '')
    address = user_data.get('address', '')
    monthly_fee = user_data.get('monthly_fee', 0.0)
    
    # Check and reset outstanding fines if past reset date
    from datetime import datetime
    reset_date_str = user_data.get('fines_reset_date')
    if reset_date_str:
        try:
            reset_date = datetime.fromisoformat(reset_date_str)
            if datetime.now() >= reset_date:
                user_data['outstanding_fines'] = 0.0
                user_data['fines_reset_date'] = get_next_month_first().isoformat()
                save_users(users)
        except ValueError:
            pass
    
    total_fines = user_data.get('outstanding_fines', 0.0)
    total_charges = monthly_fee + total_fines
    
    return render_template('profile.html', 
                         username=username,
                         full_name=full_name,
                         address=address,
                         monthly_fee=monthly_fee,
                         total_fines=total_fines,
                         total_charges=total_charges)


if __name__ == '__main__':
    app.run(debug=True)
