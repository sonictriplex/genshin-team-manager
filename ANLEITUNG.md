# Anleitung für Mitspieler

Mit dem **Team & Build Manager** hältst du deine Genshin-Impact-Teams und die Builds deiner Charaktere an einem Ort fest: Level, Sternbild, Talente, Waffe, Artefaktsets und die Werte aller fünf Artefakte (samt Teilname, Hauptwert und Nebenwerten). Du kannst ihn im **Browser** oder als **Android-App** (Handy und Tablet) nutzen; beides greift auf dasselbe Konto zu.

<p align="center">
  <img src="docs/screenshots/web/overview.jpg" alt="Übersicht aller Teams im Browser" width="720">
</p>

<sub>Die Bilder in dieser Anleitung zeigen Beispieldaten eines Demo-Kontos.</sub>

Eine Technik-Beschreibung für Entwickler steht in der [README](README.md).

**Inhalt:** [Loslegen](#loslegen) · [Teams und Builds](#teams-und-builds) · [Suchen und Beschreibungen](#suchen-filtern-und-beschreibungen) · [Android-App](#android-app) · [Passwort ändern](#passwort-ändern) · [Konto löschen](#konto-löschen) · [Über-Dialog und Version](#über-dialog-und-version) · [Daten mitnehmen](#daten-mitnehmen-oder-übertragen) · [Neue Charaktere eintragen](#neue-charaktere-und-waffen-eintragen-administratoren) · [Desktop-Version](#desktop-version-optional) · [Wenn etwas nicht klappt](#wenn-etwas-nicht-klappt)

## Loslegen

1. **Konto anlegen:** Öffne <https://genshin-manager.media-matrix.de> und wähle „Jetzt registrieren“. Der Benutzername braucht mindestens 3 Zeichen, das Passwort mindestens 6.
2. **Anmelden** mit demselben Konto, im Browser oder in der App.
3. **Teams anlegen:** Ein Team besteht aus bis zu 4 Charakteren. Name vergeben, Charaktere aus der Liste wählen (mit Suche und Filtern), speichern. Ein bestehendes Team kannst du jederzeit **umbenennen**.
4. **Builds pflegen:** Öffne in einem Team einen Charakter und lege seinen Build an oder bearbeite ihn.

<table>
  <tr>
    <td align="center"><img src="docs/screenshots/web/login.jpg" alt="Anmeldung im Browser" width="420"><br><sub>Anmeldung im Browser</sub></td>
    <td align="center"><img src="docs/screenshots/android/tablet-login.jpg" alt="Anmeldung in der Android-App" width="420"><br><sub>Anmeldung in der App</sub></td>
  </tr>
</table>

In der App ist das Feld **„Server“** schon mit `https://genshin-manager.media-matrix.de/` ausgefüllt. Lass es so, es sei denn, du hast ausdrücklich eine andere Adresse bekommen. Ein Konto kannst du dort auch direkt über „Noch kein Konto? Registrieren“ anlegen.

## Teams und Builds

- **Ein Build gehört zum Charakter, nicht zum Team.** Steht Furina in drei Teams, hat sie überall denselben Build. Änderst du ihn, ändert er sich in allen Teams.
- **Teams sortieren:** Mit den Pfeilen auf der Teamkarte verschiebst du Teams; im Browser geht das auch per Drag & Drop. Auch die Reihenfolge der Charaktere im Team lässt sich ändern. Alles wird gespeichert.
- **Startseite:** Nach der Anmeldung siehst du alle deine Teams auf einen Blick; ein Klick auf ein Team öffnet es.
- **Stat-Namen:** Verteidigung heißt überall „VTD“ (also „VTD%“ und „VTD (Fix)“). Ältere Builds mit „DEF“ werden automatisch umgestellt.
- **Deine Daten sind nur deine:** Jedes Konto sieht nur die eigenen Teams und Builds.

**Im Browser** findest du Alle Teams, Neues Team, Exportieren, Importieren, Logout, Passwort ändern, Konto löschen und Über im Benutzermenü oben rechts (für Administratoren zusätzlich „Stammdaten aktualisieren“ nach „Importieren“):

<p align="center">
  <img src="docs/screenshots/web/menu.jpg" alt="Benutzermenü im Browser" width="560">
</p>

Ein einzelnes Team zeigt die Charaktere mit Level und Sternbild; ein Klick auf einen Charakter öffnet seinen Build:

<p align="center">
  <img src="docs/screenshots/web/team.jpg" alt="Ein Team im Browser" width="720">
</p>

Dort trägst du Level, Sternbild, Talente, Waffe, Artefaktsets und die Werte der fünf Artefakt-Slots ein. Je Slot wählst du den **Namen des Teils** (z. B. „Zuflucht des Gladiators“) aus einer Liste mit Suchfeld und **Icon je Teil** (Browser, Desktop und App): Die Teile deiner gewählten Sets stehen oben, darunter alle anderen, damit auch ein Off-Piece (bei 4er-Sets oder Mischungen) möglich ist.

<p align="center">
  <img src="docs/screenshots/web/build.jpg" alt="Build eines Charakters im Browser" width="720">
</p>

**In der App** tippst du auf einen Charakter, um seinen Build zu sehen, und oben rechts auf „Bearbeiten“, um ihn zu ändern:

<table>
  <tr>
    <td align="center"><img src="docs/screenshots/android/phone-teams.jpg" alt="Teamliste auf dem Handy" width="200"><br><sub>Teams</sub></td>
    <td align="center"><img src="docs/screenshots/android/phone-build.jpg" alt="Build auf dem Handy" width="200"><br><sub>Build ansehen</sub></td>
    <td align="center"><img src="docs/screenshots/android/phone-edit.jpg" alt="Build bearbeiten auf dem Handy" width="200"><br><sub>Build bearbeiten</sub></td>
  </tr>
</table>

Beim Verlassen mit ungespeicherten Änderungen fragt die App nach, bevor sie etwas verwirft.

## Suchen, Filtern und Beschreibungen

- **Charaktere suchen:** Die Auswahl hat ein Suchfeld und Filter nach **Region**, **Element** und **Seltenheit**. Die Regionen entstehen aus den vorhandenen Charakteren; neue Regionen erscheinen von selbst.
- **Waffen suchen:** Filter nach **Waffentyp** und **Seltenheit** plus Suchfeld.
- **Beschreibungen:** Fährst du im Browser mit der Maus über ein Artefaktset, bekommst du die **Set-Boni** (1er/2er/4er); an der Waffe steht das **Passiv**, passend zur gewählten Veredelung. Am Desktop funktioniert das genauso. In der **Android-App** tippst du auf „ⓘ Beschreibung anzeigen“, um den Text aufzuklappen.

<table>
  <tr>
    <td align="center"><img src="docs/screenshots/web/character-search.jpg" alt="Charaktersuche im Browser" width="420"><br><sub>Charaktere filtern</sub></td>
    <td align="center"><img src="docs/screenshots/web/weapon-search.jpg" alt="Waffensuche im Browser" width="420"><br><sub>Waffen filtern, mit Passiv</sub></td>
  </tr>
</table>

<p align="center">
  <img src="docs/screenshots/android/phone-info.jpg" alt="Aufgeklappte Waffenbeschreibung in der App" width="240">
</p>

## Android-App

**Voraussetzung:** Android 8.0 oder neuer. Die App gibt es nicht im Play Store; du bekommst die Datei `app-release.apk` direkt von mir.

**Installieren**
1. APK aufs Handy oder Tablet bringen (Messenger, Cloud, USB).
2. Antippen. Android fragt, ob dein Browser bzw. Dateimanager Apps installieren darf; erlaube das für diesen einen Vorgang.
3. App öffnen und mit deinem Konto anmelden (oder dort direkt „Registrieren“ wählen).

**Aktualisieren:** Neue APK einfach über die alte installieren. Deine Anmeldung und Daten bleiben erhalten.

**Handy und Tablet**
- Das **Handy** zeigt eine Spalte.
- Auf dem **Tablet** darf der Bildschirm gedreht werden. Teams stehen dort in zwei (Hochformat) oder drei Spalten (Querformat), Builds zweispaltig, sodass nichts verschenkt wird:

<table>
  <tr>
    <td align="center"><img src="docs/screenshots/android/tablet-teams.jpg" alt="Tablet: Teams in drei Spalten" width="420"><br><sub>Teams in drei Spalten</sub></td>
    <td align="center"><img src="docs/screenshots/android/tablet-build.jpg" alt="Tablet: Build zweispaltig" width="420"><br><sub>Build zweispaltig</sub></td>
  </tr>
</table>

Beim Bearbeiten stehen die Eingabefelder auf dem Tablet ebenfalls in zwei Spalten, links Charakter, Waffe und Sets, rechts die fünf Artefakt-Slots:

<p align="center">
  <img src="docs/screenshots/android/tablet-edit.jpg" alt="Tablet: Build bearbeiten" width="640">
</p>

**Menü (⋮ oben rechts):** Abmelden, Über (Version) und Konto löschen (ein „Passwort ändern“ gibt es in der App nicht, das geht im Browser). „Neu laden“ (Pfeil daneben) holt den aktuellen Stand vom Server.

<p align="center">
  <img src="docs/screenshots/android/phone-menu.jpg" alt="Menü der App" width="240">
</p>

**Ohne Internet:** Die zuletzt geladenen Teams und Builds lassen sich auch offline ansehen. Bearbeiten geht nur mit Verbindung; die App zeigt dann „Offline – Stand vom …“ an. Über „Neu laden“ wird es erneut versucht.

## Passwort ändern

Im **Browser** kannst du dein Passwort selbst ändern: Benutzermenü oben rechts → „Passwort ändern“. Du gibst dein **aktuelles Passwort** und zweimal das **neue** ein (6 bis 72 Zeichen, es muss sich vom alten unterscheiden). Stimmt das aktuelle nicht, bleibt alles unverändert und du bekommst die Meldung „Das aktuelle Passwort ist falsch.“. Nach erfolgreicher Änderung musst du dich auf **anderen Geräten**, auch in der Android-App, neu anmelden; im Browser, in dem du es geändert hast, bleibst du angemeldet. In der App gibt es diese Funktion nicht; ändere das Passwort im Browser und melde dich danach in der App neu an.

<p align="center">
  <img src="docs/screenshots/web/password.jpg" alt="Passwort ändern im Browser" width="560">
</p>

Wähle ein Passwort, das du nirgendwo sonst benutzt. Ein Passwort **zurücksetzen** (wenn du es vergessen hast) geht nicht von selbst; wende dich in dem Fall an den Betreiber.

## Konto löschen

Wenn du die App nicht mehr nutzen möchtest, kannst du dein Konto selbst löschen. **Dabei werden dein Konto, alle Teams und alle Builds endgültig entfernt, in Browser und App. Das lässt sich nicht rückgängig machen.**

- **Im Browser:** Benutzermenü oben rechts → „Konto löschen“.
- **In der App:** Menü ⋮ → „Konto löschen“ (nur mit Verbindung).

Du bestätigst mit deinem Passwort. Stimmt es nicht, bleibt alles unverändert und du bekommst die Meldung „Passwort falsch.“. Exportiere vorher, wenn du deine Daten behalten willst (siehe unten).

<table>
  <tr>
    <td align="center"><img src="docs/screenshots/web/delete-account.jpg" alt="Konto löschen im Browser" width="420"><br><sub>Im Browser</sub></td>
    <td align="center"><img src="docs/screenshots/android/tablet-delete.jpg" alt="Konto löschen in der App" width="420"><br><sub>In der App</sub></td>
  </tr>
</table>

## Über-Dialog und Version

Im Browser (Benutzermenü → „Über“), in der App (Menü ⋮ → „Über“) und am Desktop (Hilfe → „Über…“) zeigt ein kleiner Dialog die **Version**, einen Hinweis zum Fanprojekt und das Logo von the media-matrix. Ein Klick bzw. Tipp auf das Logo öffnet www.media-matrix.de. Nenne mir die Version, wenn du einen Fehler meldest: Die drei Varianten haben **eigene Versionsnummern** (aktuell Web 1.8.0, Android und Desktop 1.7.2), denn der Browser bekommt Neuerungen früher als App und Desktop. Der Verlauf steht im [CHANGELOG](CHANGELOG.md).

<table>
  <tr>
    <td align="center"><img src="docs/screenshots/web/about.jpg" alt="Über-Dialog im Browser" width="380"><br><sub>Browser</sub></td>
    <td align="center"><img src="docs/screenshots/android/about.jpg" alt="Über-Dialog in der App" width="380"><br><sub>App</sub></td>
    <td align="center"><img src="docs/screenshots/desktop/about.jpg" alt="Über-Dialog am Desktop" width="260"><br><sub>Desktop</sub></td>
  </tr>
</table>

## Daten mitnehmen oder übertragen

Teams und Builds lassen sich als JSON-Datei exportieren und wieder importieren, zum Beispiel zum Sichern oder um Daten aus der Desktop-Version in die Web-Version zu übernehmen. Im Browser findest du beides im Benutzermenü („Exportieren“, „Importieren“), am Desktop im Menü „Datei“.

## Neue Charaktere und Waffen eintragen (Administratoren)

Kommt im Spiel etwas Neues dazu, tragen Administratoren es selbst im **Browser** ein. Du erkennst dich als Administrator daran, dass dein Benutzermenü den Punkt **„Stammdaten aktualisieren“** enthält:

1. Der Dialog gleicht die öffentliche Datenquelle mit der Datenbank ab und listet, was fehlt (Charaktere und Waffen).
2. **Charaktere** bekommen ihre Region aus der Datenquelle (genshin-db), sie ist vorausgewählt und änderbar; fehlt sie dort, wählst du sie selbst. Setze nur dort einen Haken, wo der Charakter im Spiel schon erschienen ist.
3. **Waffen** sind vorausgewählt. Einträge, die die Datenquelle nicht kennt (vermutlich noch nicht erschienen), zeigt der Dialog unter „Nicht eintragbar“ an.
4. „Ausgewählte eintragen“ legt die Einträge samt Bildern an (bei Waffen mit dem Passiv-Text für den Tooltip). Danach stehen sie sofort in der Auswahl; die Android-App und der Desktop bekommen neue Charaktere erst mit einem neuen Build.

<p align="center">
  <img src="docs/screenshots/web/update.jpg" alt="Stammdaten aktualisieren im Browser (Beispieleinträge)" width="620">
</p>

<sub>Das Bild zeigt Beispieleinträge, keine echten Charaktere.</sub>

Wer kein Administrator ist, sieht den Punkt nicht; fehlt dir ein Charakter oder eine Waffe, melde das dem Betreiber.

## Desktop-Version (optional)

Es gibt auch eine Desktop-App, die ihre Daten lokal in einer Datei speichert und **kein Konto** braucht. Sie läuft direkt aus dem Quellcode (Python und PySide6, siehe [desktop/README.md](desktop/README.md)); Builds und Teams lassen sich per JSON-Export mit der Web-Version austauschen. Sie kennt Teams, Builds, Teilnamen, Tooltips mit Set-Boni und Waffen-Passiv, Such- und Filterfunktionen sowie die Ansicht „Alle Teams“; „Passwort ändern“ und die Stammdaten-Aktualisierung gibt es nur im Browser.

<table>
  <tr>
    <td align="center"><img src="docs/screenshots/desktop/overview.jpg" alt="Desktop: Teamübersicht" width="420"><br><sub>Teamübersicht</sub></td>
    <td align="center"><img src="docs/screenshots/desktop/build.jpg" alt="Desktop: Build eines Charakters" width="420"><br><sub>Build eines Charakters</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/screenshots/desktop/all-teams.jpg" alt="Desktop: Alle Teams" width="420"><br><sub>Alle Teams</sub></td>
    <td align="center"><img src="docs/screenshots/desktop/weapon-search.jpg" alt="Desktop: Waffensuche" width="420"><br><sub>Waffensuche</sub></td>
  </tr>
</table>

## Wenn etwas nicht klappt

| Problem | Lösung |
|---|---|
| „Dieser Benutzername ist bereits vergeben“ | Anderen Namen wählen. |
| „Zu viele Versuche“ | Kurz warten; der Server bremst wiederholte Anmeldungen. |
| „Passwort falsch.“ beim Konto löschen | Passwort prüfen; es wird erst bei richtiger Eingabe gelöscht. |
| App zeigt „Offline“ | Internetverbindung prüfen, dann „Neu laden“. |
| Anmeldung in der App schlägt fehl | Prüfe, ob im Feld „Server“ `https://genshin-manager.media-matrix.de/` steht. |
| Installation der APK wird abgelehnt | Installation aus dieser Quelle in den Android-Einstellungen erlauben. |
| Ein Tooltip oder die Beschreibung fehlt | Im Browser über das Element fahren; in der App „ⓘ Beschreibung anzeigen“ antippen. Fehlt sie dort, ist sie noch nicht in den Daten; melde es dem Betreiber. |
| Ein Charakter oder eine Waffe fehlt | Ein Administrator trägt ihn im Browser über „Stammdaten aktualisieren“ ein; sonst beim Betreiber melden. |
| „Benutzername oder Passwort falsch.“ | Auf Groß- und Kleinschreibung achten. Passwort-Manager füllen manchmal ein **altes** Passwort ein: im privaten Fenster und von Hand eintippen. |
| „Das aktuelle Passwort ist falsch.“ beim Ändern | Aktuelles Passwort prüfen; das neue muss 6 bis 72 Zeichen lang sein und sich vom alten unterscheiden. |

## Hinweis

Inoffizielles Fanprojekt, nicht mit HoYoverse verbunden. Genshin Impact sowie zugehörige Namen und Bilder sind Eigentum von HoYoverse.
