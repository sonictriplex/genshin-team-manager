<?php
// Stammdaten (Charaktere, Waffen) mit der Quelle Enka.Network abgleichen und ergänzen. Nur für Admins.
//   GET  ?action=check                                  -> was fehlt (ändert nichts)
//   POST {characters: [{name, region}], weapons: [Name]} -> ausgewählte Einträge eintragen
// Spiegelt tools/update_stammdaten.py; die Datei shared/stammdaten.json im Repository wird dadurch NICHT verändert
// (ein späterer Lauf des Skripts findet die Einträge dort und ergänzt sie lokal).
// Die Region steht nicht in der Quelle: sie wird im Dialog gewählt und hier gegen die erlaubte Liste geprüft.
header('Content-Type: application/json; charset=utf-8');

require_once __DIR__ . '/db.php';
require_once __DIR__ . '/auth_check.php';
require_once __DIR__ . '/stammdaten_lib.php';

require_login();
require_admin();
set_time_limit(120);

const SRC = 'https://raw.githubusercontent.com/EnkaNetwork/API-docs/master/store/gi/';
const UI = 'https://enka.network';
const GDB = 'https://raw.githubusercontent.com/theBowja/genshin-db/main/src/data/German/weapons/';   // nur erschienene Waffen, mit Passiv-Texten
const MAX_APPLY = 50;
const REGIONS = ['Mondstadt', 'Liyue', 'Inazuma', 'Sumeru', 'Fontaine', 'Natlan', 'Nod-Krai', 'Snezhnaya', 'Andere Welt'];
const ELEMENTS = ['Fire' => 'Pyro', 'Water' => 'Hydro', 'Wind' => 'Anemo', 'Electric' => 'Electro', 'Grass' => 'Dendro', 'Ice' => 'Cryo', 'Rock' => 'Geo'];
const CHAR_WEAPONS = ['WEAPON_SWORD_ONE_HAND' => 'Einhandschwert', 'WEAPON_CLAYMORE' => 'Großschwert', 'WEAPON_POLE' => 'Stangenwaffe',
    'WEAPON_BOW' => 'Bogen', 'WEAPON_CATALYST' => 'Katalysator'];
const WEAPON_TYPES = [1 => 'Einhandschwert', 2 => 'Großschwert', 3 => 'Bogen', 4 => 'Stangenwaffe', 5 => 'Katalysator'];
const QUALITY = ['QUALITY_ORANGE' => 5, 'QUALITY_PURPLE' => 4];

/** Dateiname wie getIconUrl() im Frontend: klein, Leerzeichen -> _, Anführungszeichen und Bindestriche weg. */
function icon_file(string $name): string {
    $n = mb_strtolower(trim(explode('(', $name)[0]));
    return preg_replace('/[\'’„“\-]/u', '', str_replace(' ', '_', $n)) . '.png';
}

/**
 * Passiv-Beschreibung einer Waffe aus genshin-db. Rückgabe: [gefunden, passive].
 * gefunden=false: die Waffe steht dort nicht, ist also vermutlich noch nicht erschienen (wird nicht eingetragen).
 */
function fetch_passive(string $nameEn): array {
    $slug = preg_replace('/[^a-z0-9]/', '', strtolower($nameEn));
    if ($slug === '') return [false, null];
    try {
        $w = fetch_json(GDB . $slug . '.json');
    } catch (RuntimeException $e) {
        if ($e->getCode() === 404) return [false, null];
        throw $e;
    }
    if (empty($w['effectName']) || empty($w['r1'])) return [true, null];   // z. B. Einsteigerwaffen ohne Passiv
    $text = [];
    for ($i = 1; $i <= 5; $i++) $text[] = (string)($w["r$i"]['description'] ?? '');
    return [true, json_encode(['name' => $w['effectName'], 'text' => $text], JSON_UNESCAPED_UNICODE)];
}

/** Ermittelt, was in der Datenbank fehlt: [neue Charaktere, neue Waffen, vermutlich nicht erschienene Waffen]. */
function find_new(PDO $pdo): array {
    $avatars = fetch_json(SRC . 'avatars.json');
    $weapons = fetch_json(SRC . 'weapons.json');
    $locs = fetch_json(SRC . 'locs.json');
    $en = $locs['en'] ?? [];
    $de = $locs['de'] ?? [];

    $haveChars = array_flip(array_map('norm_name', $pdo->query("SELECT name FROM characters")->fetchAll(PDO::FETCH_COLUMN)));
    $haveWeapons = array_flip(array_map('norm_name', $pdo->query("SELECT name FROM weapons")->fetchAll(PDO::FETCH_COLUMN)));

    $chars = [];
    foreach ($avatars as $id => $a) {
        // nur reguläre Charaktere: keine Reisenden (Varianten mit "-"), keine Test-/Testversions-IDs
        if (!ctype_digit((string)$id) || (int)$id < 10000002 || (int)$id >= 10000900) continue;
        $name = $en[(string)($a['NameTextMapHash'] ?? '')] ?? '';
        if ($name === '' || $name === 'Traveler' || str_contains($name, '(') || isset($haveChars[norm_name($name)])) continue;
        $q = QUALITY[$a['QualityType'] ?? ''] ?? null;
        $el = ELEMENTS[$a['Element'] ?? ''] ?? null;
        $wt = CHAR_WEAPONS[$a['WeaponType'] ?? ''] ?? null;
        if (!$q || !$el || !$wt) continue;
        $chars[] = ['name' => $name, 'element' => $el, 'weapon_type' => $wt, 'rarity' => $q,
            'icon_path' => 'assets/images/' . icon_file($name),
            'src' => UI . '/ui/' . str_replace('Side_', '', basename((string)$a['SideIconName']))];
    }

    $newWeapons = [];
    $unverified = [];
    foreach ($weapons as $id => $w) {
        $nameDe = $de[(string)($w['NameTextMapHash'] ?? '')] ?? '';
        $type = WEAPON_TYPES[$w['WeaponType'] ?? 0] ?? null;
        $rarity = (int)($w['Rarity'] ?? 0);
        if ($nameDe === '' || !$type || $rarity < 1 || $rarity > 5 || str_contains($nameDe, '(') || isset($haveWeapons[norm_name($nameDe)])) continue;
        $name = trim(preg_replace('/^[„“"]|[“”"]$/u', '', $nameDe));
        [$found, $passive] = fetch_passive($en[(string)($w['NameTextMapHash'] ?? '')] ?? '');
        if (!$found) { $unverified[] = $name; continue; }
        $newWeapons[] = ['name' => $name, 'weapon_type' => $type, 'rarity' => $rarity, 'src' => UI . $w['Icon'],
            'file' => icon_file($name), 'passive' => $passive];
    }
    usort($chars, fn($a, $b) => strcasecmp($a['name'], $b['name']));
    usort($newWeapons, fn($a, $b) => strcasecmp($a['name'], $b['name']));
    sort($unverified);
    return [$chars, $newWeapons, $unverified];
}

try {
    [$chars, $weapons, $unverified] = find_new($pdo);

    if (($_SERVER['REQUEST_METHOD'] ?? '') === 'GET') {
        $strip = fn($e) => array_diff_key($e, ['src' => 1, 'icon_path' => 1, 'file' => 1, 'passive' => 1]);
        echo json_encode(["new" => ["characters" => array_map($strip, $chars), "weapons" => array_map($strip, $weapons)],
            "skipped" => array_map(fn($n) => "Waffe $n: nicht in genshin-db, vermutlich noch nicht erschienen", $unverified)], JSON_UNESCAPED_UNICODE);
        exit();
    }

    $in = require_ajax_post();
    $selChars = [];
    foreach ((array)($in['characters'] ?? []) as $c) {
        if (!is_array($c) || !is_string($c['name'] ?? null) || !in_array($c['region'] ?? null, REGIONS, true)) continue;
        $selChars[norm_name($c['name'])] = $c['region'];
    }
    $selWeapons = array_flip(array_map('norm_name', array_filter((array)($in['weapons'] ?? []), 'is_string')));
    if (count($selChars) + count($selWeapons) > MAX_APPLY) {
        http_response_code(400);
        echo json_encode(["error" => "Zu viele Einträge auf einmal (höchstens " . MAX_APPLY . ")."], JSON_UNESCAPED_UNICODE);
        exit();
    }

    // Eingetragen wird nur, was die Quelle tatsächlich liefert: dem Browser wird nur die Auswahl der Namen geglaubt
    $added = 0;
    $images = ['geladen' => 0, 'vorhanden' => 0, 'fehler' => 0];
    $insChar = $pdo->prepare("INSERT IGNORE INTO characters (name, element, weapon_type, region, rarity, icon_path) VALUES (?, ?, ?, ?, ?, ?)");
    $insWeapon = $pdo->prepare("INSERT IGNORE INTO weapons (name, weapon_type, rarity, passive_json) VALUES (?, ?, ?, ?)");
    $count = function (string $state) use (&$images) { $images[str_starts_with($state, 'FEHLER') ? 'fehler' : $state]++; };

    $pdo->beginTransaction();
    foreach ($chars as $c) {
        $region = $selChars[norm_name($c['name'])] ?? null;
        if ($region === null) continue;
        $insChar->execute([$c['name'], $c['element'], $c['weapon_type'], $region, $c['rarity'], $c['icon_path']]);
        $added += $insChar->rowCount();
        $count(save_image($c['src'], basename($c['icon_path'])));
    }
    foreach ($weapons as $w) {
        if (!isset($selWeapons[norm_name($w['name'])])) continue;
        $insWeapon->execute([$w['name'], $w['weapon_type'], $w['rarity'], $w['passive']]);
        $added += $insWeapon->rowCount();
        $count(save_image($w['src'], $w['file']));
    }
    $pdo->commit();
    echo json_encode(["added" => $added, "images" => $images], JSON_UNESCAPED_UNICODE);
} catch (Throwable $e) {
    if ($pdo->inTransaction()) $pdo->rollBack();
    error_log("stammdaten.php: " . $e->getMessage());
    http_response_code(500);
    echo json_encode(["error" => "Die Datenquelle konnte nicht abgefragt oder die Daten nicht gespeichert werden."], JSON_UNESCAPED_UNICODE);
}
