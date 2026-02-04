# Import von Unittest-Framework, Mocking-Tools und den zu testenden Modulen
import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import json
from flask import Flask, session
import login
import admin

class TestLoginModule(unittest.TestCase):
    """Testklasse für das Login-Modul"""
    def setUp(self):
    # Für jede Testmethode wird eine neue Flask-App erstellt, das Secret gesetzt, die Login-Routen registriert und ein Test-Client erzeugt
        self.app = Flask(__name__)
        self.app.secret_key = "test"
        login.register_login_routes(self.app)
        self.client = self.app.test_client()

    @patch("src.login.USERS_FILE", "test_users.json")
    @patch("builtins.open", new_callable=mock_open, read_data='{}')
    def test_register_user(self, mock_file):
        """Testet die Registrierung eines neuen Benutzers"""
        with self.app.test_request_context("/register", method="POST", data={"username": "user1", "password": "pw"}):
        # Es wird ein POST-Request simuliert
            with patch("src.login.save_users") as mock_save:
                resp = self.app.view_functions["register"]() # Es wird geprüft, ob register aufgerufen wird
                mock_save.assert_called() # Es wird geprüft, ob save_users aufgerufen wurde
                self.assertIn("Benutzer erfolgreich angelegt", resp) # Es wird geprüft, ob die Antwort den Text "..erfolgreich.." enthält

    @patch("src.login.USERS_FILE", "test_users.json")
    @patch("builtins.open", new_callable=mock_open, read_data='{"user1": {"password": "hash", "must_change_pw": false}}') # User file enthält einen Benutzer
    @patch("src.login.check_password_hash", return_value=True) # Das Hashing gibt immer true zurück
    def test_login_success(self, mock_hash, mock_file):
        """Testst einen erfolgreichen Login"""
        with self.app.test_request_context("/login", method="POST", data={"username": "user1", "password": "pw"}): # Es wird ein POST-Request simuliert
            resp = self.app.view_functions["login"]() # Es wird geprüft, ob login aufgerufen wird
            self.assertIn("redirect", str(resp)) # Es wird geprüft, ob die Antwort einen Redirect enthält

    @patch("src.login.USERS_FILE", "test_users.json")
    @patch("builtins.open", new_callable=mock_open, read_data='{"user1": {"password": "hash", "must_change_pw": false}}') # User file enthält einen Benutzer
    @patch("src.login.check_password_hash", return_value=False) # Das Hashing gibt immer false zurück
    def test_login_fail(self, mock_hash, mock_file):
        """Testest einen fehlgeschlagenen Login"""
        with self.app.test_request_context("/login", method="POST", data={"username": "user1", "password": "wrong"}):  # Es wird ein POST-Request simuliert
            resp = self.app.view_functions["login"]() # Es wird geprüft, ob login aufgerufen wird
            self.assertIn("Benutzername oder Passwort falsch", resp)  # Es wird geprüft, ob die Antwort den Text "..falsch" enthält

    @patch("src.login.USERS_FILE", "test_users.json")
    @patch("builtins.open", new_callable=mock_open, read_data='{"user1": {"password": "hash", "must_change_pw": true}}') # User file enthält einen Benutzer
    def test_login_must_change_pw(self, mock_file):
        """Testet das Erzwingen einer Passwortänderung nach dem Login"""
        with self.app.test_request_context("/login", method="POST", data={"username": "user1", "password": "pw"}): # Es wird ein POST-Request mit neuem Passwort simuliert  
            with self.app.test_client() as c: # Es wird ein Test-Client erstellt
                with c.session_transaction() as sess: # Die Session wird geöffnet und der Benutzer entsprechend gesetzt
                    sess["user"] = "user1"
                    sess["must_change_pw"] = True
                resp = c.post("/login", data={"new_password": "pw2", "new_password2": "pw2"}) # Es wird geprüft, ob die Passwortänderung erfolgreich war
                self.assertIn("Passwort erfolgreich geändert".encode('utf-8'), resp.data) # Es wird geprüft, ob die Erfolgsmeldung im Response steht

class TestAdminModule(unittest.TestCase):
    """Testklasse für das Admin-Modul"""
    def setUp(self): # Für jede Testmethode wird eine neue Flask-App erstellt, das Secret gesetzt, und die Admin-Routen gesetzt
        self.app = Flask(__name__)
        self.app.secret_key = "test"
        admin.register_admin_routes(self.app)
        self.client = self.app.test_client()

    @patch("src.admin.USERS_FILE", "test_users.json")
    @patch("builtins.open", new_callable=mock_open, read_data='{}') # User file ist leer
    def test_admin_add(self, mock_file):
        """Testet das Hinzufügen eines neuen Benutzers durch den Admin"""
        with self.app.test_request_context("/admin/add", method="POST", data={"username": "user2", "password": "pw"}): # POST-Request zum Hinzufügen eines Users
            with patch("src.admin.save_users") as mock_save:
                with patch("src.admin.ADMIN_USER", "admin"):
                    with self.app.test_client() as c:
                        with c.session_transaction() as sess:
                            sess["user"] = "admin" # Der Admin-User wird in der Session gesetzt
                        resp = c.post("/admin/add", data={"username": "user2", "password": "pw"}) # Es wird geprüft, ob save_users aufgerufen wurde und die Erfolgsmeldung im Response steht
                        mock_save.assert_called() 
                        self.assertIn("User erfolgreich hinzugefügt".encode('utf-8'), resp.data)

    @patch("src.admin.USERS_FILE", "test_users.json")
    @patch("builtins.open", new_callable=mock_open, read_data='{"user2": {"password": "hash", "must_change_pw": false}}') # User file enthält einen Benutzer 
    def test_admin_delete(self, mock_file):
        """Testest das Löschen eines Benutzers durch den Admin"""
        with self.app.test_request_context("/admin/delete/user2", method="POST"): # POST-Request zum Löschen des Users 
            with patch("src.admin.save_users") as mock_save:
                with patch("src.admin.ADMIN_USER", "admin"):
                    with self.app.test_client() as c:
                        with c.session_transaction() as sess:
                            sess["user"] = "admin" # Der Admin-User wird in der Session gesetzt
                        resp = c.post("/admin/delete/user2") # Es wird geprüft, ob save_users aufgerufen wurde und die Löschmeldung im Response steht
                        mock_save.assert_called()  
                        self.assertIn("User erfolgreich gelöscht".encode('utf-8'), resp.data)

    @patch("src.admin.USERS_FILE", "test_users.json")
    @patch("builtins.open", new_callable=mock_open, read_data='{"user2": {"password": "hash", "must_change_pw": false}}') # User file enthält einen Benutzer
    def test_admin_reset(self, mock_file):
        """Testet das Zurücksetzen des Passworts eines Users durch den Admin """
        with self.app.test_request_context("/admin/reset/user2", method="POST"): # POST-Request zum Zurücksetzen des User-Passworts
            with patch("src.admin.save_users") as mock_save:
                with patch("src.admin.ADMIN_USER", "admin"):
                    with self.app.test_client() as c:
                        with c.session_transaction() as sess:
                            sess["user"] = "admin" #  Der Admin-User wird in der Session gesetzt
                        resp = c.post("/admin/reset/user2") # Es wird geprüft, ob save_users aufgerufen wurde und die Erfolgsmeldung im Response steht
                        mock_save.assert_called()
                        self.assertIn("Passwort erfolgreich zurückgesetzt".encode('utf-8'), resp.data)

    @patch("src.admin.USERS_FILE", "test_users.json")
    @patch("builtins.open", new_callable=mock_open, read_data='{"admin": {"password": "hash", "must_change_pw": false}}')
    def test_admin_cannot_delete_self(self, mock_file):
        """Testet, dass der Admin sich nicht selbst löschen kann"""
        with self.app.test_request_context("/admin/delete/admin", method="POST"): # POST-Request zum Löschen des Admin-Users
            with patch("src.admin.save_users") as mock_save:
                with patch("src.admin.ADMIN_USER", "admin"):
                    with self.app.test_client() as c:
                        with c.session_transaction() as sess:
                            sess["user"] = "admin"
                        resp = c.post("/admin/delete/admin") #Es wird geprüft, dass save_users nicht aufgerufen wurde und die entsprechende Fehlermeldung im Response steht
                        mock_save.assert_not_called()
                        self.assertIn("Admin-Benutzer kann nicht gelöscht werden".encode('utf-8'), resp.data)

if __name__ == "__main__":
    unittest.main()