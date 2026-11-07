<?php
// Tests für api/rate_limit.php (Begrenzung von Anmelde- und Registrierungsversuchen), direkt gegen eine echte Datenbank.
//
// Start (Datenbank wie in web/README.md "Lokal gegen echtes MariaDB testen"):
//   DB_HOST=127.0.0.1 DB_NAME=genshin-manager DB_USER=root DB_PASS=testroot \
//     php -d extension=pdo_mysql web/tests/rate_limit_test.php
//
// ACHTUNG: leert die Tabelle auth_attempts der angegebenen Datenbank. Nie gegen die Produktivdatenbank starten.

require_once __DIR__ . '/../api/rate_limit.php';

foreach (['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASS'] as $name) {
    if (getenv($name) === false) { fwrite(STDERR, "Umgebungsvariable $name fehlt\n"); exit(2); }
}
if (!in_array(getenv('DB_HOST'), ['127.0.0.1', 'localhost'], true)) {
    fwrite(STDERR, "Abbruch: Der Test läuft nur gegen eine lokale Datenbank (DB_HOST=127.0.0.1)\n"); exit(2);
}

$pdo = new PDO('mysql:host=' . getenv('DB_HOST') . ';dbname=' . getenv('DB_NAME') . ';charset=utf8mb4', getenv('DB_USER'), getenv('DB_PASS'), [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
]);
$pdo->exec(file_get_contents(__DIR__ . '/../migrations/002_auth_attempts.sql'));
$pdo->exec('TRUNCATE TABLE auth_attempts');

$failed = 0;
function check(string $name, $got, $want): void {
    global $failed;
    $ok = $got === $want;
    if (!$ok) $failed++;
    printf("%s %s%s\n", $ok ? 'OK    ' : 'FEHLER', $name, $ok ? '' : ' (ist ' . var_export($got, true) . ', erwartet ' . var_export($want, true) . ')');
}
function setClient(string $remote, array $headers = []): void {
    unset($_SERVER['HTTP_X_REAL_IP'], $_SERVER['HTTP_X_FORWARDED_FOR']);
    $_SERVER['REMOTE_ADDR'] = $remote;
    foreach ($headers as $k => $v) $_SERVER[$k] = $v;
}
function reset_attempts(PDO $pdo): void { $pdo->exec('TRUNCATE TABLE auth_attempts'); }
function age(PDO $pdo, int $seconds): void { $pdo->exec("UPDATE auth_attempts SET created_at = created_at - INTERVAL $seconds SECOND"); }

// ---------------------------------------------------------------- Client-IP
setClient('203.0.113.7');
check('öffentliche Adresse wird verwendet', rl_client_ip(), '203.0.113.7');
setClient('203.0.113.7', ['HTTP_X_REAL_IP' => '198.51.100.9']);
check('Header werden bei öffentlicher Verbindung ignoriert (nicht fälschbar)', rl_client_ip(), '203.0.113.7');
setClient('127.0.0.1', ['HTTP_X_REAL_IP' => '198.51.100.9']);
check('hinter dem eigenen Proxy gilt X-Real-IP', rl_client_ip(), '198.51.100.9');
setClient('10.1.2.3', ['HTTP_X_FORWARDED_FOR' => '198.51.100.9, 10.1.2.3']);
check('hinter einem privaten Proxy gilt das erste X-Forwarded-For', rl_client_ip(), '198.51.100.9');
setClient('127.0.0.1', ['HTTP_X_REAL_IP' => 'kein-ip']);
check('ungültiger Header: Client nicht bestimmbar', rl_client_ip(), '');
setClient('127.0.0.1');
check('Proxy ohne Header: Client nicht bestimmbar', rl_client_ip(), '');

// ---------------------------------------------------------------- Anmeldung: je Benutzername
setClient('203.0.113.7');
for ($i = 1; $i <= RL_LOGIN_MAX_PER_USER - 1; $i++) rl_login_failed($pdo, 'jens');
check(RL_LOGIN_MAX_PER_USER - 1 . ' Fehlversuche: noch frei', rl_login_wait($pdo, 'jens'), 0);
rl_login_failed($pdo, 'jens');
$wait = rl_login_wait($pdo, 'jens');
check('beim Limit gesperrt', $wait > 0 && $wait <= RL_LOGIN_WINDOW, true);
check('Name ohne Beachtung von Groß-/Kleinschreibung und Leerzeichen', rl_login_wait($pdo, '  JENS ') > 0, true);
check('anderer Benutzername von anderer IP bleibt frei', (function () use ($pdo) { setClient('198.51.100.1'); return rl_login_wait($pdo, 'anna'); })(), 0);

// Wartezeit entspricht dem Alter des ältesten Eintrags
reset_attempts($pdo); setClient('203.0.113.7');
for ($i = 0; $i < RL_LOGIN_MAX_PER_USER; $i++) rl_login_failed($pdo, 'jens');
age($pdo, 600);
$wait = rl_login_wait($pdo, 'jens');
check('Wartezeit sinkt mit dem Alter der Einträge (ca. 300 s)', $wait >= 295 && $wait <= 300, true);
age($pdo, RL_LOGIN_WINDOW);
check('nach Ablauf des Fensters wieder frei', rl_login_wait($pdo, 'jens'), 0);

// Erfolg setzt den Zähler des Namens zurück
reset_attempts($pdo); setClient('203.0.113.7');
for ($i = 0; $i < RL_LOGIN_MAX_PER_USER; $i++) rl_login_failed($pdo, 'jens');
check('gesperrt vor dem Zurücksetzen', rl_login_wait($pdo, 'jens') > 0, true);
rl_login_succeeded($pdo, 'jens');
check('erfolgreiche Anmeldung hebt die Sperre des Namens auf', rl_login_wait($pdo, 'jens'), 0);

// ---------------------------------------------------------------- Anmeldung: je IP
reset_attempts($pdo); setClient('203.0.113.7');
for ($i = 1; $i <= RL_LOGIN_MAX_PER_IP; $i++) rl_login_failed($pdo, "nutzer$i");   // jeweils ein anderer Name
check('viele Namen von derselben IP: neuer Name gesperrt', rl_login_wait($pdo, 'frischer-name') > 0, true);
setClient('198.51.100.1');
check('andere IP bleibt frei', rl_login_wait($pdo, 'frischer-name'), 0);

// Nicht bestimmbarer Client: keine IP-Sperre, aber die je Name gilt
reset_attempts($pdo); setClient('127.0.0.1');
for ($i = 1; $i <= RL_LOGIN_MAX_PER_IP + 5; $i++) rl_login_failed($pdo, "nutzer$i");
check('ohne bestimmbare IP wird nicht nach IP gesperrt (sonst träfe es alle)', rl_login_wait($pdo, 'frischer-name'), 0);
for ($i = 0; $i < RL_LOGIN_MAX_PER_USER; $i++) rl_login_failed($pdo, 'jens');
check('die Sperre je Benutzername greift trotzdem', rl_login_wait($pdo, 'jens') > 0, true);

// ---------------------------------------------------------------- Registrierung
reset_attempts($pdo); setClient('203.0.113.7');
for ($i = 1; $i <= RL_REGISTER_MAX_PER_IP; $i++) check("Registrierungsversuch $i erlaubt", rl_register_attempt($pdo), 0);
check('weiterer Versuch von derselben IP gesperrt', rl_register_attempt($pdo) > 0, true);
$count = (int)$pdo->query("SELECT COUNT(*) FROM auth_attempts WHERE scope = 'register_ip'")->fetchColumn();
check('gesperrte Versuche werden nicht mitgezählt', $count, RL_REGISTER_MAX_PER_IP);
setClient('198.51.100.1');
check('andere IP darf registrieren', rl_register_attempt($pdo), 0);
age($pdo, RL_REGISTER_WINDOW);
setClient('203.0.113.7');
check('nach einer Stunde wieder erlaubt', rl_register_attempt($pdo), 0);

reset_attempts($pdo); setClient('203.0.113.7');
$stmt = $pdo->prepare("INSERT INTO auth_attempts (scope, subject, created_at) VALUES ('register_all', ?, NOW())");
for ($i = 0; $i < RL_REGISTER_MAX_TOTAL; $i++) $stmt->execute([rl_subject('all', 'register')]);
check('Gesamtgrenze für Registrierungen greift für jede IP', rl_register_attempt($pdo) > 0, true);

// ---------------------------------------------------------------- Datenschutz und Aufräumen
reset_attempts($pdo); setClient('203.0.113.7');
rl_login_failed($pdo, 'geheimer-name'); rl_register_attempt($pdo);
$dump = json_encode($pdo->query('SELECT scope, subject FROM auth_attempts')->fetchAll(PDO::FETCH_ASSOC));
check('kein Klartext von Name oder IP in der Datenbank', (strpos($dump, 'geheimer-name') === false) && (strpos($dump, '203.0.113.7') === false), true);

reset_attempts($pdo);
rl_login_failed($pdo, 'alt');
age($pdo, RL_KEEP_SECONDS + 60);
rl_login_failed($pdo, 'neu');
rl_cleanup($pdo);
$left = (int)$pdo->query('SELECT COUNT(*) FROM auth_attempts WHERE created_at < NOW() - INTERVAL ' . RL_KEEP_SECONDS . ' SECOND')->fetchColumn();
check('Aufräumen löscht alte Zeilen und lässt neue stehen', [$left, (int)$pdo->query('SELECT COUNT(*) FROM auth_attempts')->fetchColumn() > 0], [0, true]);

// ---------------------------------------------------------------- Ausfallsicherheit
reset_attempts($pdo);
$pdo->exec('RENAME TABLE auth_attempts TO auth_attempts_weg');
$errors = ini_set('error_log', '/dev/null');   // die erwarteten Fehlermeldungen nicht ausgeben
try {
    rl_login_failed($pdo, 'jens');
    rl_login_succeeded($pdo, 'jens');
    check('fehlende Tabelle: Anmeldung bleibt frei (kein Sperren, kein Fehler)', [rl_login_wait($pdo, 'jens'), rl_register_attempt($pdo)], [0, 0]);
} finally {
    $pdo->exec('RENAME TABLE auth_attempts_weg TO auth_attempts');
    ini_set('error_log', (string)$errors);
}

echo $failed === 0 ? "\nalle Tests bestanden\n" : "\n$failed FEHLER\n";
exit($failed === 0 ? 0 : 1);
