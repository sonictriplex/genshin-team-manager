<?php
// Gemeinsame Hilfsfunktionen für teams.php und transfer.php

/** Begrenzt einen Zahlenwert auf einen Bereich (Fallback bei ungültiger Eingabe). */
function clamp_int($value, int $min, int $max, int $default): int {
    if (!is_numeric($value)) return $default;
    return max($min, min($max, (int)$value));
}

/** Platzhaltertexte wie "— Zweites 2er-Set (optional) —" werden zu einem leeren Wert. */
function clean_set($value): string {
    $v = trim((string)$value);
    if ($v === '' || mb_strpos($v, '—') === 0) return '';
    return $v;
}

/** Ältere Namen der Stats (DEF heißt jetzt VTD, Verteidigung) -> aktueller Name; alles andere bleibt unverändert. */
function current_stat_name($stat) {
    static $renamed = ['DEF%' => 'VTD%', 'DEF (Fix)' => 'VTD (Fix)'];
    return is_string($stat) ? ($renamed[$stat] ?? $stat) : $stat;
}

/** Wendet current_stat_name auf Haupt- und Substats aller Slots an (Daten, die vor der Umbenennung gespeichert wurden). */
function rename_legacy_stats($stats) {
    if (!is_array($stats)) return $stats;
    foreach ($stats as $slotName => $slot) {
        if (!is_array($slot)) continue;
        if (isset($slot['main_stat'])) $stats[$slotName]['main_stat'] = current_stat_name($slot['main_stat']);
        if (isset($slot['substats']) && is_array($slot['substats'])) {
            foreach ($slot['substats'] as $i => $sub) {
                if (is_array($sub) && isset($sub['stat'])) $stats[$slotName]['substats'][$i]['stat'] = current_stat_name($sub['stat']);
            }
        }
    }
    return $stats;
}

/**
 * Bringt artifact_stats in ein sauberes, immer gleiches Format:
 * - Rückgabe ist ein assoziatives Array (Slot => Daten) oder leer
 * - jeder Slot hat genau 4 Substats der Form {stat, val}
 * - piece (Name des Artefaktteils) ist, falls vorhanden, ein String mit höchstens 255 Zeichen
 */
function normalize_artifact_stats($stats): array {
    if (!is_array($stats)) return [];

    $clean = [];
    foreach ($stats as $slotName => $slot) {
        if (!is_string($slotName) || !is_array($slot)) continue;

        $subsIn = (isset($slot['substats']) && is_array($slot['substats']))
        ? array_values($slot['substats'])
        : [];

        $subs = [];
        for ($i = 0; $i < 4; $i++) {
            $e = $subsIn[$i] ?? [];

            // Altformat: "KT% + 3.9"
            if (is_string($e)) {
                $parts = explode('+', $e, 2);
                $e = ['stat' => trim($parts[0]), 'val' => trim($parts[1] ?? '')];
            }
            if (!is_array($e)) $e = [];

            $subs[] = [
                'stat' => (string)($e['stat'] ?? ''),
                'val'  => (string)($e['val'] ?? '')
            ];
        }

        $slot['substats'] = $subs;
        if (isset($slot['main_stat'])) $slot['main_stat'] = current_stat_name($slot['main_stat']);
        foreach ($slot['substats'] as $i => $sub) $slot['substats'][$i]['stat'] = current_stat_name($sub['stat']);
        if (array_key_exists('piece', $slot)) {
            $slot['piece'] = is_string($slot['piece']) ? mb_substr(trim($slot['piece']), 0, 255) : '';
        }
        $clean[$slotName] = $slot;
    }
    return $clean;
}
