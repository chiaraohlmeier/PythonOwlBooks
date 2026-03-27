## Funktionaler Umfang

### 1. Buchverwaltung
- Erfassung und Verwaltung von Büchern mit folgenden Attributen:
  - Titel
  - Autor
  - Genre
  - Verfügbarkeitsstatus
- Hinzufügen, Entfernen und Aktualisieren von Buchdaten

### 2. Ausleihen und Rückgaben
- Verwaltung von Ausleihvorgängen
- Zuordnung ausgeliehener Bücher zu Nutzern
- Rückgabe von Büchern mit automatischer Aktualisierung des Verfügbarkeitsstatus
- Berücksichtigung von Leihfristen

### 3. Mahnwesen
- Erkennung überfälliger Ausleihen
- Erstellung von Mahnungen bei Überschreitung der Leihfrist
- Berechnung optionaler Mahngebühren

### 4. Finanzverwaltung im Adminbereich
- Erfassung von Einnahmen:
  - Mitgliedsbeiträge
  - Mahngebühren
- Erfassung von Ausgaben:
  - Neuanschaffung von Büchern
  - Reparaturen
- Berechnung von Gewinn und Verlust

### 5. Buchempfehlungen
- Generierung von Buchempfehlungen auf Basis:
  - bevorzugter Genres
  - bisheriger Ausleihen
- Einsatz einfacher regelbasierter Empfehlungssysteme

### 6. Statistiken und Auswertungen im Adminbereich
- Analyse und Ausgabe von Statistiken, z. B.:
  - meist ausgeliehene Bücher
  - aktivste Nutzer
  - beliebteste Genres
  - durchschnittliche Ausleihdauer
  - Anzahl der Mahnungen pro Nutzer

## Technische Umsetzung
- Programmiersprache: Python 3
- Weboberfläche mit Flask
- Benutzerverwaltung mit Login/Logout über die Weboberfläche
- Benutzer werden mit gehashtem Passwort in einer JSON-Datei gespeichert
- Verwendung grundlegender Programmierkonzepte:
  - Objektorientierte Programmierung
  - Datenstrukturen (Listen, Dictionaries)
  - Datums- und Zeitverarbeitung