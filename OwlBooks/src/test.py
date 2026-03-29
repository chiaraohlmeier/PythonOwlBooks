# Import von Unittest-Framework, Mocking-Tools und den zu testenden Modulen
import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import json
import sys

# Füge src zum Pfad hinzu
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, session
import login
import admin

# Import borrowing module
try:
    from src import borrowing
except ImportError:
    import borrowing


class TestBorrowingModule(unittest.TestCase):
    """Testklasse für das Borrowing-Modul"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_books = [
            {"id": "1", "title": "Test Book 1", "author": "Author 1", "genre": "Fantasy", "total": 2, "available": 2},
            {"id": "2", "title": "Test Book 2", "author": "Author 2", "genre": "Science-Fiction", "total": 1, "available": 1},
            {"id": "3", "title": "Test Book 3", "author": "Author 3", "genre": "Fantasy", "total": 1, "available": 0}
        ]
        self.test_borrowings = []
    
    @patch('borrowing.BOOKS_FILE', 'test_books.json')
    @patch('borrowing.BORROWING_FILE', 'test_ausleihe.json')
    @patch('builtins.open', new_callable=mock_open, read_data='[]')
    def test_load_books_empty(self, mock_file):
        """Testet das Laden einer leeren Bücherliste"""
        books = borrowing.load_books()
        self.assertEqual(books, [])
    
    @patch('borrowing.BOOKS_FILE', 'test_books.json')
    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps([{"id": "1", "title": "Test", "author": "Author", "genre": "Fantasy", "total": 1, "available": 1}]))
    def test_load_books_with_data(self, mock_file):
        """Testet das Laden einer nicht-leeren Bücherliste"""
        books = borrowing.load_books()
        self.assertEqual(len(books), 1)
        self.assertEqual(books[0]["id"], "1")
        self.assertEqual(books[0]["title"], "Test")
    
    @patch('borrowing.BOOKS_FILE', 'test_books.json')
    @patch('borrowing.save_books')
    def test_borrow_book_success(self, mock_save):
        """Testet das erfolgreiche Ausleihen eines verfügbaren Buches"""
        with patch('borrowing.load_books', return_value=[
            {"id": "1", "title": "Test Book", "author": "Author", "genre": "Fantasy", "total": 1, "available": 1}
        ]):
            with patch('borrowing.load_borrowings', return_value=[]):
                with patch('borrowing.save_borrowings'):
                    success, message = borrowing.borrow_book("user1", "1", days=14)
                    self.assertTrue(success)
                    self.assertIn("erfolgreich ausgeliehen", message)
                    mock_save.assert_called()
    
    @patch('borrowing.BOOKS_FILE', 'test_books.json')
    @patch('borrowing.load_books')
    def test_borrow_book_not_found(self, mock_load):
        """Testet das Ausleihen eines nicht existierenden Buches"""
        mock_load.return_value = [
            {"id": "1", "title": "Test Book", "author": "Author", "genre": "Fantasy", "total": 1, "available": 1}
        ]
        success, message = borrowing.borrow_book("user1", "999", days=14)
        self.assertFalse(success)
        self.assertIn("nicht gefunden", message)
    
    @patch('borrowing.BOOKS_FILE', 'test_books.json')
    @patch('borrowing.load_books')
    def test_borrow_book_not_available(self, mock_load):
        """Testet das Ausleihen eines nicht verfügbaren Buches"""
        mock_load.return_value = [
            {"id": "1", "title": "Test Book", "author": "Author", "genre": "Fantasy", "total": 1, "available": 0}
        ]
        success, message = borrowing.borrow_book("user1", "1", days=14)
        self.assertFalse(success)
        self.assertIn("nicht verfuegbar", message)
    
    @patch('borrowing.BOOKS_FILE', 'test_books.json')
    @patch('borrowing.load_borrowings')
    @patch('borrowing.load_books')
    def test_return_book_success(self, mock_load_books, mock_load_borrowings):
        """Testet das erfolgreiche Zurückgeben eines Buches ohne Strafe"""
        mock_load_books.return_value = [
            {"id": "1", "title": "Test Book", "author": "Author", "genre": "Fantasy", "total": 1, "available": 0}
        ]
        # Use future return date to avoid fine
        from datetime import datetime, timedelta
        future_date = (datetime.now() + timedelta(days=7)).isoformat()
        mock_load_borrowings.return_value = [
            {"id": "1", "username": "user1", "book_id": "1", "book_title": "Test Book", 
             "borrow_date": "2024-01-01T10:00:00", "return_date": future_date, 
             "returned": False, "fine": 0.0}
        ]
        
        with patch('borrowing.save_borrowings') as mock_save_borrowings:
            with patch('borrowing.save_books') as mock_save_books:
                success, message = borrowing.return_book("1")
                self.assertTrue(success)
                self.assertIn("erfolgreich zurueckgegeben", message)
                mock_save_borrowings.assert_called()
                mock_save_books.assert_called()
    
    @patch('borrowing.load_borrowings')
    def test_return_book_not_found(self, mock_load):
        """Testet das Zurückgeben einer nicht existierenden Ausleihe"""
        mock_load.return_value = []
        success, message = borrowing.return_book("999")
        self.assertFalse(success)
        self.assertIn("nicht gefunden", message)
    
    @patch('borrowing.load_borrowings')
    def test_get_user_borrowings_empty(self, mock_load):
        """Testet das Abrufen der Ausleihen eines Benutzers ohne Ausleihen"""
        mock_load.return_value = []
        borrowings = borrowing.get_user_borrowings("user1")
        self.assertEqual(borrowings, [])
    
    @patch('borrowing.load_borrowings')
    def test_get_user_borrowings_with_data(self, mock_load):
        """Testet das Abrufen der Ausleihen eines Benutzers mit Ausleihen"""
        mock_load.return_value = [
            {"id": "1", "username": "user1", "book_id": "1", "book_title": "Test Book", "returned": False},
            {"id": "2", "username": "user1", "book_id": "2", "book_title": "Test Book 2", "returned": True},
            {"id": "3", "username": "user2", "book_id": "1", "book_title": "Test Book", "returned": False}
        ]
        borrowings = borrowing.get_user_borrowings("user1")
        self.assertEqual(len(borrowings), 1)  # Nur nicht zurückgegebene
        self.assertEqual(borrowings[0]["id"], "1")
    
    @patch('borrowing.load_borrowings')
    def test_get_user_borrowing_history(self, mock_load):
        """Testet das Abrufen der kompletten Ausleih-Historie"""
        mock_load.return_value = [
            {"id": "1", "username": "user1", "book_id": "1", "returned": False},
            {"id": "2", "username": "user1", "book_id": "2", "returned": True},
            {"id": "3", "username": "user2", "book_id": "1", "returned": False}
        ]
        history = borrowing.get_user_borrowing_history("user1")
        self.assertEqual(len(history), 2)  # Beide Ausleihen von user1
    
    @patch('borrowing.load_borrowings')
    def test_get_overdue_borrowings_none(self, mock_load):
        """Testet das Abrufen überfälliger Ausleihen wenn keine überfällig sind"""
        from datetime import datetime, timedelta
        future_date = (datetime.now() + timedelta(days=7)).isoformat()
        mock_load.return_value = [
            {"id": "1", "username": "user1", "book_id": "1", "return_date": future_date, "returned": False}
        ]
        overdue = borrowing.get_overdue_borrowings()
        self.assertEqual(len(overdue), 0)
    
    @patch('borrowing.load_borrowings')
    def test_get_overdue_borrowings_with_overdue(self, mock_load):
        """Testet das Abrufen überfälliger Ausleihen"""
        from datetime import datetime, timedelta
        past_date = (datetime.now() - timedelta(days=3)).isoformat()
        mock_load.return_value = [
            {"id": "1", "username": "user1", "book_id": "1", "return_date": past_date, "returned": False}
        ]
        overdue = borrowing.get_overdue_borrowings()
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0]["days_overdue"], 3)
        self.assertEqual(overdue[0]["fine"], 6.0)  # 3 days * 2 EUR
    
    @patch('borrowing.load_books')
    @patch('borrowing.load_borrowings')
    def test_get_book_recommendations_no_favorites(self, mock_borrowings, mock_books):
        """Testet Buchempfehlungen wenn der Benutzer keine Lieblingsgenres hat"""
        mock_books.return_value = [
            {"id": "1", "title": "Book 1", "author": "Author 1", "genre": "Fantasy", "available": 1},
            {"id": "2", "title": "Book 2", "author": "Author 2", "genre": "Sci-Fi", "available": 1}
        ]
        mock_borrowings.return_value = []  # Keine Ausleihen
        recommendations = borrowing.get_book_recommendations("user1", limit=5)
        self.assertEqual(recommendations, [])  # Keine Favoriten = keine Empfehlungen
    
    @patch('borrowing.load_books')
    @patch('borrowing.load_borrowings')
    def test_get_book_recommendations_with_favorites(self, mock_borrowings, mock_books):
        """Testet Buchempfehlungen mit Lieblingsgenres"""
        mock_books.return_value = [
            {"id": "1", "title": "Fantasy Book 1", "author": "Author 1", "genre": "Fantasy", "available": 1},
            {"id": "2", "title": "Sci-Fi Book", "author": "Author 2", "genre": "Science-Fiction", "available": 1},
            {"id": "3", "title": "Fantasy Book 2", "author": "Author 3", "genre": "Fantasy", "available": 1}
        ]
        # Benutzer hat Fantasy ausgeliehen und zurückgegeben
        mock_borrowings.return_value = [
            {"id": "1", "username": "user1", "book_id": "1", "returned": True}
        ]
        recommendations = borrowing.get_book_recommendations("user1", limit=5)
        # Fantasy ist Favorite, Book 1 already borrowed, Book 3 is available
        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0]["title"], "Fantasy Book 2")
    
    @patch('borrowing.load_books')
    @patch('borrowing.load_borrowings')
    def test_get_book_recommendations_excludes_borrowed(self, mock_borrowings, mock_books):
        """Testet dass bereits ausgeliehene Bücher nicht empfohlen werden"""
        mock_books.return_value = [
            {"id": "1", "title": "Fantasy Book 1", "author": "Author 1", "genre": "Fantasy", "available": 0},
            {"id": "2", "title": "Fantasy Book 2", "author": "Author 2", "genre": "Fantasy", "available": 1}
        ]
        # Benutzer hat beide Fantasy-Bücher ausgeliehen (eine zurück, eine nicht)
        mock_borrowings.return_value = [
            {"id": "1", "username": "user1", "book_id": "1", "returned": True},
            {"id": "2", "username": "user1", "book_id": "2", "returned": False}
        ]
        recommendations = borrowing.get_book_recommendations("user1", limit=5)
        # Keine Empfehlungen weil alle ausgeliehen
        self.assertEqual(len(recommendations), 0)


class TestBookQuantity(unittest.TestCase):
    """Testklasse für Bücher-Mengenverwaltung"""
    
    @patch('borrowing.BOOKS_FILE', 'test_books.json')
    @patch('borrowing.save_books')
    def test_borrow_decrements_available(self, mock_save):
        """Testet dass Ausleihen die verfügbare Anzahl verringert"""
        test_books = [
            {"id": "1", "title": "Test Book", "author": "Author", "genre": "Fantasy", "total": 3, "available": 3}
        ]
        with patch('borrowing.load_books', return_value=test_books):
            with patch('borrowing.load_borrowings', return_value=[]):
                with patch('borrowing.save_borrowings'):
                    borrowing.borrow_book("user1", "1", days=14)
                    # Prüfe dass available um 1 verringert wurde
                    saved_books = mock_save.call_args[0][0]
                    self.assertEqual(saved_books[0]["available"], 2)
    
    @patch('borrowing.BOOKS_FILE', 'test_books.json')
    @patch('borrowing.save_books')
    def test_return_increments_available(self, mock_save):
        """Testet dass Zurückgeben die verfügbare Anzahl erhöht"""
        test_books = [
            {"id": "1", "title": "Test Book", "author": "Author", "genre": "Fantasy", "total": 3, "available": 1}
        ]
        from datetime import datetime, timedelta
        future_date = (datetime.now() + timedelta(days=7)).isoformat()
        test_borrowings = [
            {"id": "1", "username": "user1", "book_id": "1", "book_title": "Test Book",
             "borrow_date": "2024-01-01T10:00:00", "return_date": future_date,
             "returned": False, "fine": 0.0}
        ]
        with patch('borrowing.load_books', return_value=test_books):
            with patch('borrowing.load_borrowings', return_value=test_borrowings):
                with patch('borrowing.save_borrowings'):
                    borrowing.return_book("1")
                    # Prüfe dass available um 1 erhöht wurde
                    saved_books = mock_save.call_args[0][0]
                    self.assertEqual(saved_books[0]["available"], 2)


class TestLoginModule(unittest.TestCase):
    """Testklasse für das Login-Modul"""
    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = "test"
        login.register_login_routes(self.app)
        self.client = self.app.test_client()

    @patch("login.USERS_FILE", "test_users.json")
    @patch("builtins.open", new_callable=mock_open, read_data='{}')
    def test_register_user(self, mock_file):
        """Testet die Registrierung eines neuen Benutzers"""
        with self.app.test_request_context("/register", method="POST", data={"username": "user1", "password": "pw"}):
            with patch("login.save_users") as mock_save:
                resp = self.app.view_functions["register"]()
                mock_save.assert_called()

    @patch("login.USERS_FILE", "test_users.json")
    @patch("builtins.open", new_callable=mock_open, read_data='{"user1": {"password": "hash", "must_change_pw": false}}')
    @patch("login.check_password_hash", return_value=True)
    def test_login_success(self, mock_hash, mock_file):
        """Testet einen erfolgreichen Login"""
        with self.app.test_request_context("/login", method="POST", data={"username": "user1", "password": "pw"}):
            resp = self.app.view_functions["login"]()
            self.assertIn("redirect", str(resp))

    @patch("login.USERS_FILE", "test_users.json")
    @patch("builtins.open", new_callable=mock_open, read_data='{"user1": {"password": "hash", "must_change_pw": false}}')
    @patch("login.check_password_hash", return_value=False)
    def test_login_fail(self, mock_hash, mock_file):
        """Testet einen fehlgeschlagenen Login"""
        with self.app.test_request_context("/login", method="POST", data={"username": "user1", "password": "wrong"}):
            resp = self.app.view_functions["login"]()
            self.assertIn("falsch", str(resp))

    @patch("login.USERS_FILE", "test_users.json")
    @patch("builtins.open", new_callable=mock_open, read_data='{"user1": {"password": "hash", "must_change_pw": true}}')
    def test_login_must_change_pw(self, mock_file):
        """Testet das Erzwingen einer Passwortänderung nach dem Login"""
        with self.app.test_request_context("/login", method="POST", data={"username": "user1", "password": "pw"}):
            with self.app.test_client() as c:
                with c.session_transaction() as sess:
                    sess["user"] = "user1"
                    sess["must_change_pw"] = True
                resp = c.post("/login", data={"new_password": "pw2", "new_password2": "pw2"})
                self.assertIn("erfolgreich geändert".encode('utf-8'), resp.data)


class TestAdminModule(unittest.TestCase):
    """Testklasse für das Admin-Modul"""
    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = "test"
        admin.register_admin_routes(self.app)
        self.client = self.app.test_client()

    @patch("admin.USERS_FILE", "test_users.json")
    @patch("builtins.open", new_callable=mock_open, read_data='{}')
    def test_admin_add(self, mock_file):
        """Testet das Hinzufügen eines neuen Benutzers durch den Admin"""
        with self.app.test_request_context("/admin/add", method="POST", data={"username": "user2", "password": "pw"}):
            with patch("admin.save_users") as mock_save:
                with patch("admin.ADMIN_USER", "admin"):
                    with self.app.test_client() as c:
                        with c.session_transaction() as sess:
                            sess["user"] = "admin"
                        resp = c.post("/admin/add", data={"username": "user2", "password": "pw"})
                        mock_save.assert_called()

    @patch("admin.USERS_FILE", "test_users.json")
    @patch("builtins.open", new_callable=mock_open, read_data='{"user2": {"password": "hash", "must_change_pw": false}}')
    def test_admin_delete(self, mock_file):
        """Testet das Löschen eines Benutzers durch den Admin"""
        with self.app.test_request_context("/admin/delete/user2", method="POST"):
            with patch("admin.save_users") as mock_save:
                with patch("admin.ADMIN_USER", "admin"):
                    with self.app.test_client() as c:
                        with c.session_transaction() as sess:
                            sess["user"] = "admin"
                        resp = c.post("/admin/delete/user2")
                        mock_save.assert_called()

    @patch("admin.USERS_FILE", "test_users.json")
    @patch("builtins.open", new_callable=mock_open, read_data='{"user2": {"password": "hash", "must_change_pw": false}}')
    def test_admin_reset(self, mock_file):
        """Testet das Zurücksetzen des Passworts eines Users durch den Admin"""
        with self.app.test_request_context("/admin/reset/user2", method="POST"):
            with patch("admin.save_users") as mock_save:
                with patch("admin.ADMIN_USER", "admin"):
                    with self.app.test_client() as c:
                        with c.session_transaction() as sess:
                            sess["user"] = "admin"
                        resp = c.post("/admin/reset/user2")
                        mock_save.assert_called()

    @patch("admin.USERS_FILE", "test_users.json")
    @patch("builtins.open", new_callable=mock_open, read_data='{"admin": {"password": "hash", "must_change_pw": false}}')
    def test_admin_cannot_delete_self(self, mock_file):
        """Testet, dass der Admin sich nicht selbst löschen kann"""
        with self.app.test_request_context("/admin/delete/admin", method="POST"):
            with patch("admin.save_users") as mock_save:
                with patch("admin.ADMIN_USER", "admin"):
                    with self.app.test_client() as c:
                        with c.session_transaction() as sess:
                            sess["user"] = "admin"
                        resp = c.post("/admin/delete/admin")
                        mock_save.assert_not_called()


if __name__ == "__main__":
    unittest.main()