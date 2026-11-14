-- Neue Charaktere (Varesa, Sigewinne, Escoffier) und Waffen (Urzeitliches Jadeschwert, Kunwus Drachenschlächter).
-- Einmal in phpMyAdmin ausführen; bereits vorhandene Namen werden übersprungen (INSERT IGNORE).
-- Die Bilder (assets/images/<name>.png) lädt deploy/deploy.sh hoch.
INSERT IGNORE INTO characters (name, element, weapon_type, region, rarity, icon_path) VALUES
  ('Varesa',    'Electro', 'Katalysator',  'Natlan',   5, 'assets/images/varesa.png'),
  ('Sigewinne', 'Hydro',   'Bogen',        'Fontaine', 5, 'assets/images/sigewinne.png'),
  ('Escoffier', 'Cryo',    'Stangenwaffe', 'Fontaine', 5, 'assets/images/escoffier.png');
-- Die Produktivtabelle weapons hat keine Spalte icon_path (das Bild wird über den Namen gefunden).
INSERT IGNORE INTO weapons (name, weapon_type, rarity, passive_json) VALUES
  ('Urzeitliches Jadeschwert', 'Großschwert', 5, NULL),
  ('Kunwus Drachenschlächter', 'Bogen',       5, NULL);
-- Kontrolle: 3 bzw. 2 Zeilen
SELECT name FROM characters WHERE name IN ('Varesa','Sigewinne','Escoffier');
SELECT name FROM weapons WHERE name IN ('Urzeitliches Jadeschwert','Kunwus Drachenschlächter');
