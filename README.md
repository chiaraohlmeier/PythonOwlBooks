## OwlBooks - Die Bibliothek der weisen Eule

**Projekt für:** Software-Engineering Kurs  
**Version:** 1.0  
**Status:** Abgeschlossen

---

### Inhaltsverzeichnis
1. [Projektbeschreibung](#projektbeschreibung)
2. [Funktionaler Umfang](#funktionaler-umfang)
3. [Technische Umsetzung](#technische-umsetzung)
4. [Installation & Verwendung](#installation--verwendung)
5. [Anmeldedaten](#anmeldedaten)
6. [Projektstruktur](#projektstruktur)
7. [Funktionen im Detail](#funktionen-im-detail)
8. [Datenmodell](#datenmodell)
9. [Unit Tests](#unit-tests)
10. [Bekannte Limitations & TODOs](#bekannte-limitations--todos)

---

### Projektbeschreibung
OwlBooks ist eine Web-basierte Bibliotheksverwaltung, die mit Python und Flask entwickelt wurde. Die Anwendung ermöglicht die Verwaltung einer Bibliothek mit Ausleihfunktionen, Mahnwesen und personalisierten Buchempfehlungen.

## Funktionaler Umfang

### 1. Buchverwaltung ✅ IMPLEMENTIERT
- Erfassung und Verwaltung von Büchern mit folgenden Attributen:
  - Titel
  - Autor
  - Genre
  - Verfügbarkeitsstatus (total/available für Mengenverwaltung)
- Hinzufügen und Entfernen von Buchdaten im Admin-Bereich
- Übersicht aller Bücher auf der Startseite mit Paginierung (10 Bücher pro Seite)

### 2. Ausleihen und Rückgaben ✅ IMPLEMENTIERT
- Verwaltung von Ausleihvorgängen
- Zuordnung ausgeliehener Bücher zu Nutzern
- Rückgabe von Büchern mit automatischer Aktualisierung des Verfügbarkeitsstatus
- Berücksichtigung von Leihfristen (14, 21 oder 28 Tage)
- Benutzer sehen ihre eigenen Ausleihen auf der Startseite
- Admin sieht alle Ausleihen im Ausleihen-Bereich

### 3. Mahnwesen ✅ IMPLEMENTIERT
- Erkennung überfälliger Ausleihen
- Automatische Berechnung von Mahngebühren (2€ pro Tag Verzug)
- Überfällige Ausleihen werden in rot markiert
- Admin-Übersicht der überfälligen Ausleihen

### 4. Buchempfehlungen ✅ IMPLEMENTIERT
- Generierung von Buchempfehlungen auf Basis:
  - bevorzugter Genres (basierend auf Ausleih-Historie)
  - bisheriger Ausleihen
- Empfehlungen werden auf der Startseite angezeigt

### 5. Statistiken und Auswertungen im Adminbereich ✅ IMPLEMENTIERT
- Analyse und Ausgabe von Statistiken:
  - meist ausgeliehene Bücher
  - aktivste Nutzer
  - beliebteste Genres
  - durchschnittliche Ausleihdauer
  - Anzahl der Mahnungen pro Nutzer
  - Gesamte Mahngebühren

### 6. Finanzverwaltung im Adminbereich ✅ IMPLEMENTIERT
- Anzeige ausstehender Mahngebühren pro Benutzer
- Anzeige monatlicher Einnahmen (Mitgliedsbeiträge + Mahngebühren)
- Automatische Berechnung der Gebühren bei überfälligen Ausleihen
- Übersicht der Gesamteinnahmen im Admin-Dashboard

## Technische Umsetzung
- Programmiersprache: Python 3
- Weboberfläche mit Flask
- Benutzerverwaltung mit Login/Logout über die Weboberfläche
- Benutzer werden mit gehashtem Passwort in einer JSON-Datei gespeichert
- Verwendung grundlegender Programmierkonzepte:
  - Objektorientierte Programmierung
  - Datenstrukturen (Listen, Dictionaries)
  - Datums- und Zeitverarbeitung

## Installation & Verwendung

### Voraussetzungen
- Python 3.8+
- Flask
- Werkzeug (für Password Hashing)

### Installation
```bash
pip install flask werkzeug
```

### Start der Anwendung
```bash
cd OwlBooks
python src/OwlBooks.py
```

Die Anwendung läuft dann unter: **http://localhost:5000**

### Starten der Unit Tests
```bash
cd OwlBooks
python src/test.py
```

### Ausführbare Funktionen
| Funktion | Datei | Beschreibung |
|----------|-------|--------------|
| Web-Anwendung starten | `src/OwlBooks.py` | Startet den Flask-Server auf Port 5000 |
| Unit Tests ausführen | `src/test.py` | Führt alle Unit-Tests aus |
| Benutzer-Login/Registrierung | `src/login.py` | Login, Registrierung, Logout Routen |
| Admin-Verwaltung | `src/admin.py` | Benutzer, Bücher, Ausleihen verwalten |
| Ausleih-Logik | `src/borrowing.py` | Ausleihen, Zurückgeben, Empfehlungen |

## Anmeldedaten

### Admin-Benutzer
- **Benutzername:** `admin`
- **Passwort:** `admin_pass`
- **Zugriff:** Vollständige Verwaltung von Benutzern, Büchern und Ausleihen

### Standard-Test-Benutzer
- **Benutzername:** `Test`
- **Passwort:** `Test`
- **Zugriff:** Normale Benutzer-Funktionen (Bücher ausleihen, eigene Ausleihen verwalten)

### Neue Benutzer
Neue Benutzer können sich über die Registrierungs-Seite selbst anmelden.

## Projektstruktur

```
OwlBooks/
├── src/
│   ├── OwlBooks.py           # Haupt-Flask-App & Routen (STARTEN HIER)
│   ├── login.py              # Login/Register/Logout-Routen
│   ├── admin.py              # Admin-Routen (Benutzer, Bücher, Ausleihen, Statistiken)
│   ├── borrowing.py          # Ausleih-/Rückgabe-Logik & Empfehlungen
│   ├── genres.json           # Genre-Liste
│   ├── books.json            # Bücher-Datenbank (100 Bücher)
│   ├── users.json            # Benutzer-Datenbank (gehashte Passwörter)
│   ├── ausleihe.json         # Ausleih-Verlauf
│   ├── statistik.json        # Statistik-Daten
│   └── test.py               # Unit Tests
├── templates/
│   ├── index.html                 # Startseite (Meine Ausleihen, Empfehlungen, Buchbestand)
│   ├── login.html                 # Login-Seite
│   ├── register.html              # Registrierungs-Seite
│   ├── profile.html               # Benutzer-Profil
│   ├── history.html               # Ausleih-Historie
│   ├── admin.html                 # Admin-Dashboard
│   ├── admin_books.html           # Admin-Bücher-Verwaltung
│   ├── admin_books_edit.html      # Admin-Bücher-Bearbeitung
│   ├── admin_borrowings.html      # Admin-Ausleihe-Verwaltung
│   ├── admin_statistics.html      # Admin-Statistiken
│   ├── admin_statistics_books.html # Statistiken zu Büchern
│   └── admin_statistics_genres.html # Statistiken zu Genres
├── static/
│   ├── Icons/                      # Icons (Passwort-Sichtbarkeit Toggle)
│   │   ├── eye-password-hide.svg
│   │   └── eye-password-show.svg
│   └── js/
│       └── password.js             # Passwort-Sichtbarkeit Toggle
└── README.md
```

## Funktionen im Detail

### Für normale Benutzer
1. **Login/Registrierung:** Benutzer können sich anmelden oder registrieren
2. **Meine Ausleihen:** Übersicht eigener Ausleihen mit Fristen und Status
3. **Buchempfehlungen:** Personalisierte Empfehlungen basierend auf Lieblingsgenres
4. **Bücher durchsuchen:** Verfügbare Bücher sehen und ausleihen mit Suchfiltern
5. **Buch zurückgeben:** Ausgeliehene Bücher zurückgeben
6. **Profil:** Persönliche Daten und Gebühren einsehen
7. **Historie:** Komplette Ausleih-Historie einsehen

### Für Administratoren
1. **Benutzerverwaltung:** Benutzer hinzufügen, löschen, Passwort zurücksetzen
2. **Buchverwaltung:** Neue Bücher hinzufügen, existierende Bücher bearbeiten/löschen
3. **Ausleihe-Überwachung:** Alle aktiven, überfälligen und rückgegebenen Ausleihen einsehen
4. **Mahnung-Management:** Überfällige Ausleihen mit Gebühren verwalten
5. **Statistiken:** Einsehen von Ausleih-Statistiken, meistgeliehene Bücher, Top-Nutzer
6. **Reset-Funktion:** Mahngebühren und Ausleihen für alle oder einzelne Benutzer zurücksetzen

## Datenmodell

### Bücher (books.json)
```json
{
  "id": "string",
  "title": "string",
  "author": "string",
  "genre": "string",
  "total": "integer (Anzahl Exemplare)",
  "available": "integer (aktuell verfügbare Exemplare)"
}
```

### Benutzer (users.json)
```json
{
  "username": {
    "password": "string (gehasht)",
    "must_change_pw": "boolean",
    "outstanding_fines": "float",
    "fines_reset_date": "string (ISO datum)",
    "monthly_fee": "float",
    "full_name": "string",
    "address": "string"
  }
}
```

### Ausleihen (ausleihe.json)
```json
{
  "id": "string",
  "username": "string",
  "book_id": "string",
  "book_title": "string",
  "borrow_date": "string (ISO datum)",
  "return_date": "string (ISO datum)",
  "returned": "boolean",
  "fine": "float (Mahngebühr)",
  "actual_return_date": "string (ISO datum, optional)"
}
```

### Genres (genres.json)
```json
{
  "genres": ["string", "string", ...]
}
```

## Unit Tests

Das Projekt enthält umfassende Unit Tests in `src/test.py`. Diese decken folgende Module ab:

### TestBorrowingModule (17 Tests)
- `test_load_books_empty` - Laden einer leeren Bücherliste
- `test_load_books_with_data` - Laden einer nicht-leeren Bücherliste
- `test_borrow_book_success` - Erfolgreiches Ausleihen
- `test_borrow_book_not_found` - Ausleihen eines nicht existierenden Buches
- `test_borrow_book_not_available` - Ausleihen eines nicht verfügbaren Buches
- `test_return_book_success` - Erfolgreiches Zurückgeben
- `test_return_book_not_found` - Zurückgeben einer nicht existierenden Ausleihe
- `test_get_user_borrowings_empty` - Abrufen ohne Ausleihen
- `test_get_user_borrowings_with_data` - Abrufen mit Ausleihen
- `test_get_user_borrowing_history` - Komplette Historie abrufen
- `test_get_overdue_borrowings_none` - Keine überfälligen Ausleihen
- `test_get_overdue_borrowings_with_overdue` - Überfällige Ausleihen vorhanden
- `test_get_book_recommendations_no_favorites` - Keine Lieblingsgenres
- `test_get_book_recommendations_with_favorites` - Mit Lieblingsgenres
- `test_get_book_recommendations_excludes_borrowed` - Bereits ausgeliehene ausschließen
- `test_borrow_decrements_available` - Ausleihen verringert verfügbare Anzahl
- `test_return_increments_available` - Zurückgeben erhöht verfügbare Anzahl

### TestLoginModule (4 Tests)
- `test_register_user` - Registrierung eines neuen Benutzers
- `test_login_success` - Erfolgreicher Login
- `test_login_fail` - Fehlgeschlagener Login
- `test_login_must_change_pw` - Passwortänderung erzwingen

### TestAdminModule (4 Tests)
- `test_admin_add` - Hinzufügen eines neuen Benutzers
- `test_admin_delete` - Löschen eines Benutzers
- `test_admin_reset` - Zurücksetzen des Passworts
- `test_admin_cannot_delete_self` - Admin kann sich nicht selbst löschen

**Test ausführen:**
```bash
cd OwlBooks
python src/test.py
```

**Aktuelle Test-Ergebnisse:** 25/25 Tests bestanden (100%)

## Bekannte Limitations & TODOs
- Keine E-Mail-Benachrichtigungen für Mahnungen
- Keine Bild-Uploads für Bücher
- Keine Export-Funktion für Berichte
