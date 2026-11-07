-- Begrenzung von Anmelde- und Registrierungsversuchen (api/rate_limit.php).
-- Bestehende Datenbank: einmal ausführen. Es werden nur SHA-256-Werte gespeichert; Zeilen löscht der Code nach 2 Stunden.
-- Fehlt die Tabelle, bleibt die Anmeldung trotzdem möglich (dann ohne Begrenzung).
CREATE TABLE IF NOT EXISTS auth_attempts (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    scope      VARCHAR(20) NOT NULL,
    subject    CHAR(64)    NOT NULL,
    created_at DATETIME    NOT NULL,
    KEY idx_auth_attempts_lookup (scope, subject, created_at),
    KEY idx_auth_attempts_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
