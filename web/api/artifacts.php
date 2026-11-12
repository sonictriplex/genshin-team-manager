<?php
header('Content-Type: application/json; charset=utf-8');

require_once __DIR__ . '/db.php';

try {
    try {
        $stmt = $pdo->query("SELECT id, name, bonus_2pc, bonus_4pc, pieces_json FROM artifacts ORDER BY name ASC");
    } catch (PDOException $e) {
        // Migration 004 (Spalte pieces_json) fehlt noch: die Sets ohne Teilnamen ausliefern
        error_log("artifacts.php: pieces_json fehlt, bitte migrations/004_artifact_pieces.sql ausführen: " . $e->getMessage());
        $stmt = $pdo->query("SELECT id, name, bonus_2pc, bonus_4pc FROM artifacts ORDER BY name ASC");
    }
    $artifacts = $stmt->fetchAll(PDO::FETCH_ASSOC);
    // Teilnamen (Blume, Feder, ...) als Objekt ausgeben; leer = new stdClass(), damit es kein JSON-Array wird
    foreach ($artifacts as &$artifact) {
        $pieces = json_decode((string)($artifact['pieces_json'] ?? ''), true);
        $artifact['pieces'] = (is_array($pieces) && $pieces) ? $pieces : new stdClass();
        unset($artifact['pieces_json']);
    }
    unset($artifact);
    echo json_encode($artifacts, JSON_UNESCAPED_UNICODE);
} catch (PDOException $e) {
    http_response_code(500);
    error_log("artifacts.php: " . $e->getMessage());
    echo json_encode(["error" => "Fehler beim Laden der Artefakte."], JSON_UNESCAPED_UNICODE);
}
?>
