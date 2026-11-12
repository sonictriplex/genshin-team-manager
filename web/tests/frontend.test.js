// Tests für das Web-Frontend (web/index.html): Verschieben der Teamkarten (Pfeile, Drag & Drop), Benutzermenü, Anzeige von Anmeldefehlern.
//
// Start: cd web/tests && npm install && npm test
//
// Die Seite wird in jsdom geladen, die API per fetch-Attrappe beantwortet (Stammdaten aus shared/stammdaten.json).
// jsdom kennt kein echtes Drag & Drop; die Drag-Ereignisse werden mit einem nachgebauten dataTransfer ausgelöst.
// Das prüft die Logik der Seite, nicht das Verhalten eines echten Browsers beim Ziehen mit der Maus.

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');

const ROOT = path.join(__dirname, '..', '..');
const INDEX = fs.readFileSync(path.join(ROOT, 'web', 'index.html'), 'utf8')
    // Tailwind kommt vom CDN und wird für die Logik nicht gebraucht
    .replace(/<script src="https:\/\/cdn[^>]*><\/script>/g, '');
const STAMMDATEN = JSON.parse(fs.readFileSync(path.join(ROOT, 'shared', 'stammdaten.json'), 'utf8'));

const NAMES = ['Furina', 'Nilou', 'Barbara', 'Collei'];
const CHARACTERS = NAMES.map(n => STAMMDATEN.characters.find(c => c.name === n));
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Lädt die Seite mit einem Team "Test" aus Furina, Nilou und Barbara (in dieser Reihenfolge).
 * Die Seite startet mit der Übersicht aller Teams; `openTeam` öffnet das Team danach wie ein Klick auf seine Karte.
 */
async function loadPage({ loggedIn = true, openTeam = true, teams = null, artifacts = [] } = {}) {
    const posted = [];
    const deleted = [];
    const routes = {
        'auth.php?action=status': loggedIn ? { logged_in: true, username: 'tester', user_id: 1 } : { logged_in: false },
        'characters.php': CHARACTERS,
        'weapons.php': [],
        'artifacts.php': artifacts,
        'teams.php': teams || { Test: CHARACTERS.slice(0, 3).map(c => ({ character: c, saved: { level: 90 } })) },
    };
    const dom = new JSDOM(INDEX, {
        runScripts: 'dangerously',
        url: 'http://localhost/',
        pretendToBeVisual: true,
        beforeParse(window) {
            window.tailwind = {};
            window.alert = () => {};
            window.fetch = async (url, options = {}) => {
                if (options.method === 'DELETE') {
                    deleted.push(decodeURIComponent(String(url).split('name=')[1]));
                    return { ok: true, json: async () => ({ message: 'gelöscht' }) };
                }
                if (options.method === 'POST') {
                    posted.push({ url: String(url), body: JSON.parse(options.body) });
                    return { ok: true, json: async () => ({ message: 'ok' }) };
                }
                const key = Object.keys(routes).find(k => String(url).endsWith(k));
                return { ok: Boolean(key), json: async () => routes[key] };
            };
        },
    });
    await sleep(300);   // der Start lädt die Daten asynchron

    const w = dom.window;
    const d = w.document;
    if (loggedIn && openTeam) w.onTeamSelected('Test');
    const cards = () => [...d.querySelectorAll('#overviewView [data-drag-handle]')].map(h => h.parentElement);
    const handles = () => [...d.querySelectorAll('#overviewView [data-drag-handle]')];
    const order = () => cards().map(c => c.querySelector('span.truncate').textContent);
    const freeSlot = () => [...d.querySelectorAll('#overviewView > div')].find(x => x.textContent.includes('Charakter hinzufügen'));
    const button = (index, title) => [...d.querySelectorAll('#overviewView > div')][index].querySelector(`button[title="${title}"]`);

    /** Löst ein Drag-Ereignis mit nachgebautem dataTransfer aus. */
    function drag(type, target) {
        const event = new w.Event(type, { bubbles: true, cancelable: true });
        const data = {};
        event.dataTransfer = { effectAllowed: '', dropEffect: '', setData: (k, v) => { data[k] = v; }, setDragImage() {} };
        target.dispatchEvent(event);
        return event;
    }
    return { w, d, posted, deleted, cards, handles, order, freeSlot, button, drag };
}

/** Jsdom-Klick, der wie im Browser bis zum document sprudelt. */
const click = (w, el) => el.dispatchEvent(new w.MouseEvent('click', { bubbles: true, cancelable: true }));

test('Startreihenfolge und Pfeile an den Rändern', async () => {
    const p = await loadPage();
    assert.deepEqual(p.order(), ['Furina', 'Nilou', 'Barbara']);
    assert.equal(p.button(0, 'Nach links').disabled, true, 'erste Karte: ‹ aus');
    assert.equal(p.button(0, 'Nach rechts').disabled, false);
    assert.equal(p.button(2, 'Nach rechts').disabled, true, 'letzte Karte: › aus');
});

test('Pfeile verschieben die Karte', async () => {
    const p = await loadPage();
    p.button(0, 'Nach rechts').click();
    assert.deepEqual(p.order(), ['Nilou', 'Furina', 'Barbara']);
    p.button(2, 'Nach links').click();
    assert.deepEqual(p.order(), ['Nilou', 'Barbara', 'Furina']);
});

test('Drop auf eine Karte rechts verschiebt, die Markierung verschwindet', async () => {
    const p = await loadPage();
    p.drag('dragstart', p.handles()[0]);
    const over = p.drag('dragover', p.cards()[2]);
    assert.equal(over.defaultPrevented, true, 'Ablegen erlaubt');
    assert.equal(p.cards()[2].classList.contains('ring-2'), true, 'Ziel markiert');
    p.drag('drop', p.cards()[2]);
    assert.deepEqual(p.order(), ['Nilou', 'Barbara', 'Furina']);
    assert.equal(p.d.querySelectorAll('#overviewView .ring-2').length, 0);
});

test('Drop nach links', async () => {
    const p = await loadPage();
    p.drag('dragstart', p.handles()[2]);
    p.drag('drop', p.cards()[0]);
    assert.deepEqual(p.order(), ['Barbara', 'Furina', 'Nilou']);
});

test('Drop auf den freien Platz stellt die Karte ans Ende', async () => {
    const p = await loadPage();
    p.drag('dragstart', p.handles()[0]);
    p.drag('drop', p.freeSlot());
    assert.deepEqual(p.order(), ['Nilou', 'Barbara', 'Furina']);
});

test('Fremde Drags, Drop auf sich selbst und Drop nach dragend ändern nichts', async () => {
    const p = await loadPage();
    // ohne dragstart (z. B. eine Datei von außen) wird nichts angenommen
    assert.equal(p.drag('dragover', p.cards()[1]).defaultPrevented, false);
    p.drag('drop', p.cards()[1]);
    assert.deepEqual(p.order(), ['Furina', 'Nilou', 'Barbara']);

    p.drag('dragstart', p.handles()[1]);
    p.drag('drop', p.cards()[1]);
    assert.deepEqual(p.order(), ['Furina', 'Nilou', 'Barbara'], 'auf sich selbst');

    p.drag('dragstart', p.handles()[0]);
    p.drag('dragend', p.handles()[0]);
    p.drag('drop', p.cards()[2]);
    assert.deepEqual(p.order(), ['Furina', 'Nilou', 'Barbara'], 'nach dragend');
});

test('Eingaben wandern mit der Karte', async () => {
    const p = await loadPage();
    const level = i => p.d.querySelectorAll('#overviewView > div')[i].querySelector('input[type=number]').value;
    const first = p.d.querySelector('#overviewView input[type=number]');
    first.value = '77';
    first.dispatchEvent(new p.w.Event('change'));

    p.button(0, 'Nach rechts').click();
    assert.equal(level(0), '90');
    assert.equal(level(1), '77', 'Level 77 gehört weiter zu Furina');
    assert.equal(p.order()[1], 'Furina');
});

test('Speichern sendet die neue Reihenfolge', async () => {
    const p = await loadPage();
    p.button(0, 'Nach rechts').click();      // Nilou, Furina, Barbara
    p.drag('dragstart', p.handles()[2]);     // Barbara nach ganz links
    p.drag('drop', p.cards()[0]);            // Barbara, Nilou, Furina

    await p.w.saveCurrentTeam();

    assert.equal(p.posted.length, 1);
    assert.ok(p.posted[0].url.endsWith('/api/teams.php'));
    assert.equal(p.posted[0].body.name, 'Test');
    assert.deepEqual(p.posted[0].body.members.map(m => m.name), ['Barbara', 'Nilou', 'Furina']);
});

// --- Kopfzeile mit Benutzermenü (Export, Import, Logout) ---

test('Benutzermenü ist nach der Anmeldung sichtbar und zeigt den Namen; der Footer zeigt nur das Logo', async () => {
    const p = await loadPage();
    const menu = p.d.getElementById('userMenu');
    assert.equal(menu.classList.contains('hidden'), false);
    assert.equal(p.d.getElementById('userInfo').textContent, 'tester');
    assert.match(p.d.getElementById('userMenuName').textContent, /tester/);
    assert.equal(p.d.getElementById('userMenuList').classList.contains('hidden'), true, 'zunächst zu');
    const footer = p.d.querySelector('footer');
    assert.ok(footer, 'Footer mit Logo');
    assert.equal(footer.textContent.trim(), '', 'nur das Logo, keine Nutzerangaben');
    assert.match(footer.querySelector('img').getAttribute('src'), /mm_logo\.png$/);
});

test('Ohne Anmeldung bleibt das Benutzermenü verborgen und die Anmeldung erscheint', async () => {
    const p = await loadPage({ loggedIn: false });
    assert.equal(p.d.getElementById('userMenu').classList.contains('hidden'), true);
    assert.equal(p.d.getElementById('authModal').classList.contains('hidden'), false);
});

test('Das Menü öffnet und schließt per Klick, Klick daneben und Escape', async () => {
    const p = await loadPage();
    const button = p.d.getElementById('userMenuButton');
    const list = p.d.getElementById('userMenuList');

    click(p.w, button);
    assert.equal(list.classList.contains('hidden'), false);
    assert.equal(button.getAttribute('aria-expanded'), 'true');

    click(p.w, button);
    assert.equal(list.classList.contains('hidden'), true, 'zweiter Klick schließt');

    click(p.w, button);
    click(p.w, p.d.body);
    assert.equal(list.classList.contains('hidden'), true, 'Klick daneben schließt');
    assert.equal(button.getAttribute('aria-expanded'), 'false');

    click(p.w, button);
    p.d.dispatchEvent(new p.w.KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    assert.equal(list.classList.contains('hidden'), true, 'Escape schließt');
});

test('Menüpunkte lösen Export, Import und Logout aus und schließen das Menü', async () => {
    const p = await loadPage();
    const calls = [];
    p.w.exportData = () => calls.push('export');
    p.w.handleLogout = () => calls.push('logout');
    const importInput = p.d.getElementById('importFile');
    importInput.click = () => calls.push('import');

    const item = text => [...p.d.querySelectorAll('#userMenuList [role=menuitem]')].find(b => b.textContent.trim() === text);
    for (const text of ['Exportieren', 'Importieren', 'Logout']) {
        click(p.w, p.d.getElementById('userMenuButton'));
        click(p.w, item(text));
        assert.equal(p.d.getElementById('userMenuList').classList.contains('hidden'), true, `${text} schließt das Menü`);
    }
    assert.deepEqual(calls, ['export', 'import', 'logout']);
});

test('Team-Steuerung: Name, Speichern, Neues Team, Auswahl und Löschen sind vorhanden', async () => {
    const p = await loadPage();
    assert.ok(p.d.getElementById('teamNameInput'));
    assert.ok(p.d.getElementById('teamsSelect'));
    const labels = [...p.d.querySelectorAll('button')].map(b => (b.getAttribute('aria-label') || b.textContent).trim());
    assert.ok(labels.includes('Speichern'));
    assert.ok(labels.includes('Team löschen'));
    const menu = [...p.d.querySelectorAll('#userMenuList [role=menuitem]')].map(b => b.textContent.trim());
    assert.ok(menu.includes('Alle Teams') && menu.includes('Neues Team'), 'Alle Teams und Neues Team stehen im Menü');
    const outside = [...p.d.querySelectorAll('button')].filter(b => !b.closest('#userMenuList')).map(b => b.textContent.trim());
    assert.ok(!outside.includes('Alle Teams') && !outside.some(l => l.includes('Neues Team')), 'keine Knöpfe mehr in der Leiste');
    assert.equal(p.d.getElementById('teamsSelect').value, 'Test', 'das geladene Team ist ausgewählt');
});

// --- Anmeldefehler (auch die Sperre bei zu vielen Versuchen) ---

test('Anmeldefehler vom Server, auch 429 bei zu vielen Versuchen, erscheinen im Dialog', async () => {
    const p = await loadPage({ loggedIn: false });
    const form = { preventDefault() {} };
    p.d.getElementById('authUsername').value = 'jens';
    p.d.getElementById('authPassword').value = 'falsch';
    const error = p.d.getElementById('authError');

    const reply = (ok, status, error) => async () => ({ ok, status, json: async () => ({ error }) });

    p.w.fetch = reply(false, 401, 'Benutzername oder Passwort falsch.');
    await p.w.handleAuthSubmit(form);
    assert.equal(error.classList.contains('hidden'), false);
    assert.equal(error.textContent || error.innerText, 'Benutzername oder Passwort falsch.');

    p.w.fetch = reply(false, 429, 'Zu viele Anmeldeversuche. Bitte versuche es in 12 Minuten erneut.');
    await p.w.handleAuthSubmit(form);
    assert.match(error.textContent || error.innerText, /Zu viele Anmeldeversuche.*12 Minuten/);
    assert.equal(error.classList.contains('hidden'), false);
});

// --- Übersicht aller Teams und Umbenennen ---

test('Der Start zeigt die Übersicht aller Teams; ein Klick auf die Karte öffnet das Team', async () => {
    const p = await loadPage({ openTeam: false });
    assert.equal(p.d.getElementById('allTeamsView').classList.contains('hidden'), false);
    assert.equal(p.d.getElementById('overviewView').classList.contains('hidden'), true);
    const cards = [...p.d.querySelectorAll('#allTeamsView > div')];
    assert.equal(cards.length, 1);
    assert.match(cards[0].textContent, /Test/);
    assert.equal(cards[0].querySelectorAll('img').length, 3);
    click(p.w, cards[0]);
    assert.equal(p.d.getElementById('allTeamsView').classList.contains('hidden'), true);
    assert.deepEqual(p.order(), ['Furina', 'Nilou', 'Barbara']);
});

const THREE_TEAMS = () => {
    const members = n => CHARACTERS.slice(0, n).map(c => ({ character: c, saved: { level: 90 } }));
    return { Alpha: members(1), Beta: members(2), Gamma: members(3) };
};
const teamOrder = p => [...p.d.querySelectorAll('#allTeamsView > div')].map(c => c.dataset.teamName);

test('Teamübersicht: Pfeile verschieben das Team und speichern die Reihenfolge', async () => {
    const p = await loadPage({ openTeam: false, teams: THREE_TEAMS() });
    assert.deepEqual(teamOrder(p), ['Alpha', 'Beta', 'Gamma']);
    const cards = () => [...p.d.querySelectorAll('#allTeamsView > div')];
    assert.equal(cards()[0].querySelector('button[title="Nach vorn"]').disabled, true);
    assert.equal(cards()[2].querySelector('button[title="Nach hinten"]').disabled, true);
    cards()[0].querySelector('button[title="Nach hinten"]').click();
    assert.deepEqual(teamOrder(p), ['Beta', 'Alpha', 'Gamma']);
    assert.equal(p.d.getElementById('allTeamsView').classList.contains('hidden'), false, 'Klick auf den Pfeil öffnet das Team nicht');
    await sleep(20);
    assert.deepEqual(p.posted.at(-1).body, { order: ['Beta', 'Alpha', 'Gamma'] });
});

test('Teamübersicht: Drop auf eine andere Karte verschiebt das Team', async () => {
    const p = await loadPage({ openTeam: false, teams: THREE_TEAMS() });
    const cards = () => [...p.d.querySelectorAll('#allTeamsView > div')];
    p.drag('dragstart', cards()[2]);
    p.drag('dragover', cards()[0]);
    p.drag('drop', cards()[0]);
    assert.deepEqual(teamOrder(p), ['Gamma', 'Alpha', 'Beta']);
    await sleep(20);
    assert.deepEqual(p.posted.at(-1).body, { order: ['Gamma', 'Alpha', 'Beta'] });
});

test('Umbenennen: neu speichern, danach das alte Team löschen', async () => {
    const p = await loadPage();
    p.w.confirm = () => true;
    p.d.getElementById('teamNameInput').value = 'Neu';
    await p.w.saveCurrentTeam();
    assert.equal(p.posted.at(-1).body.name, 'Neu');
    assert.deepEqual(p.deleted, ['Test']);
});

test('Namen ändern und "Als neues Team": das alte Team bleibt', async () => {
    const p = await loadPage();
    const answers = [false, true];       // erst "Umbenennen" ablehnen, dann "als neues Team" bestätigen
    p.w.confirm = () => answers.shift();
    p.d.getElementById('teamNameInput').value = 'Kopie';
    await p.w.saveCurrentTeam();
    assert.equal(p.posted.at(-1).body.name, 'Kopie');
    assert.deepEqual(p.deleted, []);
});

test('Namen ändern und alles abbrechen: nichts wird gespeichert', async () => {
    const p = await loadPage();
    p.w.confirm = () => false;
    p.d.getElementById('teamNameInput').value = 'Egal';
    await p.w.saveCurrentTeam();
    assert.equal(p.posted.length, 0);
    assert.deepEqual(p.deleted, []);
});

test('Ohne Namensänderung wird nicht gefragt und nichts gelöscht', async () => {
    const p = await loadPage();
    let asked = false;
    p.w.confirm = () => { asked = true; return true; };
    await p.w.saveCurrentTeam();
    assert.equal(asked, false);
    assert.equal(p.posted.at(-1).body.name, 'Test');
    assert.deepEqual(p.deleted, []);
});

// --- Konto löschen ---

test('Konto löschen: Menüpunkt öffnet den Dialog mit dem Namen, Abbrechen und Escape schließen ihn', async () => {
    const p = await loadPage();
    const modal = p.d.getElementById('deleteAccountModal');
    assert.equal(modal.classList.contains('hidden'), true);

    click(p.w, p.d.getElementById('userMenuButton'));
    click(p.w, p.d.getElementById('deleteAccountBtn'));
    assert.equal(modal.classList.contains('hidden'), false, 'Dialog offen');
    assert.equal(p.d.getElementById('userMenuList').classList.contains('hidden'), true, 'Menü schließt');
    assert.match(p.d.getElementById('deleteAccountName').textContent, /tester/);

    p.d.getElementById('deleteAccountPassword').value = 'geheim';
    p.d.dispatchEvent(new p.w.KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    assert.equal(modal.classList.contains('hidden'), true, 'Escape schließt');
    assert.equal(p.d.getElementById('deleteAccountPassword').value, '', 'Passwort wird verworfen');
    assert.equal(p.posted.length, 0, 'ohne Bestätigung wird nichts gesendet');
});

test('Konto löschen: falsches Passwort zeigt die Meldung des Servers und lässt den Dialog offen', async () => {
    const p = await loadPage();
    const requests = [];
    p.w.fetch = async (url, options = {}) => {
        requests.push({ url: String(url), options });
        return { ok: false, status: 403, json: async () => ({ error: 'Passwort falsch.' }) };
    };
    p.w.openDeleteAccount();
    p.d.getElementById('deleteAccountPassword').value = 'falsch';
    await p.w.handleDeleteAccount({ preventDefault() {} });

    assert.equal(requests.length, 1);
    assert.ok(requests[0].url.endsWith('auth.php?action=delete_account'));
    assert.equal(requests[0].options.method, 'POST');
    assert.deepEqual(JSON.parse(requests[0].options.body), { password: 'falsch' });
    const error = p.d.getElementById('deleteAccountError');
    assert.equal(error.classList.contains('hidden'), false);
    assert.equal(error.textContent, 'Passwort falsch.');
    assert.equal(p.d.getElementById('deleteAccountModal').classList.contains('hidden'), false, 'Dialog bleibt offen');
    assert.equal(p.d.getElementById('deleteAccountSubmit').disabled, false, 'erneuter Versuch möglich');
});

test('Konto löschen: nicht erreichbarer Server wird verständlich gemeldet', async () => {
    const p = await loadPage();
    p.w.fetch = async () => { throw new Error('offline'); };
    p.w.openDeleteAccount();
    p.d.getElementById('deleteAccountPassword').value = 'egal';
    await p.w.handleDeleteAccount({ preventDefault() {} });
    assert.match(p.d.getElementById('deleteAccountError').textContent, /nicht erreichbar/);
});

test('Über-Dialog: Menüpunkt öffnet ihn mit Logo, Escape und Schließen schließen ihn', async () => {
    const p = await loadPage();
    const modal = p.d.getElementById('aboutModal');
    assert.equal(modal.classList.contains('hidden'), true);
    click(p.w, p.d.getElementById('userMenuButton'));
    click(p.w, p.d.getElementById('aboutBtn'));
    assert.equal(modal.classList.contains('hidden'), false, 'Dialog offen');
    assert.equal(p.d.getElementById('userMenuList').classList.contains('hidden'), true, 'Menü schließt');
    assert.ok(modal.querySelector('img[src$="mm_logo.png"]'), 'media-matrix-Logo');
    const link = modal.querySelector('#aboutLogoLink');
    assert.equal(link.getAttribute('href'), 'https://www.media-matrix.de', 'Logo verlinkt auf die Webseite');
    assert.equal(link.getAttribute('target'), '_blank', 'öffnet in neuem Tab');
    assert.match(link.getAttribute('rel'), /noopener/, 'ohne Zugriff auf das Ursprungsfenster');
    assert.ok(link.contains(modal.querySelector('img[src$="mm_logo.png"]')), 'das Logo steckt im Link');
    assert.match(modal.textContent, /HoYoverse/);
    p.d.dispatchEvent(new p.w.KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    assert.equal(modal.classList.contains('hidden'), true, 'Escape schließt');
});

test('Die Web-Version im Über-Dialog stimmt mit dem obersten Web-Eintrag im Changelog überein', async () => {
    const changelog = fs.readFileSync(path.join(ROOT, 'CHANGELOG.md'), 'utf8');
    const expected = changelog.match(/^## Web (\d+\.\d+\.\d+)/m)[1];
    const p = await loadPage();
    assert.equal(p.d.getElementById('webVersion').textContent.trim(), `Web-Version ${expected}`);
});

test('Anmeldeseite hat die Überschrift in der Genshin-Schrift', async () => {
    const p = await loadPage({ loggedIn: false });
    const heading = p.d.querySelector('#authModal h1');
    assert.ok(heading, 'Überschrift vorhanden');
    assert.equal(heading.textContent.trim(), 'GENSHIN IMPACT Team & Build Manager');
    assert.ok(heading.classList.contains('genshin-title'), 'Genshin-Schrift');
    assert.equal(p.d.getElementById('authModal').classList.contains('hidden'), false, 'Anmeldedialog sichtbar');
});

test('Anmeldeseite: Überschrift steht über der Box, der Dialog bringt sein eigenes Hintergrundbild mit', async () => {
    const p = await loadPage({ loggedIn: false });
    const modal = p.d.getElementById('authModal');
    const heading = modal.querySelector('h1');
    const card = p.d.getElementById('authTitle').parentElement;
    assert.ok(!card.contains(heading), 'Überschrift steht nicht in der Box');
    assert.equal(heading.nextElementSibling, card, 'Box folgt direkt auf die Überschrift');
    assert.ok(heading.classList.contains('text-center'), 'zentriert');
    assert.match(modal.getAttribute('style'), /genshin-impact\.jpg/, 'Hintergrundbild');
});

test('Artefaktteile: Dropdown pro Slot, Teile der gewählten Sets zuerst, Off-Piece wählbar, Auswahl wird gespeichert', async () => {
    const artifacts = STAMMDATEN.artifacts.map((a, i) => ({ id: i + 1, name: a.name, bonus_2pc: a.bonus_2pc, bonus_4pc: a.bonus_4pc, pieces: a.pieces }));
    const teams = { Test: [{ character: CHARACTERS[0], saved: { level: 90, artifact: 'Abenteurer', artifact_2: 'Berserker' } }] };
    const { w, d, posted } = await loadPage({ artifacts, teams });
    w.toggleDetailView(0);

    const feder = d.getElementById('art_piece_Feder');
    const groups = [...feder.querySelectorAll('optgroup')];
    assert.equal(groups[0].label, 'Teile der gewählten Sets');
    assert.ok([...groups[0].children].some(o => o.value === 'Abenteurerschwanzfeder'));
    assert.equal(groups[0].children.length, 2);
    assert.ok([...groups[1].children].some(o => o.value === 'Zuflucht des Gladiators'), 'Off-Piece aus fremdem Set ist wählbar');
    assert.equal(d.getElementById('art_piece_Krone').querySelectorAll('option').length > 60, true);

    feder.value = 'Zuflucht des Gladiators';
    feder.dispatchEvent(new w.Event('change', { bubbles: true }));
    // Setwechsel baut die Dropdowns neu auf und behält die Auswahl
    w.updateSavedProp(0, 'artifact', 'Verbeugung des Gladiators');
    const neu = d.getElementById('art_piece_Feder');
    assert.equal(neu.value, 'Zuflucht des Gladiators');
    assert.ok([...neu.querySelector('optgroup').children].some(o => o.value === 'Zuflucht des Gladiators'), 'Teil steht jetzt bei den Teilen der gewählten Sets');

    await w.saveCurrentTeam();
    const sent = posted.find(p => p.url.includes('teams.php'));
    assert.equal(sent.body.members[0].artifact_stats.Feder.piece, 'Zuflucht des Gladiators');
});
