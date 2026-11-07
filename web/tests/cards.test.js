// Tests für das Verschieben der Teamkarten in web/index.html (Pfeile und Drag & Drop).
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

/** Lädt die Seite mit einem Team aus Furina, Nilou und Barbara (in dieser Reihenfolge). */
async function loadPage() {
    const posted = [];
    const routes = {
        'auth.php?action=status': { logged_in: true, username: 'tester', user_id: 1 },
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
    return { w, d, posted, cards, handles, order, freeSlot, button, drag };
}

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
