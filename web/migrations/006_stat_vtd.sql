-- Umbenennung der Stats DEF% / DEF (Fix) in VTD% / VTD (Fix) (Verteidigung) in den gespeicherten Builds.
-- Einmal ausführen. Auch ohne die Migration zeigen und speichern die Clients die neuen Namen:
-- teams.php und transfer.php wandeln die alten Namen beim Lesen und Speichern um.
UPDATE user_characters
SET artifact_stats_json = REPLACE(REPLACE(artifact_stats_json, '"DEF%"', '"VTD%"'), '"DEF (Fix)"', '"VTD (Fix)"')
WHERE artifact_stats_json LIKE '%DEF%';
