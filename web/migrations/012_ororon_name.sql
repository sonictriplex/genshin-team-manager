-- Korrigiert den Charakternamen "Ororun" zu "Ororon" (Stammdaten und Spieler-Charaktere).
-- Einmal in phpMyAdmin ausführen; wiederholbar. UPDATE IGNORE lässt eine Zeile unverändert, falls "Ororon" dort schon existiert.
UPDATE IGNORE characters
   SET name = 'Ororon', icon_path = 'assets/images/characters/ororon.png'
 WHERE name = 'Ororun';
UPDATE IGNORE user_characters SET char_name = 'Ororon' WHERE char_name = 'Ororun';

-- Kontrolle: keine Zeile mit "Ororun" mehr (beide Abfragen leer)
SELECT id, name FROM characters WHERE name = 'Ororun';
SELECT id, char_name FROM user_characters WHERE char_name = 'Ororun';
