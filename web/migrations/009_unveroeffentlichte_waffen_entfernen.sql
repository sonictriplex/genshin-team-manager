-- Entfernt zwei Waffen, die nie erschienen sind (Test-Einträge aus den Spieldaten, siehe Migration 007).
-- Vorher geprüft: kein Build (user_characters.weapon) verwendet sie.
DELETE FROM weapons WHERE name IN ('Urzeitliches Jadeschwert', 'Kunwus Drachenschlächter')
  AND NOT EXISTS (SELECT 1 FROM user_characters WHERE weapon IN ('Urzeitliches Jadeschwert', 'Kunwus Drachenschlächter'));
