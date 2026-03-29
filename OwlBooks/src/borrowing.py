import json
import os
import sys

# Füge src zum Pfad hinzu, damit Importe funktionieren
if os.path.dirname(__file__) not in sys.path:
    sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
try:
    from src.login import load_users, save_users
except ModuleNotFoundError:
    from login import load_users, save_users

BORROWING_FILE = os.path.join(os.path.dirname(__file__), "ausleihe.json")
BOOKS_FILE = os.path.join(os.path.dirname(__file__), "books.json")

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

def borrow_book(username, book_id, days=14):
    """Benutzer leiht sich ein Buch aus."""
    try:
        books = load_books()
        borrowings = load_borrowings()
        
        if not isinstance(books, list):
            return False, "Fehler: Buecherdatenstruktur fehlerhaft."
        
        book = None
        for b in books:
            if isinstance(b, dict) and b.get('id') == book_id:
                book = b
                break
        
        if not book:
            return False, "Buch nicht gefunden."
        
        # Check available count
        available = book.get('available', 0)
        if available <= 0:
            return False, "Buch ist nicht verfuegbar."
        
        borrow_date = datetime.now().isoformat()
        return_date = (datetime.now() + timedelta(days=days)).isoformat()
        
        borrowing = {
            'id': str(len(borrowings) + 1),
            'username': username,
            'book_id': book_id,
            'book_title': book.get('title', 'Unbekannt'),
            'borrow_date': borrow_date,
            'return_date': return_date,
            'returned': False,
            'fine': 0.0
        }
        
        borrowings.append(borrowing)
        book['available'] = available - 1
        
        save_borrowings(borrowings)
        save_books(books)
        
        return True, f"Buch '{book.get('title', '')}' erfolgreich ausgeliehen."
    except Exception as e:
        return False, f"Fehler beim Ausleihen: {str(e)}"

def return_book(borrowing_id):
    """Buch zurueckgeben."""
    try:
        borrowings = load_borrowings()
        books = load_books()
        
        borrowing = None
        for b in borrowings:
            if isinstance(b, dict) and b.get('id') == borrowing_id and not b.get('returned', False):
                borrowing = b
                break
        
        if not borrowing:
            return False, "Ausleihe nicht gefunden."
        
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
        for book in books:
            if isinstance(book, dict) and book.get('id') == borrowing['book_id']:
                book['available'] = book.get('available', 0) + 1
                break
        
        save_borrowings(borrowings)
        save_books(books)
        
        if fine > 0:
            users = load_users()
            username = borrowing.get('username')
            if username in users:
                users[username]['outstanding_fines'] = users[username].get('outstanding_fines', 0.0) + fine
                save_users(users)
        
        if fine > 0:
            return True, f"Buch zurueckgegeben. Mahngebuehr: {fine:.2f} EUR"
        else:
            return True, "Buch erfolgreich zurueckgegeben."
    except Exception as e:
        return False, f"Fehler beim Zurueckgeben: {str(e)}"

def get_user_borrowings(username):
    """Gibt alle aktiven Ausleihen eines Benutzers zurueck."""
    try:
        borrowings = load_borrowings()
        if not isinstance(borrowings, list):
            return []
        return [b for b in borrowings if isinstance(b, dict) and b.get('username') == username and not b.get('returned', False)]
    except Exception:
        return []

def get_user_borrowing_history(username):
    """Gibt die komplette Ausleih-Historie eines Benutzers zurueck."""
    try:
        borrowings = load_borrowings()
        if not isinstance(borrowings, list):
            return []
        return [b for b in borrowings if isinstance(b, dict) and b.get('username') == username]
    except Exception:
        return []

def get_overdue_borrowings():
    """Gibt alle ueberfaelligen Ausleihen zurueck."""
    try:
        borrowings = load_borrowings()
        if not isinstance(borrowings, list):
            return []
        overdue = []
        
        for b in borrowings:
            if not isinstance(b, dict) or b.get('returned', False):
                continue
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
        
        return overdue
    except Exception:
        return []

def get_user_favorite_genres(username):
    """Ermittelt die Lieblingsgenres eines Benutzers basierend auf der Ausleih-Historie."""
    try:
        books = load_books()
        borrowings = load_borrowings()
        
        # Sammle alle Genres aus der Historie
        genre_counts = {}
        for b in borrowings:
            if b.get('username') == username and b.get('returned', False):
                book_id = b.get('book_id')
                book = next((bk for bk in books if bk['id'] == book_id), None)
                if book:
                    genre = book.get('genre', 'Unbekannt')
                    genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        # Sortiere nach Häufigkeit
        sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
        return [g[0] for g in sorted_genres]
    except Exception:
        return []

def get_book_recommendations(username, limit=5):
    """Generiert Buchempfehlungen basierend auf dem Lieblingsgenre des Benutzers."""
    try:
        books = load_books()
        borrowings = load_borrowings()
        
        # Hole bevorzugte Genres
        favorite_genres = get_user_favorite_genres(username)
        if not favorite_genres:
            return []
        
        # IDs ALLER jemals vom User ausgeliehenen Bücher (inkl. returned)
        user_borrowed_ids = set()
        for b in borrowings:
            if b.get('username') == username:
                user_borrowed_ids.add(b.get('book_id'))
        
        # Sammle Empfehlungen nach Genre
        recommendations = []
        seen_titles = set()  # Prevent duplicate titles
        
        for genre in favorite_genres:
            for book in books:
                if book.get('genre') == genre:
                    key = (book['title'], book['author'], book['genre'])
                    if key in seen_titles:
                        continue
                    
                    # Prüfe ob der User dieses Buch schon mal ausgeliehen hatte
                    if book['id'] in user_borrowed_ids:
                        continue
                    
                    # Bücher mit available > 0 sind verfügbar
                    if book.get('available', 0) <= 0:
                        continue
                    
                    seen_titles.add(key)
                    recommendations.append({
                        'id': book['id'],
                        'title': book['title'],
                        'author': book['author'],
                        'genre': book['genre'],
                        'reason': f'Deinem Lieblingsgenre: {genre}'
                    })
                    if len(recommendations) >= limit:
                        return recommendations
        
        return recommendations[:limit]
    except Exception:
        return []
