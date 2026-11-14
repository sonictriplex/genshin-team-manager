-- Erzeugt von tools/update_stammdaten.py. Einmal in phpMyAdmin ausführen (INSERT IGNORE, wiederholbar).
-- Passiv-Texte der Waffen stammen aus genshin-db (deutsch).
INSERT IGNORE INTO characters (name, element, weapon_type, region, rarity, icon_path) VALUES
  ('Nicole', 'Pyro', 'Katalysator', 'Snezhnaya', 5, 'assets/images/nicole.png'),
  ('Skirk', 'Cryo', 'Einhandschwert', 'Snezhnaya', 5, 'assets/images/skirk.png'),
  ('Zibai', 'Geo', 'Einhandschwert', 'Liyue', 5, 'assets/images/zibai.png');
