-- Schema der Web-Version (MySQL / MariaDB).
-- ACHTUNG: aus den Abfragen in api/*.php abgeleitet, nicht aus der Produktivdatenbank exportiert.
-- Vor dem Einsatz mit `SHOW CREATE TABLE` abgleichen. Spalten und Schlüssel, auf die der Code sich stützt,
-- sind enthalten; Typen und Längen sind Annahmen.
-- Für eine bestehende Datenbank sind nur die Dateien in migrations/ relevant.

CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Stammdaten (Inhalt: ../shared/stammdaten.json)
CREATE TABLE IF NOT EXISTS characters (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(255) NOT NULL UNIQUE,
    element     VARCHAR(50)  NOT NULL,
    weapon_type VARCHAR(50)  NOT NULL,
    region      VARCHAR(50)  NOT NULL,
    rarity      INT NOT NULL,
    icon_path   VARCHAR(255) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS weapons (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(255) NOT NULL UNIQUE,
    weapon_type VARCHAR(50)  NOT NULL,
    rarity      INT NOT NULL,
    icon_path   VARCHAR(255) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS artifacts (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    name      VARCHAR(255) NOT NULL UNIQUE,
    bonus_1pc TEXT,
    bonus_2pc TEXT,
    bonus_4pc TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Nutzerdaten
CREATE TABLE IF NOT EXISTS user_characters (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    user_id             INT NOT NULL,
    char_name           VARCHAR(255) NOT NULL,
    level               INT NOT NULL DEFAULT 90,
    constellation       INT NOT NULL DEFAULT 0,
    weapon              VARCHAR(255) NOT NULL DEFAULT '',
    weapon_level        INT NOT NULL DEFAULT 90,
    refinement          INT NOT NULL DEFAULT 1,
    artifact            VARCHAR(255) NOT NULL DEFAULT '',
    artifact_2          VARCHAR(255) NOT NULL DEFAULT '',
    talent_attack       INT NOT NULL DEFAULT 1,
    talent_skill        INT NOT NULL DEFAULT 1,
    talent_burst        INT NOT NULL DEFAULT 1,
    artifact_stats_json TEXT,
    UNIQUE KEY uq_user_char (user_id, char_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS teams (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name    VARCHAR(255) NOT NULL,
    position INT NOT NULL DEFAULT 0,
    UNIQUE KEY uq_user_team (user_id, name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS team_members (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    team_id    INT NOT NULL,
    char_name  VARCHAR(255) NOT NULL,
    slot_order INT NOT NULL,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Token-Login für Apps (siehe migrations/001_api_tokens.sql)
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

-- Begrenzung von Anmelde- und Registrierungsversuchen (siehe migrations/002_auth_attempts.sql)
CREATE TABLE IF NOT EXISTS auth_attempts (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    scope      VARCHAR(20) NOT NULL,
    subject    CHAR(64)    NOT NULL,
    created_at DATETIME    NOT NULL,
    KEY idx_auth_attempts_lookup (scope, subject, created_at),
    KEY idx_auth_attempts_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
