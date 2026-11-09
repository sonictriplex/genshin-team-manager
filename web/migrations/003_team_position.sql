-- Reihenfolge der Teams (Spalte teams.position, siehe teams.php und transfer.php).
-- Bestehende Datenbank: VOR dem Hochladen des neuen Codes einmal ausführen.
-- Bisher galt die Anlage-Reihenfolge (id); die Startwerte übernehmen sie.
ALTER TABLE teams ADD COLUMN position INT NOT NULL DEFAULT 0;
UPDATE teams SET position = id;
