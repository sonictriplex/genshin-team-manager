-- Token-Login für Apps (z. B. Android): auth.php?action=token
-- Bestehende Datenbank: einmal ausführen. Es wird nur der SHA-256-Hash des Tokens gespeichert.
CREATE TABLE IF NOT EXISTS api_tokens (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT NOT NULL,
    token_hash   CHAR(64) NOT NULL,
    device       VARCHAR(100) NOT NULL DEFAULT '',
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used_at DATETIME NULL,
    expires_at   DATETIME NOT NULL,
    UNIQUE KEY uq_api_tokens_hash (token_hash),
    KEY idx_api_tokens_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
