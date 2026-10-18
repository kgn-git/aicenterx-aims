"""Film-specific checks for the Customer Service Copilot film (issue #3, phase 2).

Usage:  python test/service-copilot_test.py [--write-lines]

The shared controls and layout test is test/film_controls_test.py; this file adds what only this film's script asks for:
  1. lines: the 28 on-screen lines in simulation/service-copilot/copilot-lines.json match the approved script's shot table
     verbatim, and pass the script's counting rules (words <= 14 per line, Flesch-Kincaid grade <= 8, reading pace <= 5.0
     words per second, film budget <= 300 words). --write-lines regenerates the JSON from the script.
  2. film text: every scene in the film (window.FILM_CONFIG) has the script's start, dur, setting, scene name, headline and
     support line; the corner label and accent are the script's; no source line, note, chip or card is added; no record id
     appears on screen.
  3. clearance: >= 0.6 m from every collider and person (FILM.clearance) and >= 0.9 m from every visible head, at 0.1 s steps.
  4. faithful to status: guards in test are never shown solid; the web-chat filter is absent until 4.2; red rings only appear
     in beat 3; the withdrawn tile is gone after the nightly rebuild; the open pips stay lit.
  5. fallback: with three.js blocked, the page shows the open headline, the WebGL note, the colour legend and every scene.
Prints a JSON report; exit code 1 on any failure.
"""
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / 'simulation' / 'service-copilot'
SCRIPT = DIR / 'Customer Service Copilot - Script and Protocols.md'
FILM = DIR / 'Customer Service Copilot.html'
LINES = DIR / 'copilot-lines.json'
GL_ARGS = ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
LIMIT_WORDS, LIMIT_FK, LIMIT_PACE, BUDGET = 14, 8.0, 5.0, 300
SCENE_NAMES = ['Introduction', 'The situation \u2014 The call', 'The situation \u2014 The search', 'The AI at work \u2014 Finding the policy',
               'The AI at work \u2014 The cited answer', 'The AI at work \u2014 The agent decides', 'What can go wrong \u2014 The old fee list',
               'What can go wrong \u2014 The hidden trick', 'What can go wrong \u2014 The leak between teams', 'How it is kept safe \u2014 The nightly rebuild',
               'How it is kept safe \u2014 Still being tested', 'How it is kept safe \u2014 Checking samples', 'How it is kept safe \u2014 The next gate', 'Close']
RECORD_ID = re.compile(r'\b(?:r|n|d|e|w\d-o)\d+\b|\bA\.\d+\b|\bmd-[a-z]+|\bds-[a-z]+|\bbm-q\d', re.I)


# ---------------------------------------------------------------- the script's counting rules (Part 1, "Word count and readability")
def words(s):
    return [w for w in s.split() if re.search(r'[A-Za-z0-9]', w)]


def syllables(w):
    return max(1, len(re.findall(r'[aeiouy]+', w.lower())))


def fk(s):
    ws = words(s)
    sentences = max(1, len(re.findall(r'[.!?]', s)))
    return 0.39 * len(ws) / sentences + 11.8 * sum(syllables(w) for w in ws) / len(ws) - 15.59


def script_shots():
    """Rows of the Part 1 shot table: id, start, dur, beat, setting, headline, support line."""
    rows = []
    for line in SCRIPT.read_text(encoding='utf-8').splitlines():
        if re.match(r'^\| (Open|Close|\d\.\d) \|', line):
            c = [x.strip() for x in line.strip().strip('|').split(' | ')]
            if len(c) != 10 or not re.fullmatch(r'\d+(\.\d+)?', c[1]):
                continue  # the word-count table also starts its rows with the shot id
            rows.append({'id': c[0], 'start': float(c[1]), 'dur': float(c[2]), 'beat': c[3], 'setting': c[4], 'head': c[7], 'sup': c[8]})
    return rows


def build_lines(rows):
    out, total = [], 0
    for r in rows:
        for el in ('head', 'sup'):
            t = r[el]
            n = len(words(t))
            total += n
            out.append({'shot': r['id'], 'element': 'headline' if el == 'head' else 'support', 'text': t, 'words': n, 'limit': LIMIT_WORDS, 'fk': round(fk(t), 1)})
        pace = (len(words(r['head'])) + len(words(r['sup']))) / r['dur']
        out[-1]['pace'] = round(pace, 2)
        out[-1]['dur'] = r['dur']
    return {'source': SCRIPT.name, 'rules': {'words': 'whitespace tokens containing a letter or digit', 'fk': '0.39*words/sentences + 11.8*syllables/words - 15.59; syllables = [aeiouy]+ groups, min 1; sentences at . ! ?',
            'limits': {'words_per_line': LIMIT_WORDS, 'fk_max': LIMIT_FK, 'pace_max_wps': LIMIT_PACE, 'film_budget': BUDGET}},
            'lines': out, 'total_words': total}


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    checks = {}

    def check(name, ok, detail=''):
        checks[name] = {'ok': bool(ok), 'detail': detail if isinstance(detail, str) else json.dumps(detail, ensure_ascii=False)[:1500]}

    rows = script_shots()
    check('script: 14 shots parsed from the Part 1 table, contiguous 0-60 s', len(rows) == 14 and all(abs(r['start'] - (rows[i - 1]['start'] + rows[i - 1]['dur'] if i else 0)) < 1e-6 for i, r in enumerate(rows))
          and abs(rows[-1]['start'] + rows[-1]['dur'] - 60) < 1e-6, [(r['id'], r['start'], r['dur']) for r in rows])
    want = build_lines(rows)
    if '--write-lines' in sys.argv:
        LINES.write_text(json.dumps(want, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')

    # ------------------------------------------------------------ 1. the lines file
    have = json.loads(LINES.read_text(encoding='utf-8')) if LINES.exists() else None
    check('lines: copilot-lines.json exists and matches the script verbatim (text, counts, grades, pace)', have == want, 'regenerate with --write-lines' if have != want else f'{len(want["lines"])} lines')
    L = want['lines']
    over = [(x['shot'], x['element'], x['words']) for x in L if x['words'] > LIMIT_WORDS]
    hard = [(x['shot'], x['element'], x['fk']) for x in L if x['fk'] > LIMIT_FK]
    fast = [(x['shot'], x['pace']) for x in L if x.get('pace', 0) > LIMIT_PACE + 1e-9]
    check(f'lines: 28 lines, each <= {LIMIT_WORDS} words', len(L) == 28 and not over, over or f'max {max(x["words"] for x in L)}')
    check(f'lines: Flesch-Kincaid grade <= {LIMIT_FK:g} on every line', not hard, hard or f'max {max(x["fk"] for x in L)}')
    check(f'lines: reading pace <= {LIMIT_PACE:g} words/s on every shot', not fast, fast or f'max {max(x.get("pace", 0) for x in L)}')
    check(f'lines: film budget <= {BUDGET} words (script states 277)', want['total_words'] <= BUDGET and want['total_words'] == 277, f'total {want["total_words"]}')

    with sync_playwright() as pw:
        br = pw.chromium.launch(args=GL_ARGS)
        pg = br.new_page(viewport={'width': 1280, 'height': 720})
        errors = []
        pg.on('pageerror', lambda e: errors.append(f'pageerror: {e}'))
        pg.on('console', lambda m: errors.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
        pg.goto(FILM.as_uri(), wait_until='load', timeout=60000)
        pg.wait_for_function('window.FILM && window.FILM.ready === true', timeout=60000)
        pg.evaluate('FILM.pause()')
        cfg = pg.evaluate('window.FILM_CONFIG')

        # ------------------------------------------------------------ 2. the film's text against the script
        beats = cfg['beats']
        diffs = []
        for i, (b, r) in enumerate(zip(beats, rows)):
            d = {}
            for key, val in (('start', r['start']), ('dur', r['dur']), ('setting', r['setting']), ('head', r['head']), ('sup', r['sup']), ('name', SCENE_NAMES[i])):
                if (abs(b.get(key, -1) - val) > 1e-6) if isinstance(val, float) else b.get(key) != val:
                    d[key] = (b.get(key), val)
            want_beat = 0 if r['id'] in ('Open', 'Close') else int(r['id'][0])
            if b['beat'] != want_beat:
                d['beat'] = (b['beat'], want_beat)
            if d:
                diffs.append({'shot': r['id'], 'diff': d})
        check('film text: 14 scenes with the script\'s start, dur, setting, scene name, headline and support line', len(beats) == 14 and not diffs, diffs or '14 scenes')
        check('film text: corner label "Customer Service Copilot \u00b7 Pilot"; accent Customer Ops blue on every beat, neutral cards',
              cfg['initiative'] == 'Customer Service Copilot \u00b7 Pilot' and all(cfg['accent'][str(n)].lower() == '#3d7cc9' for n in (1, 2, 3, 4)) and cfg['accent']['0'].lower() == '#e8e6e1',
              {'initiative': cfg['initiative'], 'accent': cfg['accent']})
        extra = [(b['name'], k) for b in beats for k in ('source', 'note', 'chips', 'cards', 'stages', 'foot') if b.get(k)]
        check('film text: no source line, note, chip or card beyond the script', not extra, extra or 'none')
        onscreen = [cfg['initiative']] + [b[k] for b in beats for k in ('setting', 'head', 'sup', 'name')]
        ids = [t for t in onscreen if RECORD_ID.search(t)]
        check('film text: no record id on screen', not ids, ids or 'none')
        shown = []
        for b in beats:
            pg.evaluate('t => FILM.seek(t)', b['start'] + b['dur'] / 2)
            o = pg.evaluate("() => ({ head: document.getElementById('head').textContent, sup: document.getElementById('sup').textContent, blab: document.getElementById('blab').textContent, note: document.getElementById('note').textContent, sname: document.getElementById('sname').textContent })")
            if o['head'] != b['head'] or o['sup'] != b['sup'] or o['blab'] or o['note'] or o['sname'] != b['setting']:
                shown.append({'scene': b['name'], 'overlay': o})
        check('overlay: each scene shows exactly its headline, support line and setting, with no source line or note', not shown, shown or '14 scenes')

        # ------------------------------------------------------------ 3. clearance (colliders and people >= minClearance; heads >= 0.9 m)
        cl = pg.evaluate("""() => { let worst = null, head = null;
          for (let t = 0; t < FILM.duration; t += 0.1) { const c = FILM.clearance(t); if (!worst || c.d < worst.d) worst = c;
            const cam = FILM_DEBUG.camera(); for (const h of FILM_DEBUG.heads()) { const d = Math.hypot(h[0]-cam[0], h[1]-cam[1], h[2]-cam[2]); if (!head || d < head.d) head = { t, d }; } }
          return { coll: worst, head }; }""")
        check(f'clearance: >= {cfg["minClearance"]} m from every collider and person (0.1 s steps)', cfg['minClearance'] >= 0.6 and cl['coll']['d'] >= cfg['minClearance'], cl['coll'])
        check('clearance: >= 0.9 m from every visible head (0.1 s steps)', cl['head']['d'] >= 0.9, cl['head'])

        # ------------------------------------------------------------ 4. faithful to status (world state at sampled times)
        def flags(t):
            return pg.evaluate('t => { FILM.clearance(t); return FILM_DEBUG.flags(); }', t)
        bad = []
        red_outside = []
        for k in range(0, 600, 2):
            t = k / 10
            f = flags(t)
            if not f['voiceRing'] and f['agent']:
                bad.append((t, 'voice filter ring missing'))
            if t < 44 and (f['chatRing'] or not f['chatBracket']):
                bad.append((t, 'web-chat filter shown before 4.2'))
            if t >= 44 and (not f['chatRing'] or f['chatBracket']):
                bad.append((t, 'web-chat ring (in test) missing from 4.2'))
            if t >= 44 and f['amberTile']:
                bad.append((t, 'withdrawn tile back after the rebuild'))
            if (f['bubbleRed'] or f['panelRed']) and not (25 <= t < 40):
                red_outside.append(t)
        check('status: the voice filter ring is always shown dashed; the web-chat channel has an empty bracket until 4.2, then a dashed ring', not [b for b in bad if 'filter' in b[1] or 'ring' in b[1]], bad[:8] or 'ok')
        check('status: red rings (a fault reached someone) appear only in beat 3', not red_outside, red_outside[:10] or 'ok')
        moments = {
            '2.3 green-edged source card; customer words cleared under the lock': (24.4, lambda f: f['sourceCard'] and f['cardEdge'] == '#3fa34d' and f['lock'] and not f['words'] and f['bubbleGreen']),
            '3.1 amber-edged source card; red ring under the customer': (29.6, lambda f: f['sourceCard'] and f['cardEdge'] == '#e9a23b' and f['bubbleRed'] and f['amberTile']),
            '3.2 hooked block in the chat pipe; keyhole card and red ring on the panel': (34.6, lambda f: f['keyhole'] and f['panelRed']),
            '3.2 the hooked block flows through the unfiltered chat pipe': (32.6, lambda f: f['hook'] and f['chatBracket'] and not f['chatRing']),
            '3.3 violet title strip and red ring on the panel': (39.6, lambda f: f['violetStrip'] and f['panelRed']),
            '4.1 the withdrawn tile drops out of the rebuilt library': (43.5, lambda f: not f['amberTile'] and not f['agent']),
            '4.2 hooked block held at the dashed ring; the leak pip still lit': (45.5, lambda f: f['hook'] and f['chatRing'] and f['openPip']),
            '4.4 green ring around the pilot pod; two open pips on the gate': (55.0, lambda f: f['sealRing'] and f['gatePips']),
            'Close: green-edged source, green rim, words cleared, leak pip still lit': (58.0, lambda f: f['cardEdge'] == '#3fa34d' and f['bubbleGreen'] and f['lock'] and not f['words'] and f['openPip']),
        }
        miss = {}
        for name, (t, ok) in moments.items():
            f = flags(t)
            if not ok(f):
                miss[name] = f
        check('status: each staged moment shows what the shot table describes', not miss, miss or f'{len(moments)} moments')
        check('status: the withdrawn tile is gone after the nightly rebuild', not [b for b in bad if 'withdrawn' in b[1]], 'ok')
        check('no console errors or warnings, no page errors', not errors, errors[:10] or 'none')
        br.close()

        # ------------------------------------------------------------ 5. fallback with three.js blocked
        br = pw.chromium.launch(args=GL_ARGS)
        fp = br.new_page(viewport={'width': 1280, 'height': 720})
        fp.route(re.compile(r'three(\.min)?\.js'), lambda r: r.abort())
        fp.goto(FILM.as_uri(), wait_until='load', timeout=60000)
        fp.wait_for_function('window.FILM && window.FILM.ready === true', timeout=45000)
        fb = fp.evaluate("""() => { const f = document.getElementById('fallback'); return { title: document.getElementById('fbtitle').textContent,
            paras: Array.from(f.querySelectorAll(':scope > p')).map(p => p.textContent), items: Array.from(document.querySelectorAll('#fblist li')).map(li => li.textContent),
            text: f.textContent }; }""")
        br.close()
        legend_ok = len(fb['paras']) == 2 and fb['paras'][0].startswith('This film needs 3D graphics (WebGL).') and all(w in fb['paras'][1] for w in ('green', 'amber', 'red ring', 'Violet', 'ice-white', 'dashed', 'empty bracket', 'red open pip', 'lock'))
        items_ok = len(fb['items']) == 14 and all(r['head'] in it and r['sup'] in it and SCENE_NAMES[i] in it for i, (r, it) in enumerate(zip(rows, fb['items'])))
        check('fallback: the open headline as title, then the WebGL note, the colour legend and every scene with its headline and support line',
              fb['title'] == rows[0]['head'] and legend_ok and items_ok, {'title': fb['title'], 'paras': [p[:80] for p in fb['paras']], 'items': len(fb['items'])})
        check('fallback: no record id and no times', not RECORD_ID.search(fb['text']) and not re.search(r'\b\d+(\.\d+)? ?s\b|\d:\d\d', fb['text']), 'ok')

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
