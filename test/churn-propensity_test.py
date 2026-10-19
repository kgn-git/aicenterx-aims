"""Film-specific checks for simulation/churn-propensity/Churn Propensity.html (issue #7, phase 2).

Usage:  python test/churn-propensity_test.py [--write-lines]

The shared test (test/film_controls_test.py) covers controls, layout, determinism of the snapshot state, clearance and the
fallback. This test checks the film against its approved script, "Churn Propensity - Script and Protocols.md":
  - script parity: one scene per shot-table row (Open, 1.1-4.2, Close) with the same start, dur, beat, setting, source line,
    headline and support line (verbatim) and accent; no notes, chips, cards or footers; the initiative label top right;
    the fallback title is the open headline; scenes are named "<beat> - <setting>" with the setting in the scene list
  - runtime 57 s: beats 10 / 12 / 15 / 12 s (49 s), open and close cards 4 s each
  - the word-count and readability table of Part 1, row by row (headline, support and source words, pace, grades), and its
    limits: headline <= 14 words, support <= 18, source <= 10, 220 words in total (headlines, supports and sources),
    Flesch-Kincaid grade <= 8 for every headline and support line (and for the source lines the table does not flag as
    verbatim record names), pace <= 5.0 words per second; no digit in any on-screen line
  - test/churn-propensity-lines.json holds the same lines (written with --write-lines)
  - the staged world follows the shot table at the script's local times (read through the film's debug hook
    window.FILM_CHURN): the street lamp, the laptop pages and the clickstream dots (1.1); the coins spreading and the leavers
    (1.2); the streams, the two live drawers opening, the packets and the ranked column (2.1); the stamp in the inset, the
    invitation on the phone and the three grey plates that never change (2.2); the dashed "what if" bar and the red dashed
    outline (3.1); the door glyphs and the outline below the cut (3.2); the late objection that has not reached the register,
    and the outline round the caller's tile (3.3); the funnel, the grey tray, the amber share, the preview, the stamp and the
    send (4.1); this quarter's bars still rising at the cut and the new-customer panel (4.2); the empty slot and the outlined
    next quarter (close)
  - colour rules: a red dashed outline appears only in beat 3 (26-41 s); no solid red anywhere in the world; no in-world words
  - the camera keeps >= 1.5 m from every object of the abstract set (its colliders are padded by 0.5 m, checked at >= 1.0 m)
  - determinism of the picture: the rendered frame at t is the same whatever was shown before (this also covers the film's
    own canvas screens, which FILM.signature does not see)
  - the template machinery after "END OF CONFIG" is unchanged; no console errors or warnings
Prints a JSON report; exit code 1 on any failure.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
FILM = ROOT / 'simulation' / 'churn-propensity' / 'Churn Propensity.html'
SCRIPT = ROOT / 'simulation' / 'churn-propensity' / 'Churn Propensity - Script and Protocols.md'
TEMPLATE = ROOT / 'simulation' / '_template' / 'film-template.html'
LINES = ROOT / 'test' / 'churn-propensity-lines.json'
OUT = ROOT / 'test' / 'shots' / 'churn-propensity-specific'
GL_ARGS = ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
ACCENT = {'neutral': '#e8e6e1', 'teal': '#2a9d8f', 'blue': '#4a86d8', 'red': '#d84a3a', 'green': '#3fa34d'}
BEATS = {'Open': 0, 'The situation': 1, 'The AI at work': 2, 'What can go wrong': 3, 'How it is kept safe': 4, 'Close': 0}
SHOTS = ['Open', '1.1', '1.2', '2.1', '2.2', '3.1', '3.2', '3.3', '4.1', '4.2', 'Close']
SETS = ['home', 'home', 'mkt', 'fs', 'home', 'rev', 'mkt', 'mkt', 'mkt', 'rev', 'rev']
END = '/* ================================================== END OF CONFIG'


def cell(s):
    s = s.strip()
    return '' if s == '—' else s.strip('`')


def shot_table():
    """Part 1 shot table: | # | start | dur | beat | setting | source | camera | world action | headline | support | note | accent | traces |"""
    rows = []
    for line in SCRIPT.read_text(encoding='utf-8').splitlines():
        if not re.match(r'^\| (Open|Close|\d\.\d) \| \d+ \| \d+ \| ', line):
            continue
        c = [x.strip() for x in line.strip().strip('|').split('|')]
        if len(c) != 13:
            continue
        rows.append({'shot': c[0], 'start': float(c[1]), 'dur': float(c[2]), 'beat': BEATS[c[3]], 'setting': cell(c[4]), 'source': cell(c[5]),
                     'head': c[8], 'sup': cell(c[9]), 'extra': cell(c[10]), 'accent': ACCENT[c[11]]})
    return rows


def word_table():
    """Part 1 word-count table: | shot | dur | headline | support | source | all | pace | FK headline | FK support | FK source |"""
    rows, total = {}, None
    for line in SCRIPT.read_text(encoding='utf-8').splitlines():
        c = [x.strip() for x in line.strip().strip('|').split('|')]
        if len(c) != 10:
            continue
        if re.match(r'^(Open|Close|\d\.\d)$', c[0]) and re.match(r'^\d+$', c[1]):
            num = lambda v: 0 if v == '—' else int(v)
            fk = lambda v: None if v == '—' else float(v.replace('*', '').strip())
            rows[c[0]] = {'dur': int(c[1]), 'head': num(c[2]), 'sup': num(c[3]), 'source': num(c[4]), 'all': int(c[5]), 'pace': float(c[6]),
                          'fkHead': fk(c[7]), 'fkSup': fk(c[8]), 'fkSource': fk(c[9]), 'sourceFlagged': '*' in c[9]}
        elif c[0] == '**Total**':
            total = int(re.search(r'\d+', c[5]).group(0))
    return rows, total


def words(s):
    return [w for w in s.split() if re.search(r'[A-Za-z0-9]', w)]


def grade(s):
    ws = words(s)
    if not ws:
        return 0.0
    sentences = max(1, len(re.findall(r'[.!?]', s)))
    syl = sum(max(1, len(re.findall(r'[aeiouy]+', w.lower()))) for w in ws)
    return 0.39 * len(ws) / sentences + 11.8 * syl / len(ws) - 15.59


# world state at film time t, read through the film's debug hook after FILM.signature(t) has staged that exact frame
STATE_JS = """t => { FILM.pause(); FILM.signature(t); const o = window.FILM_CHURN, w = s => JSON.parse(JSON.stringify(s.want));
  const vis = Object.keys(o.sets).filter(k => o.sets[k].visible), P = g => [g.position.x, g.position.y, g.position.z];
  return { sets: vis, laptop: w(o.laptop), curs: o.curs.map(g => g.visible), cursPos: o.curs.map(P), lamp: o.lampHeadM.emissiveIntensity,
    elena: P(o.elena), elenaPitch: o.elena.userData.head.rotation.x, chin: o.elena.userData.la.rotation.x, tablePhone: o.tablePhone.visible,
    ePhone: w(o.ePhone), ePhoneShown: o.ePhone.group.visible, ins22: w(o.ins22), f22: o.f22.visible,
    plates: o.plates.map(g => g.visible), platesSpec: o.plates.map(g => JSON.stringify(g.userData.screen.want)),
    w12: w(o.w12), own: w(o.own), ana: w(o.ana), rev: w(o.rev), newc: w(o.newc),
    f33: o.f33.visible, xenv: o.xenv33.visible, xenvPos: P(o.xenv33), drawer: P(o.regDrawer),
    inStreams: o.inP.concat(o.inC).filter(g => g.visible).length, drawers: o.drawers.map(g => g.position.z), packets: o.pk.filter(m => m.visible).length,
    tiles: o.tiles.map(g => g.visible), tilePos: o.tiles.map(P), slots: o.slots,
    tileSpec: o.tiles.map(g => JSON.parse(JSON.stringify(o.cs.find(s => s.mesh === g.children[0]).want))),
    folder: o.folder.visible, f2lean: o.f2.userData.body.rotation.x }; }"""

# every visible mesh in the world whose own colour is the fault red (a solid red ring, plate or glyph would be one)
SOLID_RED_JS = """t => { FILM.pause(); FILM.signature(t); const o = window.FILM_CHURN, out = [];
  Object.keys(o.sets).forEach(k => { const g = o.sets[k]; if (!g.visible) return; g.traverse(m => { if (!m.isMesh) return; let v = m.visible, q = m.parent; while (v && q) { v = q.visible; q = q.parent; }
    if (!v || !m.material || !m.material.color) return; const c = m.material.color.getHexString(), e = m.material.emissive ? m.material.emissive.getHexString() : '';
    if (c === 'd84a3a' || e === 'd84a3a') out.push(k); }); }); return out; }"""


def main():
    checks = {}

    def check(name, ok, detail=''):
        checks[name] = {'ok': bool(ok), 'detail': detail if isinstance(detail, str) else json.dumps(detail)[:1500]}

    rows = shot_table()
    wt, wt_total = word_table()
    check('script: shot table parsed (Open, 1.1-4.2, Close) and word-count table parsed',
          [r['shot'] for r in rows] == SHOTS and sorted(wt) == sorted(SHOTS) and wt_total == 220, f'{[r["shot"] for r in rows]}; word rows {len(wt)}; total {wt_total}')
    film_src = FILM.read_text(encoding='utf-8')
    tpl_src = TEMPLATE.read_text(encoding='utf-8')
    check('template machinery after "END OF CONFIG" is unchanged', END in film_src and film_src[film_src.index(END):] == tpl_src[tpl_src.index(END):], 'byte-identical tail')
    cfg_src = film_src[film_src.index('/* ---- film-local glyph painters'):film_src.index(END)]   # the film's own block: painters, CONFIG, build, update
    check('in-world screens draw glyphs only (no fillText / strokeText in the film\'s painters)', 'fillText' not in film_src and 'strokeText' not in film_src, 'none')
    check('abstract set: every object carries a collider padded by 0.5 m', 'var pad = 0.5;' in cfg_src and cfg_src.count('padColl(') >= 4, f'{cfg_src.count("padColl(")} padColl uses')

    errors = []
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=GL_ARGS)
        pg = br.new_page(viewport={'width': 1280, 'height': 720})
        pg.on('console', lambda m: errors.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
        pg.on('pageerror', lambda e: errors.append(f'pageerror: {e}'))
        pg.goto(FILM.as_uri(), wait_until='load', timeout=60000)
        pg.wait_for_function('window.FILM && window.FILM.ready === true', timeout=45000)
        pg.evaluate('FILM.pause()')
        cfg = pg.evaluate('window.FILM_CONFIG')
        beats = cfg['beats']

        # ---- the film against the script, scene by scene
        diff = []
        for r, b in zip(rows, beats):
            want = {'start': r['start'], 'dur': r['dur'], 'beat': r['beat'], 'setting': r['setting'], 'source': r['source'], 'head': r['head'], 'sup': r['sup'], 'accent': r['accent']}
            got = {'start': b['start'], 'dur': b['dur'], 'beat': b['beat'], 'setting': b['setting'], 'source': b.get('source', ''), 'head': b['head'], 'sup': b.get('sup', ''),
                   'accent': cfg['accent'][str(b['beat'])].lower()}
            bad = {k: (got[k], v) for k, v in want.items() if got[k] != v}
            if bad:
                diff.append({'shot': r['shot'], 'diff': bad})
        check('every scene matches its shot: start, dur, beat, setting, source line, headline, support line (verbatim), accent',
              len(beats) == len(rows) and not diff, diff or f'{len(beats)} scenes')
        extra = [b['name'] for b in beats if b.get('note') or b.get('chips') or b.get('cards') or b.get('stages') or b.get('foot')]
        check('no on-screen text beyond the script (no notes, chips, cards or footers)', not extra and all(not r['extra'] for r in rows), extra or 'none')
        core = sum(b['dur'] for b in beats if b['beat'])
        per_beat = [sum(b['dur'] for b in beats if b['beat'] == n) for n in (1, 2, 3, 4)]
        check('runtime: 57 s; beats 10 / 12 / 15 / 12 s (49 s); open and close cards 4 s each',
              cfg['duration'] == 57 and core == 49 and per_beat == [10, 12, 15, 12] and beats[0]['dur'] == 4 and beats[-1]['dur'] == 4, f'film {cfg["duration"]} beats {per_beat}')
        check('initiative label, title and fallback title (the open headline)',
              cfg.get('initiative') == 'Churn Propensity' and cfg.get('title') == 'Churn Propensity' and cfg['fallbackTitle'] == rows[0]['head'], f'{cfg.get("initiative")} / {cfg["fallbackTitle"]}')
        check('each beat scene is named "<beat> — <setting>" and listed by its setting; cards Introduction and Close',
              all((b['name'] == f'{cfg["beatLabels"][b["beat"] - 1]} — {b["setting"]}' and b.get('nav') == b['setting']) if b['beat'] else b['name'] in ('Introduction', 'Close') for b in beats)
              and beats[0]['name'] == 'Introduction' and beats[-1]['name'] == 'Close', [b['name'] for b in beats])
        check('accents are the template defaults; minimum clearance 1.0 m',
              {k: v.lower() for k, v in cfg['accent'].items()} == {'0': '#e8e6e1', '1': '#2a9d8f', '2': '#4a86d8', '3': '#d84a3a', '4': '#3fa34d'} and cfg['minClearance'] == 1.0, cfg['accent'])

        # ---- words, readability, pace, digits (against the script's word-count table)
        lines, over, tdiff = [], [], []
        for r, b in zip(rows, beats):
            hw, sw, rw = len(words(b['head'])), len(words(b.get('sup', ''))), len(words(b.get('source', '')))
            pace = (hw + sw) / b['dur']
            item = {'shot': r['shot'], 'setting': b['setting'], 'head': b['head'], 'sup': b.get('sup', ''), 'source': b.get('source', ''),
                    'headWords': hw, 'supWords': sw, 'sourceWords': rw, 'allWords': hw + sw + rw, 'wordsPerSecond': round(pace, 2),
                    'gradeHead': round(grade(b['head']), 1), 'gradeSup': round(grade(b.get('sup', '')), 1), 'gradeSource': round(grade(b['source']), 1) if b.get('source') else None}
            lines.append(item)
            t = wt.get(r['shot'], {})
            want = {'head': t.get('head'), 'sup': t.get('sup'), 'source': t.get('source'), 'all': t.get('all'), 'pace': t.get('pace'), 'fkHead': t.get('fkHead'), 'fkSup': t.get('fkSup'), 'fkSource': t.get('fkSource')}
            got = {'head': hw, 'sup': sw, 'source': rw, 'all': hw + sw + rw, 'pace': round(pace, 1), 'fkHead': item['gradeHead'], 'fkSup': item['gradeSup'], 'fkSource': item['gradeSource']}
            bad = {k: (got[k], v) for k, v in want.items() if got[k] != v}
            if bad:
                tdiff.append({'shot': r['shot'], 'diff': bad})
            if hw > 14 or sw > 18 or rw > 10 or item['gradeHead'] > 8.0 or item['gradeSup'] > 8.0 or pace > 5.0 + 1e-9:
                over.append(item)
            if item['gradeSource'] is not None and item['gradeSource'] > 8.0 and not t.get('sourceFlagged'):
                over.append({'shot': r['shot'], 'source grade (not flagged as a record name)': item['gradeSource']})
        total = sum(x['allWords'] for x in lines)
        check("words: every line matches the script's word-count and readability table (words, pace, grades)", not tdiff, tdiff or f'{len(lines)} shots')
        check('words: headline <= 14, support <= 18, source <= 10 words; grade <= 8 (flagged record names reported); pace <= 5.0 words/s', not over,
              over or f'max pace {max(x["wordsPerSecond"] for x in lines)}, max grade {max(max(x["gradeHead"], x["gradeSup"]) for x in lines)}')
        check('words: 220 on-screen words in total (headlines, supports, sources), at the ceiling', total == 220 == wt_total, f'{total} words')
        digits = sorted({d for b in beats for s in (b['head'], b.get('sup', ''), b.get('source', ''), b['setting']) for d in re.findall(r'\d', s)})
        check('no digit in any on-screen line (setting, source, headline, support)', not digits, digits or 'none')
        if '--write-lines' in sys.argv:
            LINES.write_text(json.dumps({'film': FILM.name, 'script': SCRIPT.name, 'totalWords': total, 'lines': lines}, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        stored = json.loads(LINES.read_text(encoding='utf-8')) if LINES.exists() else {}
        check('test/churn-propensity-lines.json holds the same on-screen lines, counts and grades', stored.get('lines') == lines and stored.get('totalWords') == total,
              'in step' if stored.get('lines') == lines else 'out of step: run with --write-lines')

        # ---- the staged world at the script's local times
        S = lambda t: pg.evaluate(STATE_JS, t)
        exp = []

        def at(t, label, ok):
            exp.append((round(t, 2), label, bool(ok)))
        for b, s in zip(beats, SETS):
            for f in (0.05, 0.5, 0.95):
                tt = b['start'] + b['dur'] * f
                at(tt, f'set {s} alone on screen', S(tt)['sets'] == [s])
        s0, s1 = S(0.5), S(3.0)
        at(3.0, 'open: the street lamp comes on; Elena on the sofa; her phone face down on the low table', s0['lamp'] < 0.2 and s1['lamp'] > 0.9 and abs(s1['elena'][2] + 0.86) < 0.01 and s1['tablePhone'])
        s = S(4.5); at(4.5, '1.1: the help pages, no cursor dot yet', s['laptop']['pg'] == 0 and not any(s['curs']))
        s = S(5.3); at(5.3, '1.1: a page on closing an account opens (0.8 s); a cursor dot lifts off', s['laptop']['pg'] == 1 and s['curs'][0])
        a, b2 = S(5.2)['cursPos'][0], S(6.2)['cursPos'][0]; at(6.2, '1.1: the dot drifts toward the window', b2[2] > a[2] + 0.8)
        s = S(6.6); at(6.6, '1.1: a second page opens (2.2 s); a second dot lifts off', s['laptop']['pg'] == 2 and s['curs'][1])
        s = S(8.3); at(8.3, '1.1: she pauses, chin on hand (3.5 s)', s['chin'] < -0.8)
        s = S(9.3); at(9.3, '1.2: the budget is still in its stack', s['w12']['spread'] == 0 and s['w12']['idle'] == 0)
        s = S(11.1); at(11.1, '1.2: the coins have spread evenly over every tile (0.5-2.0 s); nobody has left yet', s['w12']['spread'] > 0.99 and s['w12']['leave'] == 0)
        s = S(12.6); at(12.6, '1.2: a few tiles slide off the grid (2.5-3.5 s)', s['w12']['leave'] > 0.99)
        s = S(15.0); at(15.0, '2.1: two blue streams arrive; the drawers are still shut', s['inStreams'] >= 2 and all(abs(z + 0.88) < 1e-3 for z in s['drawers']))
        s = S(16.6); at(16.6, '2.1: the two live drawers have slid open; packets head for the S-curve ring', all(z > -0.6 for z in s['drawers']) and s['packets'] >= 2)
        s = S(17.4); at(17.4, '2.1: no tile has left the ring yet', not any(s['tiles']))
        s = S(19.7)
        at(19.7, '2.1: seven tiles stacked in a ranked column, fullest at the top; Elena\'s tile (house) near the top',
           all(s['tiles']) and all(abs(p[1] - q[1]) < 0.01 for p, q in zip(s['tilePos'], s['slots'])) and [x['fill'] for x in s['tileSpec']] == sorted([x['fill'] for x in s['tileSpec']], reverse=True)
           and [x['house'] for x in s['tileSpec']].index(True) == 1)
        s = S(20.2); at(20.2, '2.2: the stamp has not landed; the phone is quiet', s['ins22']['stamp'] == 0 and s['ePhone']['mode'] == 'home' and s['f22'])
        s = S(21.3); at(21.3, '2.2: the campaign owner\'s green stamp has landed in the inset (0.3-1.2 s)', s['ins22']['stamp'] >= 0.99)
        s = S(22.0); at(22.0, '2.2: her phone lights with the invitation (1.8 s); she stands at the window', s['ePhone']['mode'] == 'msg' and s['ePhoneShown'] and abs(s['elena'][2] - 2.42) < 0.01)
        a, b2 = S(22.5), S(24.8); at(24.8, '2.2: she reads the message, then looks out of the window (3.5-6 s)', a['elenaPitch'] > 0.4 and b2['elenaPitch'] < 0.1)
        specs = [S(20 + k * 0.5) for k in range(12)]
        at(25.9, '2.2: the price, credit and service plates stay grey and unchanged throughout',
           all(all(x['plates']) for x in specs) and len({json.dumps(x['platesSpec']) for x in specs}) == 1 and all('"bg":"#8d99a3"' in p for p in specs[0]['platesSpec']))
        s = S(26.9); at(26.9, '3.1: the review screen; the "what if" bar has not grown yet; no outline', s['rev']['mode'] == '31' and s['rev']['wi'] == 0 and s['rev']['red'] == 0 and s['rev']['rise'] == 0)
        a, b2 = S(27.6), S(28.9); at(28.9, '3.1: the dashed "what if" bar grows in (1.0-3.0 s)', 0 < a['rev']['wi'] < b2['rev']['wi'] < 1)
        a, b2 = S(29.1), S(29.9); at(29.9, '3.1: the red dashed outline draws round the narrowing gap (3.2 s)', a['rev']['red'] == 0 and b2['rev']['red'] > 0.9)
        a, b2 = S(32.4), S(32.9); at(32.9, '3.2: three bottom tiles carry the door glyph (1.5 s)', a['ana']['door'] == 0 and b2['ana']['door'] > 0.99)
        a, b2 = S(33.7), S(34.5); at(34.5, '3.2: a red dashed outline draws round them below the cut (2.8 s)', a['ana']['red'] == 0 and b2['ana']['red'] > 0.9)
        a, b2, c2 = S(36.4), S(37.0), S(40.9)
        at(37.0, '3.3: a late objection rises from the call (inset) and drifts toward the register, not yet arrived', c2['f33'] and not a['xenv'] and b2['xenv'] and c2['xenv'] and c2['xenvPos'][0] < c2['drawer'][0] - 0.05)
        a, b2 = S(38.7), S(39.5)
        at(39.5, '3.3: a red dashed outline round the caller\'s tile (2.8 s); no crossed envelope on it yet; nothing sent', a['own']['red'] == 0 and b2['own']['red'] > 0.9 and all(S(36 + k)['own']['xenv'] == 0 and S(36 + k)['own']['send'] == 0 for k in range(5)))
        a, b2 = S(41.4), S(42.1)
        at(42.1, '4.1: the list passes the funnel; the late objector\'s tile drops into the grey tray (1.0 s); the suppressed bar ticks up',
           a['own']['drop'] < 0.1 and a['own']['sup'] == 0 and b2['own']['funnel'] > 0.99 and b2['own']['drop'] > 0.99 and b2['own']['xenv'] > 0.99 and b2['own']['sup'] == 1)
        a, b2 = S(43.5), S(44.4); at(44.4, '4.1: the amber new-customer share pulses while she reads it (2.0-3.2 s), then settles', a['own']['amb'] > 0 and b2['own']['amb'] == 0)
        a, b2 = S(44.4), S(44.6); at(44.6, '4.1: the message preview appears (3.5 s)', a['own']['preview'] == 0 and b2['own']['preview'] == 1)
        a, b2 = S(45.4), S(46.0); at(46.0, '4.1: sign-off: the green stamp lands and the send turns blue (4.5 s)', a['own']['stamp'] == 0 and a['own']['send'] == 0 and b2['own']['stamp'] > 0.99 and b2['own']['send'] == 1)
        a, b2, c2 = S(47.3), S(52.0), S(52.95)
        at(52.95, '4.2: this quarter\'s bars rise together and are still rising at the cut; no "what if" bar',
           a['rev']['mode'] == '42' and a['rev']['wi'] == 0 and 0 < b2['rev']['rise'] < c2['rev']['rise'] < 0.5)
        a, b2, c2 = S(49.3), S(50.0), S(52.95)
        at(50.0, '4.2: the new-customer panel begins to rise in amber (2.5 s), still rising at the cut; a figure leans in',
           a['newc']['rise'] == 0 and 0 < b2['newc']['rise'] < c2['newc']['rise'] < 0.5 and c2['f2lean'] > 0.15)
        s = S(55.0); at(55.0, 'close: the empty slot with the folder hovering above it; the next quarter outlined on the wall', s['folder'] and s['rev']['mode'] == 'close' and s['newc'].get('close') == 1)
        bad = [e for e in exp if not e[2]]
        check("staged world follows the shot table at the script's local times", not bad, bad or f'{len(exp)} checks')

        # ---- colour rules: a red dashed outline only in beat 3; never a solid red object
        red_at = pg.evaluate("""() => { const out = []; for (let k = 0; k < 570; k++) { const t = k / 10; FILM.signature(t); const o = window.FILM_CHURN;
            if ((o.own.want.red || 0) > 0 || (o.ana.want.red || 0) > 0 || (o.rev.want.red || 0) > 0) out.push(t); } return out; }""")
        check('red dashed outlines appear only in beat 3 (26-41 s)', red_at and all(26 <= t < 41 for t in red_at), f'{len(red_at)} samples, {red_at[:1]}..{red_at[-1:]}')
        solid = [(t, r) for t in [k * 0.5 for k in range(114)] for r in [pg.evaluate(SOLID_RED_JS, t)] if r]
        check('no solid red anywhere in the world (no fault is recorded for churn)', not solid, solid[:5] or 'none in 114 samples')

        # ---- abstract set: the camera keeps >= 1.5 m from every object (padded colliders >= 1.0 m)
        worst = pg.evaluate("() => { let w = null; for (let t = 14; t < 20; t += 0.1) { const c = FILM.clearance(t); if (!w || c.d < w.d) w = c; } return w; }")
        check('abstract set (14-20 s): camera >= 1.5 m from every object', worst['d'] >= 1.0, worst)

        # ---- the rendered frame is a pure function of t (own canvases included)
        settle = '!FILM.present().pending && !FILM.present().dirty'

        def seek(t):
            pg.evaluate('t => FILM.seek(t)', t)
            pg.wait_for_function(settle, timeout=10000)

        def frame(t):
            seek(t)
            pg.evaluate("() => { document.getElementById('ui').style.visibility = 'hidden'; }")
            pg.wait_for_timeout(120)
            h = hashlib.sha1(pg.locator('#stage').screenshot()).hexdigest()
            pg.evaluate("() => { document.getElementById('ui').style.visibility = ''; }")
            return h
        probe = [2.5, 6.6, 11.5, 17.0, 21.5, 29.5, 34.6, 39.5, 46.2, 51.0, 55.0]
        first = {t: frame(t) for t in probe}
        for t in probe:
            frame((t * 7.3) % cfg['duration'])
        again = {t: frame(t) for t in reversed(probe)}
        differ = [t for t in probe if first[t] != again[t]]
        check('determinism of the picture: the rendered frame at t is identical whatever was shown before', not differ, f'{len(probe)} times; differing at {differ}')
        for t in (6.6, 16.6, 21.9, 29.9, 34.5, 39.5, 46.2, 52.9, 55.5):
            seek(t)
            pg.wait_for_timeout(150)
            pg.screenshot(path=str(OUT / f'frame-{t:05.1f}.png'))
        br.close()
    check('no console errors or warnings', not errors, errors[:10])
    failed = [k for k, v in checks.items() if not v['ok']]
    result = {'film': str(FILM), 'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}
    (OUT / 'report.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
