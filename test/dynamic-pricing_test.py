"""Film-specific checks for simulation/dynamic-pricing/Dynamic Pricing.html (issue #9, phase 2).

Usage:  python test/dynamic-pricing_test.py [--write-lines]

The shared test (test/film_controls_test.py) covers controls, layout, determinism, clearance and the fallback. This test checks
the film against its approved script, "Dynamic Pricing - Script and Protocols.md":
  1. script: the Part 1 shot table parses into 12 contiguous shots (59 s); its word-count table states 219 caption words, a
     highest grade of 7.8 and a highest pace of 4.4 words/s, and 58 source-line words.
  2. lines: the 24 caption lines and the 10 source lines in "simulation/dynamic-pricing/Dynamic Pricing - lines.json" match the
     shot table and the "Source lines" table verbatim and pass the script's counting rules (headline <= 14 words, support line
     <= 18 words and <= 14 as the other films apply, note <= 10, source line <= 10 words, Flesch-Kincaid grade <= 8 on every
     caption line, pace <= 5.5 words/s, <= 220 caption words). --write-lines regenerates the JSON.
  3. film text: every scene in window.FILM_CONFIG has the script's start, dur, beat, setting, headline, support line, note, source
     line and nav label; the scene name is "<beat> - <setting>" (cards: "Open card" / "Close card"); the initiative label is
     "Dynamic Pricing . a proposal, nothing built"; accents are the template defaults; the fallback title is the script's; no chip,
     card, roadmap or footer; a note on shot 3.1 only; no digit and no record id on screen; the overlay shows exactly that text.
  4. runtime: 59 s; beats 10 / 11 / 15 / 15 s; cards 4 s each.
  5. staged world (read through the film's debug hook window.FILM_DP after FILM.signature(t) has staged that exact frame): one set
     per shot; the canvas panels light one after another on the open card, with question tokens on five of them; the price list is
     worked row by row; the board flow is drawn, then the dial sweeps along the curve and back and stops nowhere; the fork and its
     token appear in 2.2; in 3.1 the second tag grows and only then gets a dashed red outline; in 3.2 the reason slot stays empty,
     the staff member looks back to the call and the red outline forms at 2.5 s; in 3.3 prices go into the shared tool and come
     back, the lines rise together and the red outline wraps them last; at intake the printout slides across and the question
     list stays empty; in 4.2 the three questions settle on the question list while the register keeps only its empty line; in
     4.3 the tile waits, the tick lands, the tile moves to the tag and nothing flows past the gate; the close shows the gate.
  6. colour rules: red appears only in beat 3 (25-40 s), only as dashed outlines, and never pulses.
  7. clearance: >= 0.8 m from every collider and figure (CONFIG.minClearance), sampled every 0.1 s.
  8. fallback (three.js blocked): the script's fallback title, the WebGL note and every shot as "<beat> - <setting>" with its
     headline, support line and note; no shot numbers and no times.
Prints a JSON report; exit code 1 on any failure.
"""
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / 'simulation' / 'dynamic-pricing'
FILM = DIR / 'Dynamic Pricing.html'
SCRIPT = DIR / 'Dynamic Pricing - Script and Protocols.md'
LINES = DIR / 'Dynamic Pricing - lines.json'
GL_ARGS = ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
ACCENT = {0: '#e8e6e1', 1: '#2a9d8f', 2: '#4a86d8', 3: '#d84a3a', 4: '#3fa34d'}
BEATS = {'Open card': 0, 'The situation': 1, 'The AI at work': 2, 'What can go wrong': 3, 'How it is kept safe': 4, 'Close card': 0}
LIMITS = {'headline': 14, 'support': 18, 'note': 10}
LIMIT_SOURCE, LIMIT_FK, LIMIT_PACE, BUDGET = 10, 8.0, 5.5, 220
INITIATIVE = 'Dynamic Pricing \u00b7 a proposal, nothing built'
FALLBACK_TITLE = 'Dynamic Pricing, as it is proposed.'
WEBGL_NOTE = 'This film needs 3D graphics (WebGL). Your browser could not start it. Here is the film in words.'
RECORD_ID = re.compile(r'\b(?:w\d-o\d|bm-[a-z]+|d\d|r\d+|md-[a-z]+|ds-[a-z]+)\b|\bA\.\d+\b', re.I)


# ---------------------------------------------------------------- the script's counting rules (Part 1, "Word count and readability")
def words(s):
    return [w for w in s.split() if re.search(r'[A-Za-z0-9]', w)]


def fk(s):
    ws = words(s)
    sentences = max(1, len(re.findall(r'[.!?]', s)))
    syl = sum(max(1, len(re.findall(r'[aeiouy]+', w.lower()))) for w in ws)
    return 0.39 * len(ws) / sentences + 11.8 * syl / len(ws) - 15.59


def cell(c):
    c = c.strip()
    return '' if c in ('—', '-') else c


def shot_table():
    """Rows of the Part 1 shot table (13 columns): id, start, dur, beat, setting, source, ..., headline, support, note, nav."""
    rows = []
    for line in SCRIPT.read_text(encoding='utf-8').splitlines():
        if not re.match(r'^\| (0|C|\d\.\d) \| \d+ \| \d+ \| ', line):
            continue
        c = [x.strip() for x in line.strip().strip('|').split(' | ')]
        if len(c) != 13:
            raise ValueError(f'shot row with {len(c)} columns: {line[:80]}')
        rows.append({'id': c[0], 'start': float(c[1]), 'dur': float(c[2]), 'beat': BEATS[c[3]], 'beatName': c[3], 'setting': c[4],
                     'source': cell(c[5]), 'head': c[8], 'sup': cell(c[9]), 'note': cell(c[10]), 'nav': c[11]})
    return rows


def source_table():
    """Part 1 "Source lines" table: | shot | `source line` | record it names |."""
    out = {}
    for line in SCRIPT.read_text(encoding='utf-8').splitlines():
        m = re.match(r'^\| (\d\.\d) \| `([^`]+)` \| [^|]+\|\s*$', line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def script_totals():
    text = SCRIPT.read_text(encoding='utf-8')
    m = re.search(r'^\| \*\*Total\*\* \| 24 lines \| \*\*(\d+)\*\* \| [^|]+\| max \*\*([\d.]+)\*\* [^|]+\| max \*\*([\d.]+)\*\*', text, re.M)
    s = re.search(r'^\| \*\*Total\*\* \| 10 lines \| \*\*(\d+)\*\* \|', text, re.M)
    return {'words': int(m.group(1)), 'maxFk': float(m.group(2)), 'maxPace': float(m.group(3)), 'sourceWords': int(s.group(1))}


def build_lines(rows, sources):
    lines, pace = [], []
    for r in rows:
        for el, key in (('headline', 'head'), ('support', 'sup'), ('note', 'note')):
            t = r[key]
            if t:
                lines.append({'shot': r['id'], 'element': el, 'text': t, 'words': len(words(t)), 'limit': LIMITS[el], 'fk': round(fk(t), 1)})
        pace.append({'shot': r['id'], 'dur': r['dur'], 'wordsPerSecond': round((len(words(r['head'])) + len(words(r['sup']))) / r['dur'], 2)})
    src = [{'shot': r['id'], 'text': sources[r['id']], 'words': len(words(sources[r['id']])), 'limit': LIMIT_SOURCE, 'fk': round(fk(sources[r['id']]), 1)}
           for r in rows if r['id'] in sources]
    return {'film': FILM.name, 'script': SCRIPT.name,
            'rules': {'words': 'whitespace tokens containing a letter or digit', 'fk': '0.39*words/sentences + 11.8*syllables/words - 15.59; syllables = [aeiouy]+ groups, min 1; sentences at . ! ?',
                      'limits': {'headline': LIMITS['headline'], 'support': LIMITS['support'], 'note': LIMITS['note'], 'source': LIMIT_SOURCE, 'fk_max': LIMIT_FK, 'pace_max_wps': LIMIT_PACE, 'film_budget': BUDGET},
                      'note': 'source lines are record citations, counted apart from the caption budget and reported, not enforced, on grade (script Open points 8 and 9)'},
            'lines': lines, 'pace': pace, 'total_words': sum(x['words'] for x in lines), 'max_fk': max(x['fk'] for x in lines), 'max_pace': max(x['wordsPerSecond'] for x in pace),
            'source_lines': src, 'source_words': sum(x['words'] for x in src)}


# world state at film time t, read through the film's debug hook after FILM.signature(t) has staged that exact frame
STATE_JS = """t => { FILM.pause(); FILM.signature(t); const o = window.FILM_DP, w = s => JSON.parse(JSON.stringify(s.want));
  return { sets: Object.keys(o.sets).filter(k => o.sets[k].visible), red: o.st.red,
    canvas: w(o.canvas), ctok: o.ctok.filter(q => q.g.visible).length, list: w(o.list), office: w(o.offWall), board: w(o.board),
    stok: o.stok.visible, ftok: o.ftok.visible, ftokY: o.ftok.position.y, people12: [o.lead.visible, o.spon.visible, o.own1.visible],
    d: [o.d1.visible, o.d2.visible, o.d3.visible], tag1: o.c1.tag.scale.y, tag2: o.c2.tag.scale.y, red31: o.red31.visible, red31s: o.red31.scale.x,
    agent: w(o.agentScr), staffYaw: o.staff.head.rotation.y, market: w(o.market), pk: o.pk.map(p => p.visible), buyerYaw: o.buyer.head.rotation.y,
    paperX: o.paper.mesh.position.x, split: w(o.split), pown: w(o.pown), tile: o.tile.visible, tileX: o.tile.position.x,
    lpk: o.lpk.filter(p => p.visible && p.scale.x > 0.002).map(p => p.position.z), lamp: '#' + o.lamp.material.emissive.getHexString() }; }"""


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    checks = {}

    def check(name, ok, detail=''):
        checks[name] = {'ok': bool(ok), 'detail': detail if isinstance(detail, str) else json.dumps(detail, ensure_ascii=False)[:1500]}

    # ------------------------------------------------------------ 1. the script
    rows = shot_table()
    contiguous = all(abs(r['start'] - (rows[i - 1]['start'] + rows[i - 1]['dur'] if i else 0)) < 1e-6 for i, r in enumerate(rows))
    check('script: 12 shots parsed from the Part 1 table, contiguous 0-59 s', len(rows) == 12 and contiguous and rows[-1]['start'] + rows[-1]['dur'] == 59,
          [(r['id'], r['start'], r['dur']) for r in rows])
    sources = source_table()
    totals = script_totals()
    want = build_lines(rows, sources)
    if '--write-lines' in sys.argv:
        LINES.write_text(json.dumps(want, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')

    # ------------------------------------------------------------ 2. the lines file and the counting rules
    have = json.loads(LINES.read_text(encoding='utf-8')) if LINES.exists() else None
    check('lines: "Dynamic Pricing - lines.json" exists and matches the script verbatim (text, counts, grades, pace)', have == want,
          'regenerate with --write-lines' if have != want else f'{len(want["lines"])} caption lines, {len(want["source_lines"])} source lines')
    L = want['lines']
    over = [(x['shot'], x['element'], x['words']) for x in L if x['words'] > x['limit'] or (x['element'] == 'support' and x['words'] > 14)]
    hard = [(x['shot'], x['element'], x['fk']) for x in L if x['fk'] > LIMIT_FK]
    fast = [(x['shot'], x['wordsPerSecond']) for x in want['pace'] if x['wordsPerSecond'] > LIMIT_PACE + 1e-9]
    check('lines: 24 caption lines within their limits (headline 14, support 18 and 14, note 10 words)', len(L) == 24 and not over, over or f'{len(L)} lines')
    check(f'lines: Flesch-Kincaid grade <= {LIMIT_FK:g} on every caption line; highest as the script states', not hard and want['max_fk'] == totals['maxFk'],
          hard or f'max {want["max_fk"]} (script {totals["maxFk"]})')
    check(f'lines: pace <= {LIMIT_PACE:g} words/s on every shot; highest as the script states', not fast and want['max_pace'] == totals['maxPace'],
          fast or f'max {want["max_pace"]} (script {totals["maxPace"]})')
    check(f'lines: caption words <= {BUDGET} and equal to the script total', want['total_words'] <= BUDGET and want['total_words'] == totals['words'],
          f'{want["total_words"]} (script {totals["words"]})')
    SL = want['source_lines']
    bad_src = [(x['shot'], x['words']) for x in SL if x['words'] > LIMIT_SOURCE or re.search(r'\d', x['text']) or RECORD_ID.search(x['text'])]
    check('source lines: one per beat shot (10), each <= 10 words, no digit, no record id; total as the script states',
          [x['shot'] for x in SL] == [r['id'] for r in rows if r['beat']] and not bad_src and want['source_words'] == totals['sourceWords'],
          bad_src or f'{len(SL)} lines, {want["source_words"]} words (script {totals["sourceWords"]})')

    errors = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=GL_ARGS)
        pg = br.new_page(viewport={'width': 1280, 'height': 720})
        pg.on('console', lambda m: errors.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
        pg.on('pageerror', lambda e: errors.append(f'pageerror: {e}'))
        pg.goto(FILM.as_uri(), wait_until='load', timeout=60000)
        pg.wait_for_function('window.FILM && window.FILM.ready === true', timeout=60000)
        pg.evaluate('FILM.pause()')
        cfg = pg.evaluate('window.FILM_CONFIG')
        beats = cfg['beats']

        # ------------------------------------------------------------ 3. the film's text against the script
        diffs = []
        for r, b in zip(rows, beats):
            name = (f'{r["beatName"]} \u2014 {r["setting"]}')
            wantb = {'start': r['start'], 'dur': r['dur'], 'beat': r['beat'], 'setting': r['setting'], 'head': r['head'], 'sup': r['sup'], 'note': r['note'],
                     'source': r['source'], 'nav': r['nav'], 'name': name, 'accent': ACCENT[r['beat']]}
            got = {'start': b['start'], 'dur': b['dur'], 'beat': b['beat'], 'setting': b['setting'], 'head': b['head'], 'sup': b.get('sup', ''), 'note': b.get('note', ''),
                   'source': b.get('source', ''), 'nav': b.get('nav', ''), 'name': b['name'], 'accent': cfg['accent'][str(b['beat'])].lower()}
            d = {k: (got[k], v) for k, v in wantb.items() if got[k] != v}
            if d:
                diffs.append({'shot': r['id'], 'diff': d})
        check('film text: 12 scenes with the script\'s start, dur, beat, setting, headline, support line, note, source line, nav label, name and accent',
              len(beats) == len(rows) == 12 and not diffs, diffs or '12 scenes')
        check('film text: initiative label top right, template-default accents, the script\'s fallback title',
              cfg['initiative'] == INITIATIVE and cfg['fallbackTitle'] == FALLBACK_TITLE and {str(k): v for k, v in ACCENT.items()} == {k: v.lower() for k, v in cfg['accent'].items()},
              {'initiative': cfg['initiative'], 'fallbackTitle': cfg['fallbackTitle'], 'accent': cfg['accent']})
        extra = [(b['name'], k) for b in beats for k in ('chips', 'cards', 'stages', 'foot') if b.get(k)]
        notes = [b['name'] for b in beats if b.get('note')]
        check('film text: no chips, cards, roadmap or footer; a note on shot 3.1 only', not extra and notes == [beats[5]['name']], {'extra': extra, 'notes': notes})
        onscreen = [cfg['initiative']] + [b.get(k, '') for b in beats for k in ('setting', 'head', 'sup', 'note', 'source', 'nav')]
        bad = [t for t in onscreen if re.search(r'\d', t) or RECORD_ID.search(t)]
        check('film text: no digit and no record id anywhere on screen', not bad, bad or 'none')
        shown = []
        for b in beats:
            pg.evaluate('t => FILM.seek(t)', b['start'] + b['dur'] / 2)
            o = pg.evaluate("""() => ({ head: document.getElementById('head').textContent, sup: document.getElementById('sup').textContent, blab: document.getElementById('blab').textContent,
                note: document.getElementById('note').textContent, sname: document.getElementById('sname').textContent, sidx: document.getElementById('sidx').textContent,
                bnum: document.getElementById('bnum').textContent })""")
            if (o['head'] != b['head'] or o['sup'] != b.get('sup', '') or o['blab'] != (b.get('source', '') if b['beat'] else '') or o['note'] != b.get('note', '')
                    or o['sname'] != b['setting'] or o['sidx'] != INITIATIVE or o['bnum'] != (str(b['beat']) if b['beat'] else '')):
                shown.append({'scene': b['name'], 'overlay': o})
        check('overlay: each scene shows exactly its setting, initiative label, beat numeral, source line, headline, support line and note', not shown, shown or '12 scenes')

        # ------------------------------------------------------------ 4. runtime
        per_beat = [sum(b['dur'] for b in beats if b['beat'] == n) for n in (1, 2, 3, 4)]
        check('runtime: 59 s; beats 10 / 11 / 15 / 15 s (51 s); cards 4 s each', cfg['duration'] == 59 and per_beat == [10, 11, 15, 15] and beats[0]['dur'] == 4 and beats[-1]['dur'] == 4,
              f'film {cfg["duration"]} s, beats {per_beat}')

        # ------------------------------------------------------------ 5. the staged world at the script's local times
        S = lambda t: pg.evaluate(STATE_JS, t)
        exp = []

        def at(t, label, ok, detail=None):
            exp.append((round(t, 2), label, bool(ok)) + ((detail,) if detail is not None and not ok else ()))
        sets = ['meet', 'off', 'meet', 'meet', 'meet', 'meet', 'meet', 'meet', 'gov', 'gov', 'plan', 'off']
        for b, s in zip(beats, sets):
            st = S(b['start'] + b['dur'] / 2)
            at(b['start'] + b['dur'] / 2, f'{b["nav"]}: set {s} alone on screen', st['sets'] == [s], st['sets'])
        s0, s1 = S(0.6), S(3.9); at(3.9, 'open: the canvas panels light one after another; question tokens on five of them',
                                    0 < s0['canvas']['on'] < 3 and s1['canvas']['on'] == 7 and s1['ctok'] == 5 and s0['ctok'] < 5, [s0['canvas'], s1['ctok']])
        s0, s1 = S(4.3), S(8.7); at(8.7, '1.1: the price list is worked row by row (none checked, then all seven)', s0['list']['lit'] == 0 and s1['list']['lit'] == 7, [s0['list'], s1['list']])
        s0, s1 = S(5.0), S(7.0); at(7.0, '1.1: demand keeps moving on the wall screen (no gate on it yet)', s0['office']['ph'] != s1['office']['ph'] and not s1['office']['close'], [s0['office'], s1['office']])
        s = S(11.0); at(11.0, '1.2: a lead at the canvas and two seated figures; the value panel is the one pointed at', s['people12'] == [True, True, True] and s['canvas']['hi'] == 1)
        s0, s1 = S(14.2), S(17.1); at(17.1, '2.1: the flow is drawn left to right (0.3-3.0 s); the socket carries a question token',
                                      s0['board']['d'] == 0 and s1['board']['d'] == 1 and s1['stok'] and s1['board']['nd'] == -1, [s0['board'], s1['board']])
        nds = [S(14 + 3.5 + k * 0.07)['board']['nd'] for k in range(35)]   # 0.07 s steps, so no two samples sit symmetric about a turn
        still = [k for k in range(1, len(nds)) if abs(nds[k] - nds[k - 1]) < 1e-6]
        at(20.0, '2.1: the dial sweeps along the curve and back (3.5-5.0 s) and stops nowhere', not still and min(nds[:22]) < 0.05 and max(nds[:22]) > 0.95 and nds[21] < 0.05, nds)
        s0, s1, s2 = S(20.2), S(21.0), S(22.5)
        at(22.5, '2.2: the fork appears; the large question token rises at it; no dial on the curve', s0['board']['fk'] == 0 and s2['board']['fk'] == 1 and s2['ftok'] and s1['ftokY'] < s2['ftokY'] and s2['board']['nd'] == -1)
        s = S(25.5); at(25.5, '3.1: two customers, same tag height; no red yet', s['d'] == [True, False, False] and s['tag1'] == 1 and s['tag2'] == 1 and not s['red31'] and not s['red'])
        s = S(27.6); at(27.6, '3.1: her tag has grown (1.5-3.0 s), still no red outline', s['tag2'] > 1.3 and not s['red31'])
        s = S(28.6); at(28.6, '3.1: the taller tag carries a dashed red outline', s['tag2'] == 1.6 and s['tag1'] == 1 and s['red31'] and s['red'])
        s = S(30.5); at(30.5, '3.2: no reason slot yet; no red on the agent screen', s['d'] == [True, True, False] and s['agent']['slot'] == 0 and s['agent']['red'] == 0)
        s = S(32.0); at(32.0, '3.2: the reason slot is an empty grey box; no red yet', s['agent']['slot'] == 1 and s['agent']['red'] == 0)
        s = S(33.2); at(33.2, '3.2: the staff member has looked back to the call; the red outline has formed', s['staffYaw'] > 0.8 and s['agent']['red'] == 1)
        s = S(35.3); at(35.3, '3.3: nothing drawn or sent yet', s['d'] == [True, True, True] and s['market']['p'] == 0 and not any(s['pk']))
        s = S(35.75); at(35.75, '3.3: prices go into the shared tool (0.5-1.0 s)', s['pk'][0] and s['pk'][2] and not s['pk'][1])
        s = S(36.25); at(36.25, '3.3: a suggested price comes back (1.0-1.5 s)', s['pk'][1] and s['pk'][3] and not s['pk'][0])
        s = S(37.5); at(37.5, '3.3: the two price lines rise together; no red yet', 0.4 < s['market']['p'] < 0.6 and s['market']['red'] == 0)
        s0, s1 = S(38.4), S(39.5); at(39.5, '3.3: the red outline wraps both lines once they are drawn; the buyer looks from tag to tag',
                                      s1['market']['p'] == 1 and s1['market']['red'] == 1 and s0['market']['red'] == 0 and s0['buyerYaw'] != s1['buyerYaw'])
        s0, s1 = S(40.4), S(43.0); at(43.0, '4.1: the owner slides the printout across the desk; the question list is still empty', s1['paperX'] > s0['paperX'] + 0.3 and s1['split']['n'] == 0)
        s0, s1 = S(45.5), S(48.3); at(48.3, '4.2: the three questions settle on the question list (1.0-3.0 s); the register has only its empty line',
                                      s0['split']['n'] == 0 and s1['split']['n'] == 3 and sorted(s1['split']) == ['n'])
        s = S(50.5); at(50.5, '4.3: a price tile arrives and waits under the hold square', 0 < s['pown']['a'] < 1 and s['pown']['tick'] == 0)
        s = S(51.6); at(51.6, '4.3: the tile waits, no tick yet', s['pown']['a'] == 1 and s['pown']['tick'] < 1 and not s['pown']['gone'])
        s = S(52.0); at(52.0, '4.3: the green tick has landed (1.0-2.0 s)', s['pown']['tick'] == 1 and not s['tile'])
        s = S(52.7); at(52.7, '4.3: the tile moves on to the price tag', s['pown']['gone'] == 1 and s['tile'] and 120.0 < s['tileX'] < 121.2)
        zs = [z for k in range(0, 18) for z in S(53.3 + k * 0.1)['lpk']]
        at(55.0, '4.3: the outcome flows from the tag toward the gate and nothing passes the barrier (gate at z -1.7)', zs and max(zs) <= -1.8 + 1e-6, zs[:6])
        s = S(54.0); at(54.0, '4.3: the gate lamp is amber', s['lamp'] == '#e9a23b')
        s = S(57.0); at(57.0, 'close: the wall screen shows the closed gate with its two empty check rings', s['office']['close'] == 1)
        bad = [e for e in exp if not e[2]]
        check('staged world follows the shot table at the script\'s local times', not bad, bad or f'{len(exp)} checks')

        # ------------------------------------------------------------ 6. colour rules
        red_at = pg.evaluate("() => { const out = []; for (let k = 0; k < 590; k++) { const t = k / 10; FILM.signature(t); if (window.FILM_DP.st.red) out.push(t); } return out; }")
        check('red (a possible harm) appears only in beat 3 (25-40 s)', red_at and all(25 <= t < 40 for t in red_at), f'{len(red_at)} samples, {red_at[:1]}..{red_at[-1:]}')
        steady = pg.evaluate("""() => { const o = window.FILM_DP, a = [], b = [], c = []; for (let k = 0; k < 120; k++) { const t = 28.4 + k / 10; FILM.signature(t);
            if (o.red31.visible) a.push(+o.red31.scale.x.toFixed(4)); if (t >= 32.9 && t < 35) b.push(o.agentScr.want.red); if (t >= 39.4 && t < 40) c.push(o.market.want.red); } return [a, b, c]; }""")
        check('red never pulses: each dashed red outline forms once and then holds', steady[0] and len(set(steady[0])) == 1 and set(steady[1]) == {1} and set(steady[2]) == {1},
              [sorted(set(x)) for x in steady])
        src = FILM.read_text(encoding='utf-8')
        red_calls = re.findall(r"strokeStyle = DP\.red;[^\n]*", src)
        check('red is drawn as dashed outlines only (canvas strokes with a line dash; the 3D outline is built from dashes)',
              len(red_calls) == 2 and all('setLineDash([' in x for x in red_calls) and 'fillStyle = DP.red' not in src
              and re.search(r"o\.red31 = dashRect\(", src) is not None, red_calls)

        # ------------------------------------------------------------ 7. clearance
        worst = pg.evaluate('JSON.stringify(FILM.minClearance(0.1))')
        worst = json.loads(worst)
        check(f'clearance: >= {cfg["minClearance"]} m from every collider and figure (0.1 s steps)', cfg['minClearance'] == 0.8 and worst['d'] >= 0.8, worst)
        br.close()

        # ------------------------------------------------------------ 8. fallback with three.js blocked
        br = pw.chromium.launch(args=GL_ARGS)
        fp = br.new_page(viewport={'width': 1280, 'height': 720})
        fp.route(re.compile(r'three(\.min)?\.js'), lambda r: r.abort())
        fp.goto(FILM.as_uri(), wait_until='load', timeout=60000)
        fp.wait_for_function('window.FILM && window.FILM.ready === true', timeout=45000)
        fb = fp.evaluate("""() => ({ mode: FILM.mode, title: document.getElementById('fbtitle').textContent,
            paras: Array.from(document.querySelectorAll('#fallback > p')).map(p => p.textContent),
            items: Array.from(document.querySelectorAll('#fblist li')).map(li => [li.querySelector('b').textContent, li.querySelector('span').textContent]),
            text: document.getElementById('fallback').textContent })""")
        br.close()

        def item_ok(r, it):
            label = (f'{r["beat"]} ' if r['beat'] else '') + f'{r["beatName"]} \u2014 {r["setting"]}'
            return it[0] == label and r['head'] in it[1] and r['sup'] in it[1] and r['note'] in it[1]
        check('fallback: the script\'s title, the WebGL note and every shot as "<beat> - <setting>" with its headline, support line and note',
              fb['mode'] == 'fallback' and fb['title'] == FALLBACK_TITLE and fb['paras'] == [WEBGL_NOTE] and len(fb['items']) == 12
              and all(item_ok(r, it) for r, it in zip(rows, fb['items'])), {'title': fb['title'], 'items': fb['items'][:3]})
        check('fallback: no shot numbers and no times', not re.search(r'\b\d\.\d\b|\b\d+(\.\d+)? ?s\b|\d:\d\d', fb['text']), 'ok')

    check('no console errors or warnings, no page errors', not errors, errors[:10] or 'none')
    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'film': str(FILM), 'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
