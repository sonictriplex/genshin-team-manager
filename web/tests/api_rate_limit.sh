#!/usr/bin/env bash
# Ende-zu-Ende-Test der Begrenzung von Anmeldungen und Registrierungen über HTTP gegen eine laufende API.
#
#   Datenbank und Server wie in web/README.md ("Lokal gegen echtes MariaDB testen"), dann:
#   web/tests/api_rate_limit.sh http://127.0.0.1:8000
#
# Läuft nur gegen lokale Adressen. Legt Test-Konten an (rl-test-*) und füllt auth_attempts der Datenbank.
# Der Server steht hinter keinem Proxy; die Client-IP wird wie bei nginx über X-Real-IP simuliert.
set -u
BASE="${1:-}"
case "$BASE" in
    http://127.0.0.1:*|http://localhost:*) ;;
    *) echo "Aufruf: $0 http://127.0.0.1:PORT  (nur lokale Adressen erlaubt)"; exit 2 ;;
esac
API="$BASE/api/auth.php"
TMP=$(mktemp); trap 'rm -f "$TMP" "$TMP.h"' EXIT
FAILED=0
RUN=$RANDOM
check() { if [ "$2" = "$3" ]; then echo "OK     $1"; else echo "FEHLER $1 (ist '$2', erwartet '$3')"; FAILED=$((FAILED + 1)); fi; }

# post <aktion> <ip> <json>  -> HTTP-Status; Antwort in $TMP, Header in $TMP.h
post() { curl -s -o "$TMP" -D "$TMP.h" -w '%{http_code}' -X POST -H 'Content-Type: application/json' -H "X-Real-IP: $2" -d "$3" "$API?action=$1"; }
body() { cat "$TMP"; }

U1="rl-test-a-$RUN"; U2="rl-test-b-$RUN"; GHOST="rl-test-gibtsnicht-$RUN"
IP1="198.51.100.10"; IP2="198.51.100.20"; IP3="198.51.100.30"

check "Registrierung (neues Konto)"                      "$(post register $IP1 "{\"username\":\"$U1\",\"password\":\"richtig1\"}")" 200
check "Registrierung (zweites Konto)"                    "$(post register $IP1 "{\"username\":\"$U2\",\"password\":\"richtig2\"}")" 200

echo "-- Anmeldung: 8 Fehlversuche je Benutzername"
for i in 1 2 3 4 5 6 7 8; do s=$(post login $IP1 "{\"username\":\"$U1\",\"password\":\"falsch$i\"}"); [ "$s" = 401 ] || { echo "Versuch $i: $s"; FAILED=$((FAILED + 1)); }; done
check "9. Versuch mit falschem Passwort ist gesperrt"      "$(post login $IP1 "{\"username\":\"$U1\",\"password\":\"falsch9\"}")" 429
check "Meldung nennt die Wartezeit"                        "$(body | grep -c 'Minuten')" 1
check "Retry-After-Header gesetzt (> 0)"                   "$(grep -i '^retry-after:' "$TMP.h" | tr -dc '0-9' | awk '{print ($1>0)?"ja":"nein"}')" ja
check "auch das RICHTIGE Passwort ist während der Sperre gesperrt" "$(post login $IP1 "{\"username\":\"$U1\",\"password\":\"richtig1\"}")" 429
check "Token-Anmeldung teilt die Sperre"                   "$(post token $IP1 "{\"username\":\"$U1\",\"password\":\"richtig1\"}")" 429
check "von anderer IP bleibt der Name trotzdem gesperrt"   "$(post login $IP2 "{\"username\":\"$U1\",\"password\":\"richtig1\"}")" 429
check "anderes Konto ist nicht betroffen"                  "$(post login $IP1 "{\"username\":\"$U2\",\"password\":\"richtig2\"}")" 200

echo "-- Unbekannter Benutzername verhält sich genauso (kein Erraten von Konten)"
for i in 1 2 3 4 5 6 7 8; do post login $IP3 "{\"username\":\"$GHOST\",\"password\":\"x$i\"}" >/dev/null; done
check "Unbekannter Name wird ebenfalls gesperrt"           "$(post login $IP3 "{\"username\":\"$GHOST\",\"password\":\"x9\"}")" 429

echo "-- Erfolg setzt den Zähler zurück"
for i in 1 2 3 4 5; do post login $IP2 "{\"username\":\"$U2\",\"password\":\"falsch$i\"}" >/dev/null; done
check "richtiges Passwort nach 5 Fehlversuchen geht"       "$(post login $IP2 "{\"username\":\"$U2\",\"password\":\"richtig2\"}")" 200
for i in 1 2 3 4 5 6 7; do post login $IP2 "{\"username\":\"$U2\",\"password\":\"falsch$i\"}" >/dev/null; done
check "danach sind wieder 7 Fehlversuche möglich (Zähler war zurückgesetzt)" "$(post login $IP2 "{\"username\":\"$U2\",\"password\":\"richtig2\"}")" 200

echo "-- Registrierung: 5 Versuche je IP und Stunde"
IPR="198.51.100.77"
for i in 1 2 3 4 5; do s=$(post register $IPR "{\"username\":\"rl-test-r$i-$RUN\",\"password\":\"richtig1\"}"); [ "$s" = 200 ] || { echo "Registrierung $i: $s"; FAILED=$((FAILED + 1)); }; done
check "6. Registrierung derselben IP ist gesperrt"         "$(post register $IPR "{\"username\":\"rl-test-r6-$RUN\",\"password\":\"richtig1\"}")" 429
check "Meldung nennt Registrierungen"                      "$(body | grep -c 'Registrierungen')" 1
check "andere IP darf registrieren"                        "$(post register 198.51.100.78 "{\"username\":\"rl-test-r7-$RUN\",\"password\":\"richtig1\"}")" 200
check "Eingabefehler (zu kurz) wird weiter geprüft"        "$(post register 198.51.100.79 '{"username":"ab","password":"richtig1"}')" 400

echo "-- Normaler Betrieb"
check "Anmeldestatus ohne Anmeldung bleibt erreichbar"     "$(curl -s -o /dev/null -w '%{http_code}' "$API?action=status")" 200
check "Stammdaten bleiben erreichbar"                      "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/api/characters.php")" 200

echo
if [ "$FAILED" -eq 0 ]; then echo "alle Tests bestanden"; else echo "$FAILED FEHLER"; fi
exit $((FAILED > 0))
