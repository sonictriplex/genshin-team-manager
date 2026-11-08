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
async function loadPage({ loggedIn = true, openTeam = true } = {}) {
    const posted = [];
    const deleted = [];
    const routes = {
        'auth.php?action=status': loggedIn ? { logged_in: true, username: 'tester', user_id: 1 } : { logged_in: false },
        'characters.php': CHARACTERS,
        'weapons.php': [],
        'artifacts.php': [],
        'teams.php': { Test: CHARACTERS.slice(0, 3).map(c => ({ character: c, saved: { level: 90 } })) },
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
