#!/usr/bin/env bash
# Ende-zu-Ende-Test von auth.php?action=delete_account über HTTP gegen eine laufende API.
#
#   Datenbank und Server wie in web/README.md ("Lokal gegen echtes MariaDB testen"), dann:
#   web/tests/api_delete_account.sh http://127.0.0.1:8000
#
# Läuft nur gegen lokale Adressen. Legt Test-Konten an (del-test-*) und räumt sie selbst auf.
set -u
BASE="${1:-}"
case "$BASE" in
    http://127.0.0.1:*|http://localhost:*) ;;
    *) echo "Aufruf: $0 http://127.0.0.1:PORT  (nur lokale Adressen erlaubt)"; exit 2 ;;
esac
API="$BASE/api"
TMP=$(mktemp); JAR=$(mktemp); trap 'rm -f "$TMP" "$JAR"' EXIT
FAILED=0
RUN=$RANDOM
check() { if [ "$2" = "$3" ]; then echo "OK     $1"; else echo "FEHLER $1 (ist '$2', erwartet '$3')"; FAILED=$((FAILED + 1)); fi; }

# post <Datei?aktion> <IP> <json> [weitere curl-Argumente]  -> HTTP-Status; Antwort in $TMP
post() { local url="$1" ip="$2" data="$3"; shift 3; curl -s -o "$TMP" -w '%{http_code}' -X POST -H 'Content-Type: application/json' -H "X-Real-IP: $ip" -d "$data" "$@" "$API/$url"; }
body() { cat "$TMP"; }
count() { podman exec gtm-mariadb mariadb -uroot -ptestroot genshin-manager -N -e "$1" 2>/dev/null; }

U1="del-test-a-$RUN"; U2="del-test-b-$RUN"; U3="del-test-c-$RUN"
TEAM='{"format":"genshin-team-manager","version":1,"builds":[],"teams":[{"name":"T","members":[]}]}'

# --- Konto 1 (Token) ----------------------------------------------------------
check "Registrierung 1"                  "$(post 'auth.php?action=register' 198.51.100.1 "{\"username\":\"$U1\",\"password\":\"richtig1\"}")" 200
check "Token holen"                      "$(post 'auth.php?action=token' 198.51.100.1 "{\"username\":\"$U1\",\"password\":\"richtig1\"}")" 200
TOKEN=$(body | sed -E 's/.*"token":"([^"]+)".*/\1/')
AUTH=(-H "Authorization: Bearer $TOKEN")
check "Team anlegen"                     "$(post 'transfer.php' 198.51.100.1 "{\"mode\":\"merge\",\"data\":$TEAM}" "${AUTH[@]}")" 200
ID1=$(count "SELECT id FROM users WHERE username='$U1'")
check "Team in der Datenbank"            "$(count "SELECT COUNT(*) FROM teams WHERE user_id=$ID1")" 1

# --- Konto 2 (Session) bleibt unberührt ----------------------------------------
check "Registrierung 2 (Session)"        "$(post 'auth.php?action=register' 198.51.100.2 "{\"username\":\"$U2\",\"password\":\"richtig2\"}" -c "$JAR")" 200
check "Team von Konto 2"                 "$(post 'transfer.php' 198.51.100.2 "{\"mode\":\"merge\",\"data\":$TEAM}" -b "$JAR")" 200
ID2=$(count "SELECT id FROM users WHERE username='$U2'")

# --- Ablehnungen ---------------------------------------------------------------
check "GET ist nicht erlaubt"            "$(curl -s -o "$TMP" -w '%{http_code}' "${AUTH[@]}" "$API/auth.php?action=delete_account")" 405
check "ohne Anmeldung: 401"              "$(post 'auth.php?action=delete_account' 198.51.100.3 '{"password":"richtig1"}')" 401
check "falsches Passwort: 403 (nicht 401)" "$(post 'auth.php?action=delete_account' 198.51.100.1 '{"password":"falsch"}' "${AUTH[@]}")" 403
check "Meldung 'Passwort falsch'"        "$(body | grep -c 'Passwort falsch')" 1
check "leeres Passwort: 403"             "$(post 'auth.php?action=delete_account' 198.51.100.1 '{}' "${AUTH[@]}")" 403
check "Konto 1 besteht noch"             "$(count "SELECT COUNT(*) FROM users WHERE id=$ID1")" 1
check "Token gilt nach Fehlversuch weiter" "$(curl -s -o "$TMP" -w '%{http_code}' "${AUTH[@]}" "$API/teams.php")" 200
# Passwort von Konto 2 reicht nicht für Konto 1
check "fremdes Passwort wird abgelehnt"  "$(post 'auth.php?action=delete_account' 198.51.100.1 '{"password":"richtig2"}' "${AUTH[@]}")" 403

# --- Löschen -------------------------------------------------------------------
check "Löschen mit richtigem Passwort"   "$(post 'auth.php?action=delete_account' 198.51.100.1 '{"password":"richtig1"}' "${AUTH[@]}")" 200
check "Nutzer weg"                       "$(count "SELECT COUNT(*) FROM users WHERE id=$ID1")" 0
check "Teams weg"                        "$(count "SELECT COUNT(*) FROM teams WHERE user_id=$ID1")" 0
check "Teammitglieder ohne Team: keine Waisen" "$(count "SELECT COUNT(*) FROM team_members WHERE team_id NOT IN (SELECT id FROM teams)")" 0
check "Builds weg"                       "$(count "SELECT COUNT(*) FROM user_characters WHERE user_id=$ID1")" 0
check "Token weg"                        "$(count "SELECT COUNT(*) FROM api_tokens WHERE user_id=$ID1")" 0
check "alter Token ist ungültig (401)"   "$(curl -s -o "$TMP" -w '%{http_code}' "${AUTH[@]}" "$API/teams.php")" 401
check "Anmeldung mit altem Konto scheitert" "$(post 'auth.php?action=login' 198.51.100.1 "{\"username\":\"$U1\",\"password\":\"richtig1\"}")" 401
check "Name ist wieder frei"             "$(post 'auth.php?action=register' 198.51.100.1 "{\"username\":\"$U1\",\"password\":\"neu12345\"}")" 200

# --- Konto 2 unberührt, dann per Session löschen ---------------------------------
check "Konto 2 besteht noch"             "$(count "SELECT COUNT(*) FROM teams WHERE user_id=$ID2")" 1
check "Session-Löschung"                 "$(post 'auth.php?action=delete_account' 198.51.100.2 '{"password":"richtig2"}' -b "$JAR" -c "$JAR")" 200
check "Konto 2 weg"                      "$(count "SELECT COUNT(*) FROM users WHERE id=$ID2")" 0
check "Session danach abgemeldet"        "$(curl -s -b "$JAR" "$API/auth.php?action=status" | grep -c '"logged_in":false')" 1

# --- Begrenzung der Fehlversuche -------------------------------------------------
check "Registrierung 3"                  "$(post 'auth.php?action=register' 198.51.100.4 "{\"username\":\"$U3\",\"password\":\"richtig3\"}")" 200
check "Token 3"                          "$(post 'auth.php?action=token' 198.51.100.4 "{\"username\":\"$U3\",\"password\":\"richtig3\"}")" 200
T3=$(body | sed -E 's/.*"token":"([^"]+)".*/\1/')
for i in 1 2 3 4 5 6 7 8; do post 'auth.php?action=delete_account' 198.51.100.4 '{"password":"x"}' -H "Authorization: Bearer $T3" >/dev/null; done
check "nach 8 Fehlversuchen gesperrt (429)" "$(post 'auth.php?action=delete_account' 198.51.100.4 '{"password":"richtig3"}' -H "Authorization: Bearer $T3")" 429
check "Konto 3 trotz Sperre noch da"     "$(count "SELECT COUNT(*) FROM users WHERE username='$U3'")" 1

# Aufräumen
count "DELETE FROM users WHERE username LIKE 'del-test-%'; DELETE FROM auth_attempts;" >/dev/null
[ "$FAILED" = 0 ] && echo "ALLES OK" || { echo "$FAILED Fehler"; exit 1; }
