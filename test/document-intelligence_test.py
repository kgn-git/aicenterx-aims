"""Film-specific checks for simulation/document-intelligence/Document Intelligence.html (initiative `docai`, issue #8 phase 2).

Usage:  python test/document-intelligence_test.py [--write-lines]

The shared test (test/film_controls_test.py) covers controls, layout, determinism, clearance and the fallback. This test checks
the film against its script, "Document Intelligence - Script and Protocols.md" (Part 1, the source of truth):
  - one scene per shot-table row (Open, 1.1, 2.1, 2.2, 3.1, 3.2, 4.1, 4.2, 4.3, Close), with the same start, dur, beat, setting,
    source line, headline and support line (verbatim) and accent; no notes, chips, cards or stages (Part 1 "Overlay")
  - the shot table and the word-count table of the script agree, and the film carries exactly those 28 lines
  - runtime 56 s: beats 8 / 12 / 12 / 16 s (48 s), open and close cards 4 s each
  - scene names (Introduction, "<beat> — <setting>", Close), navigation labels, initiative label, fallback title, accents
  - the word and readability limits of Part 1: headline <= 14 words, support <= 18, source line <= 10, Flesch-Kincaid grade <= 8
    on every line, reading pace <= 4.5 words per second, 220 words in all (the script counts 219); no digit on screen except in the
    record ids n3 and r8 that the source lines name
  - the staged world follows the shot table at the script's local times (read through the film's debug hook window.FILM_DOCAI)
  - red appears only as the 3D fault rings of shots 1.1, 3.1 and 3.2; the in-world screens never show a warning glyph
  - the camera keeps >= 2.5 m from every object of the region set (colliders padded by 1.5 m, checked at >= 1.0 m) and >= 1.0 m
    from every collider and person indoors; no Math.random or Date in CONFIG
--write-lines writes test/document-intelligence-lines.json (every on-screen line with its words, grade and pace), as the script asks.
Prints a JSON report; exit code 1 on any failure.
"""
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
FILM = ROOT / 'simulation' / 'document-intelligence' / 'Document Intelligence.html'
SCRIPT = ROOT / 'simulation' / 'document-intelligence' / 'Document Intelligence - Script and Protocols.md'
LINES = ROOT / 'test' / 'document-intelligence-lines.json'
GL_ARGS = ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
ACCENT = {'neutral': '#e8e6e1', 'teal': '#2a9d8f', 'blue': '#4a86d8', 'red': '#d84a3a', 'green': '#3fa34d'}
SHOTS = ['Open', '1.1', '2.1', '2.2', '3.1', '3.2', '4.1', '4.2', '4.3', 'Close']
LIMIT = {'headline': 14, 'support': 18, 'source': 10}


def cells(line):
    return [c.strip() for c in line.strip().strip('|').split(' | ')]


def shot_table():
    """Part 1 shot table: 13 columns, the first a shot id."""
    rows = []
    for line in SCRIPT.read_text(encoding='utf-8').splitlines():
        if not re.match(r'^\| (Open|Close|\d\.\d) \|', line):
            continue
        c = cells(line)
        if len(c) != 13:
            continue
        beat = int(c[3].split()[0])
        rows.append({'id': c[0], 'start': float(c[1]), 'dur': float(c[2]), 'beat': beat, 'setting': c[4],
                     'source': '' if c[5] == '—' else c[5], 'head': c[8], 'sup': c[9], 'extra': c[10], 'accent': ACCENT[c[11]]})
    return rows


def word_table():
    """Part 1 "Word count and readability" table: | shot | line | text | words | limit | FK grade |."""
    out = []
    for line in SCRIPT.read_text(encoding='utf-8').splitlines():
        if not re.match(r'^\| (Open|Close|\d\.\d) \| (headline|support|source) \|', line):
            continue
        c = cells(line)
        out.append({'shot': c[0], 'line': c[1], 'text': c[2], 'words': int(c[3]), 'limit': int(c[4])})
    return out


def words(s):
    return [w for w in s.split() if re.search(r'[A-Za-z0-9]', w)]


def grade(s):
    ws = words(s)
    sentences = max(1, len(re.findall(r'[.!?]', s)))
    syl = sum(max(1, len(re.findall(r'[aeiouy]+', w.lower()))) for w in ws)
    return 0.39 * len(ws) / sentences + 11.8 * syl / len(ws) - 15.59


# world state at film time t, read through the film's debug hook after FILM.signature(t) has staged that exact frame
STATE_JS = """t => { FILM.pause(); FILM.signature(t); const o = window.FILM_DOCAI, w = s => JSON.parse(JSON.stringify(s.want));
  const shown = m => { let v = m.visible, q = m.parent; while (v && q) { v = q.visible; q = q.parent; } return v; };
  return { sets: Object.keys(o.sets).filter(k => o.sets[k].visible), form: w(o.form), scan: w(o.scan), wall: w(o.wall), bench: w(o.bscr), risk: w(o.rscr),
    sheet: o.sheet.visible, sheetSpec: w(o.sheet.scr), drawerZ: o.drawer.position.z,
    rings: { slip: shown(o.rSlip), sheet: shown(o.sheetRing), drawer: shown(o.rDrawer), clamp: shown(o.rClamp), rows: shown(o.rRows) },
    pages: o.pages.map(g => [g.visible, g.position.y]), lamp: o.lampM.emissiveIntensity, panel: o.panelM.emissiveIntensity,
    chk: [o.chk.visible, o.chk.position.x, o.chk.position.z], c2: o.c2.visible, c3: o.c3.visible, inStack: [o.inStack.visible, o.inStack.scale.y],
    pk: o.pk.filter(p => p.visible).map(p => p.position.x), pin: o.pinM.color.getHexString(),
    cp: o.cp.map(m => [m.visible, m.material.color.getHexString(), m.position.x, m.position.y, m.position.z]), bar: [o.bar.visible, o.bar.position.y],
    links: [o.lk1.g.visible, o.lk2.g.visible], rt: o.rt.map(g => g.visible), leahPoint: o.leah.userData.ra.rotation.x,
    owner: o.owner.visible, rev: o.rev.visible }; }"""


def main():
    checks = {}

    def check(name, ok, detail=''):
        checks[name] = {'ok': bool(ok), 'detail': detail if isinstance(detail, str) else json.dumps(detail)[:1500]}

    rows = shot_table()
    wt = word_table()
    check('script: shot table parsed (10 shots: Open, nine story shots, Close)', [r['id'] for r in rows] == SHOTS, [r['id'] for r in rows])
    # the script's own two tables must agree, so the film can follow either
    from_shots = []
    for r in rows:
        if r['source']:
            from_shots.append((r['id'], 'source', r['source']))
        from_shots += [(r['id'], 'headline', r['head']), (r['id'], 'support', r['sup'])]
    from_words = [(x['shot'], x['line'], x['text']) for x in wt]
    check('script: the word-count table repeats the shot table line for line (28 lines)', sorted(from_shots) == sorted(from_words) and len(wt) == 28,
          {'only in shot table': sorted(set(from_shots) - set(from_words)), 'only in word table': sorted(set(from_words) - set(from_shots))})
    bad_counts = [x for x in wt if len(words(x['text'])) != x['words'] or x['limit'] != LIMIT[x['line']]]
    check('script: word counts and limits in the word table are right', not bad_counts, bad_counts or f'{sum(x["words"] for x in wt)} words')

    src = FILM.read_text(encoding='utf-8')
    cfg_src = src[src.index('/* ---- film-local glyph painters'):src.index('/* ================================================== END OF CONFIG')]
    check('CONFIG uses no Math.random or Date (a pure function of t)', not re.search(r'Math\.random|\bDate\b', cfg_src))
    check('in-world screens never draw a warning glyph (the script: no warning during a fault)', "'warn'" not in cfg_src and 'STATUS.warn' not in cfg_src and 'STATUS.fault' not in cfg_src)

    errors = []
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

        # ---- the film against the shot table, scene by scene
        diff = []
        for r, b in zip(rows, beats):
            want = {'start': r['start'], 'dur': r['dur'], 'beat': r['beat'], 'setting': r['setting'], 'source': r['source'], 'head': r['head'], 'sup': r['sup'], 'accent': r['accent']}
            got = {'start': b['start'], 'dur': b['dur'], 'beat': b['beat'], 'setting': b['setting'], 'source': b.get('source', ''), 'head': b['head'], 'sup': b.get('sup', ''),
                   'accent': cfg['accent'][str(b['beat'])].lower()}
            bad = {k: (got[k], v) for k, v in want.items() if got[k] != v}
            if bad:
                diff.append({'shot': r['id'], 'diff': bad})
        check('every scene matches its shot: start, dur, beat, setting, source line, headline, support line (verbatim), accent', len(beats) == len(rows) and not diff, diff or f'{len(beats)} scenes')
        extras = [b['name'] for b in beats if any(k in b for k in ('note', 'chips', 'cards', 'stages', 'foot'))]
        check('no notes, chips, cards or stages (script: "This film uses no notes, chips, cards or stages")', not extras and all(r['extra'] == '—' for r in rows), extras)
        per_beat = [sum(b['dur'] for b in beats if b['beat'] == n) for n in (1, 2, 3, 4)]
        check('runtime: 56 s; beats 8 / 12 / 12 / 16 s (48 s); cards 4 s each', cfg['duration'] == 56 and per_beat == [8, 12, 12, 16] and beats[0]['dur'] == 4 and beats[-1]['dur'] == 4,
              f'film {cfg["duration"]} beats {per_beat}')
        names_ok = all((b['name'] == f'{cfg["beatLabels"][b["beat"] - 1]} — {b["setting"]}' and b.get('nav') == b['setting']) if b['beat'] else b['name'] in ('Introduction', 'Close') for b in beats)
        check('scene names "<beat> — <setting>" with the setting as the list label; cards Introduction and Close', names_ok and beats[0]['name'] == 'Introduction' and beats[-1]['name'] == 'Close', [b['name'] for b in beats])
        check('initiative label and fallback title (the open headline)', cfg['initiative'] == 'Document Intelligence' and cfg['fallbackTitle'] == 'A bought service could read our scans.' == rows[0]['head'],
              [cfg['initiative'], cfg['fallbackTitle']])
        check('accents are the template defaults the script keeps', [cfg['accent'][str(n)].lower() for n in range(5)] == ['#e8e6e1', '#2a9d8f', '#4a86d8', '#d84a3a', '#3fa34d'], cfg['accent'])
        check('camera clearance rule is the script\'s 1.0 m indoors', abs(cfg['minClearance'] - 1.0) < 1e-9, cfg['minClearance'])

        # ---- words, readability, pace, digits
        lines, over = [], []
        for r, b in zip(rows, beats):
            for kind, text in (('source', b.get('source', '')), ('headline', b['head']), ('support', b.get('sup', ''))):
                if not text:
                    continue
                item = {'shot': r['id'], 'line': kind, 'text': text, 'words': len(words(text)), 'limit': LIMIT[kind], 'grade': round(grade(text), 1)}
                lines.append(item)
                if item['words'] > item['limit'] or grade(text) > 8.0:
                    over.append(item)
            pace = (len(words(b['head'])) + len(words(b.get('sup', '')))) / b['dur']
            if pace > 4.5 + 1e-9:
                over.append({'shot': r['id'], 'wordsPerSecond': round(pace, 2)})
        total = sum(x['words'] for x in lines)
        film_lines = sorted((x['shot'], x['line'], x['text']) for x in lines)
        check('the film carries exactly the 28 lines of the word table', film_lines == sorted(from_words), {'film only': sorted(set(film_lines) - set(from_words))})
        check('words: headline <= 14, support <= 18, source <= 10, FK grade <= 8 on every line, pace <= 4.5 words/s', not over, over or f'max grade {max(x["grade"] for x in lines)}')
        check('words: 219 on screen in all, within the 220-word film limit', total == 219 and total <= 220, f'{total} words')
        digit_tokens = [(b['name'], k, tok) for b in beats for k in ('setting', 'head', 'sup', 'source', 'name', 'nav') for tok in b.get(k, '').replace(',', ' ').replace(';', ' ').split() if re.search(r'\d', tok)]
        check('no digit on screen except the record ids n3 and r8 in the source lines', all(k == 'source' and t in ('n3', 'r8') for _, k, t in digit_tokens) or
              all(k in ('source', 'name', 'nav') and t in ('n3', 'r8') for _, k, t in digit_tokens), digit_tokens)
        if '--write-lines' in sys.argv:
            pace_by = {r['id']: round((len(words(b['head'])) + len(words(b.get('sup', '')))) / b['dur'], 2) for r, b in zip(rows, beats)}
            for x in lines:
                x['wordsPerSecond'] = pace_by[x['shot']] if x['line'] != 'source' else None
            LINES.write_text(json.dumps({'film': FILM.name, 'script': SCRIPT.name, 'totalWords': total, 'limit': 220, 'lines': lines}, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

        # ---- the staged world at the script's local times
        S = lambda t: pg.evaluate(STATE_JS, t)
        exp = []

        def at(t, label, ok):
            exp.append((round(t, 2), label, bool(ok)))
        sets = ['k1', 'k1', 'reg', 'k1', 'bench', 'k1', 'k1', 'k1', 'risk', 'k1']
        for b, s in zip(beats, sets):
            at(b['start'] + b['dur'] / 2, f'set {s} alone on screen', S(b['start'] + b['dur'] / 2)['sets'] == [s])
        # open: the lights come on; the service waits, grey, beside the closed pilot gate; nobody at the desk yet
        s0, s1 = S(0.1), S(2.5)
        at(2.5, 'open: the lights come on; the wall screen shows the waiting service and the gate; the checker not yet in',
           s0['panel'] < 0.2 and s1['panel'] > 0.9 and s1['wall']['m'] == 'wait' and not s1['chk'][0])
        # 1.1
        s = S(4 + 1.0); at(5.0, '1.1: the scanner lamp is on and the last pages are dropping onto the batch tray', s['lamp'] > 1.0 and s['pages'][0][0] and not s['pages'][3][0])
        s = S(4 + 3.8); at(7.8, '1.1: the lamp has gone off; all four last pages lie on the tray; the in-tray stays tall',
                           s['lamp'] < 0.2 and all(p[0] and 1.07 < p[1] < 1.1 for p in s['pages']) and s['inStack'] == [True, 0.24])
        s = S(4 + 5.0); at(9.0, '1.1: she keys the form by hand, row by row (some rows typed, some still empty), from the grey scan',
                           s['scan']['m'] == 'page' and 'k' in s['form']['rows'] and 'e' in s['form']['rows'] and s['form']['hdr'] == '#5b6670')
        s = S(4 + 6.3); at(10.3, '1.1: the last row is typed (with the slip); no ring yet', s['form']['rows'] == 'kkkkkkkk' and s['form']['slip'] == 7 and not s['rings']['slip'])
        s = S(4 + 6.7); at(10.7, '1.1: a small red ring blinks round the slipped row; the screen itself shows nothing', s['rings']['slip'] and 'warn' not in json.dumps(s['form']))
        s = S(4 + 7.3); at(11.3, '1.1: the ring is gone (it blinks once); the form goes to the tagged drawer with the slip', not s['rings']['slip'] and s['sheet'] and s['sheetSpec']['slip'] == 7 and s['drawerZ'] > 0.3)
        s = S(4 + 7.98); at(11.98, '1.1: the form is in the drawer, which is closing', not s['sheet'] and s['drawerZ'] < 0.1)
        # 2.1
        s = S(12 + 1.5); at(13.5, '2.1: blue packets travel along the pipe towards the black cube; the pin is still grey',
                            len(s['pk']) >= 3 and all(58.0 <= x <= 65.7 for x in s['pk']) and s['pin'] == '8d99a3')
        s = S(12 + 4.0); at(16.0, '2.1: the map pin above the vendor\'s building has lit green', s['pin'] == '3fa34d')
        # 2.2
        s = S(18 + 0.4); at(18.4, "2.2: the customer's contract slides into her queue as a tile", s['form'].get('q') == 1 and 0 < s['form']['nt'] < 1)
        s = S(18 + 1.0); at(19.0, '2.2: the tile opens with every row already filled in blue (the overnight run); the scan shows the blue layout boxes',
                            s['form']['rows'] == 'bbbbbbbb' and s['scan']['m'] == 'scan' and s['scan']['bx'] == 1)
        s = S(18 + 3.4); at(21.4, '2.2: one row did not match its box: it is amber while she retypes it; the rows before it are green',
                            s['form']['rows'][:5] == 'gggga' and s['form']['rows'][5:] == 'bbb')
        s = S(18 + 4.6); at(22.6, '2.2: every row confirmed green before anything is saved', s['form']['rows'] == 'gggggggg' and s['form']['hdr'] == '#3fa34d' and not s['sheet'])
        s = S(18 + 5.3); at(23.3, '2.2: the all-green form goes into the drawer with a tick', s['sheet'] and s['sheetSpec']['rows'] == 'gggggggg' and s['sheetSpec'].get('tick') == 1)
        # 3.1
        s = S(24 + 0.5); at(24.5, '3.1: the contract feeds into the clamp; no page read yet; the bar is not there', not s['bar'][0] and all(c[1] == 'f2f0ea' for c in s['cp']))
        s = S(24 + 1.4); at(25.4, '3.1: its first pages pass as blue packets', sum(c[1] == '4a86d8' for c in s['cp']) >= 2)
        s = S(24 + 2.6); at(26.6, '3.1: the bar has dropped shut; the remaining pages are grey and lie in the tray behind, unread; the screen still blank',
                            s['bar'][0] and abs(s['bar'][1] - 1.0) < 0.01 and all(c[1] == '9aa3ab' and c[4] < -1.6 for c in s['cp'][4:]) and s['bench']['on'] == 0)
        s = S(24 + 3.3); at(27.3, '3.1: the returned form is on the wall screen, tidy, with no warning; no red ring yet',
                            s['bench']['on'] == 1 and s['bench']['rec'] == 0 and not s['rings']['clamp'] and not s['rings']['rows'])
        s = S(24 + 4.8); at(28.8, "3.1: the record's own fields lie beside the form; red rings pulse round the shut bar and the blank rows; she points",
                            s['bench']['rec'] == 1 and s['rings']['clamp'] and s['rings']['rows'] and s['leahPoint'] < -1.0)
        # 3.2
        pg0 = [S(30 + x / 10)['scan']['pg'] for x in range(0, 26, 2)]
        at(32.5, '3.2: she never steps past the first page (0-2.5 s); the thumbnail strip stays unused', all(p == 0 for p in pg0))
        s = S(30 + 1.0); at(31.0, '3.2: the cut-short extraction: blue filled rows and blank rows that look ordinary, no flag', s['form']['rows'][5:] == 'nnn' and s['scan']['cut'] == 4 and s['scan']['dim'] == 1)
        s = S(30 + 2.4); at(32.4, '3.2: she has ticked every filled row; the blank rows stay blank', s['form']['rows'] == 'gggggnnn')
        s = S(30 + 3.0); at(33.0, '3.2: the form goes into the drawer with a red ring travelling with it, and no tick', s['sheet'] and s['rings']['sheet'] and s['sheetSpec']['rows'] == 'gggggnnn' and not s['sheetSpec'].get('tick'))
        s = S(30 + 4.7); at(34.7, '3.2: the drawer is copied along two blue links to the two racks, which light the same short file',
                            s['links'] == [True, True] and all(s['rt']) and s['rings']['drawer'] and not s['sheet'])
        # 4.1
        s = S(36 + 0.7); at(36.7, '4.1: three checkers stand at the wall screen as the page strip lights one thumbnail after another',
                            s['chk'][0] and s['c2'] and s['c3'] and s['chk'][2] < -3.0 and s['wall']['m'] == 'walk' and 1 <= s['wall']['k'] <= 7)
        s = S(36 + 2.5); at(38.5, '4.1: at the desk she steps through the pages of the same cut-short extraction, ticking thumbnails',
                            not s['c2'] and not s['c3'] and s['chk'][2] > -1 and 2 <= s['scan']['pg'] <= 6 and s['scan']['tk'] >= 2 and s['scan']['cut'] == 4)
        s = S(36 + 3.45); at(39.45, '4.1: every page stepped through and ticked; the later pages have no blue boxes (cut 4)', s['scan']['tk'] == 8 and s['scan']['pg'] == 7 and s['scan']['cut'] == 4)
        s = S(36 + 3.7); at(39.7, '4.1: she holds the document: the blank rows turn amber', s['form']['rows'][5:] == 'aaa' and s['form']['hdr'] == '#e9a23b')
        s = S(36 + 4.7); at(40.7, '4.1: she types them from the scan; every row green; not saved yet', s['form']['rows'] == 'gggggggg' and not s['sheet'])
        s = S(36 + 5.0); at(41.0, '4.1: only then does the form go into the drawer, with a tick', s['sheet'] and s['sheetSpec']['rows'] == 'gggggggg' and s['sheetSpec'].get('tick') == 1)
        # 4.2
        s0, s1, s2 = S(41.5 + 0.2), S(41.5 + 3.1), S(41.5 + 5.3)
        at(46.8, '4.2: the week\'s fixes drop into the tally column as one team total (0-3 s); the no-rekeying bar grows only after 3 s',
           s0['wall']['m'] == 'tally' and s0['wall']['d'] == 0 and s1['wall']['d'] == 6 and abs(s1['wall']['kb'] - 0.12) < 0.02 and s2['wall']['kb'] > 0.35 and s2['wall']['d'] == 6)
        # 4.3
        s0, s1, s2 = S(47 + 0.5), S(47 + 2.6), S(47 + 4.3)
        at(51.3, '4.3: the supplier card (1.0-2.5 s), then the risk card with the hourglass and the empty treatment slot (2.5-4.0 s); two figures',
           s0['risk']['s1'] == 0 and s0['risk']['r1'] == 0 and s1['risk']['s1'] == 1 and s1['risk']['s2'] == 1 and s1['risk']['s3'] == 1 and s1['risk']['r1'] < 0.5
           and s2['risk']['r1'] == 1 and s2['risk']['r2'] == 1 and s2['owner'] and s2['rev'])
        # close
        s = S(52 + 2.0); at(54.0, 'close: she keys a scan by hand again, rows filling slowly; the gate stays closed beside the empty decision slot',
                            s['chk'][0] and s['scan']['m'] == 'page' and 'k' in s['form']['rows'] and 'e' in s['form']['rows'] and s['wall']['m'] == 'close' and s['inStack'] == [True, 0.24])
        bad = [e for e in exp if not e[2]]
        check("staged world follows the shot table at the script's local times", not bad, bad or f'{len(exp)} checks')

        # ---- red only as the fault rings of shots 1.1, 3.1 and 3.2
        red_at = pg.evaluate("""() => { const out = []; for (let k = 0; k < 560; k++) { const t = k / 10; FILM.signature(t);
            const shown = m => { let v = m.visible, q = m.parent; while (v && q) { v = q.visible; q = q.parent; } return v; };
            if (FILM_DOCAI.red.some(shown)) out.push(t); } return out; }""")
        check('red fault rings appear only in shots 1.1 (4-12 s), 3.1 and 3.2 (24-36 s)', red_at and all(4 <= t < 12 or 24 <= t < 36 for t in red_at) and any(t < 12 for t in red_at)
              and any(24 <= t < 30 for t in red_at) and any(30 <= t < 36 for t in red_at), f'{len(red_at)} samples, {red_at[:1]}..{red_at[-1:]}')

        # ---- camera clearance by set
        worst = pg.evaluate("() => { let w = null; for (let t = 12; t < 18; t += 0.1) { const c = FILM.clearance(t); if (!w || c.d < w.d) w = c; } return w; }")
        check('region set (12-18 s): camera >= 2.5 m from every object (padded colliders >= 1.0 m)', worst['d'] >= 1.0, worst)
        rooms = pg.evaluate("() => { let w = null; for (let t = 0; t < 56; t += 0.1) { if (t >= 12 && t < 18) continue; const c = FILM.clearance(t); if (!w || c.d < w.d) w = c; } return w; }")
        check('room sets: camera >= 1.0 m from every collider and person', rooms['d'] >= 1.0, rooms)
        br.close()
    check('no console errors or warnings', not errors, errors[:10])
    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'film': str(FILM), 'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
