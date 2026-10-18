"""Film-specific checks for the Fraud Triage Model film (issue #5, phase 2).

Usage:  python test/fraud-triage_test.py ["simulation/fraud-triage/Fraud Triage Model.html"] [outDir]

The shared test (test/film_controls_test.py) checks the controls, layout, determinism of the snapshot state and clearance.
This test adds what is particular to this film and its approved script, "Fraud Triage Model - Script and Protocols.md":
  - script parity: the 13 scenes match the Part 1 shot table row by row (start, dur, setting, AI Canvas tag, headline,
    support line), and test/fraud-lines.json holds the same 25 on-screen lines
  - readability: words per line within the script's limits, Flesch-Kincaid grade <= 8 on every line (vowel-group
    syllables), reading rate (headline + support words / shot duration) <= 4.5 words per second
  - numbering convention: no digit in any on-screen line; the film accent is violet on every beat, neutral on the cards
  - staging: each shot is filmed in its own set (city block, flat, review desk, systems aisle, board room)
  - camera: at least 2.5 m from every collider and person in the exterior shots (open and close), 1.0 m inside
  - the phone inset: shown only when her phone matters (shots 1.1, 3.3 and the cut-in in 4.1), never in other shots
  - determinism of the picture: the rendered frame at t is the same whatever was shown before (this also covers the film's
    own canvas screens, which FILM.signature does not see)
  - no console errors or warnings, no page errors
Prints a JSON report; exit code 1 on any failure.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
FILM = ROOT / 'simulation' / 'fraud-triage' / 'Fraud Triage Model.html'
SCRIPT = ROOT / 'simulation' / 'fraud-triage' / 'Fraud Triage Model - Script and Protocols.md'
LINES = ROOT / 'test' / 'fraud-lines.json'
GL_ARGS = ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
VIOLET, NEUTRAL = '#8a6fd1', '#e8e6e1'
# the set each shot is filmed in, as a range of camera x (the sets are built far apart along x)
SETS = {'E': (-140, -60), 'A': (-10, 10), 'C': (45, 75), 'B': (105, 135), 'D': (165, 195)}
SHOT_SET = {'Open': 'E', '1.1': 'A', '1.2': 'C', '2.1': 'B', '2.2': 'B', '2.3': 'C', '3.1': 'C', '3.2': 'B', '3.3': 'A',
            '4.1': 'C', '4.2': 'C', '4.3': 'D', 'Close': 'E'}
INSET_SHOWN = [7.0, 9.5, 41.0, 43.5, 47.6, 48.6]          # shots 1.1, 3.3, 4.1 (cut-in 47.0-49.0)
INSET_HIDDEN = [2.0, 12.0, 18.0, 23.0, 27.0, 32.0, 37.0, 45.0, 51.0, 56.0, 61.0]


def words(s):
    return [w for w in s.split() if re.search(r'[A-Za-z0-9]', w)]


def grade(s):
    ws = words(s)
    sentences = max(1, len(re.findall(r'[.!?]', s)))
    syl = sum(max(1, len(re.findall(r'[aeiouy]+', re.sub(r'[^A-Za-z]', '', w).lower()))) for w in ws)
    return 0.39 * len(ws) / sentences + 11.8 * syl / len(ws) - 15.59


def shot_table():
    rows = [l for l in SCRIPT.read_text(encoding='utf-8').splitlines() if re.match(r'^\| (Open|Close|\d\.\d) \| \d', l)]
    out = []
    for r in rows:
        c = [x.strip() for x in r.strip().strip('|').split('|')]
        out.append({'shot': c[0], 'start': float(c[1]), 'dur': float(c[2]), 'setting': c[4], 'tag': '' if c[5] == '—' else c[5],
                    'head': c[8], 'sup': '' if c[9] == '—' else c[9]})
    return out


def main():
    film = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else FILM
    out = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else ROOT / 'test' / 'shots' / 'fraud-triage-specific'
    out.mkdir(parents=True, exist_ok=True)
    checks, errors = {}, []

    def check(name, ok, detail=''):
        checks[name] = {'ok': bool(ok), 'detail': detail if isinstance(detail, str) else json.dumps(detail)[:2000]}

    table = shot_table()
    check('script: the shot table has 13 shots (open, 1.1-4.3, close)', [r['shot'] for r in table] == list(SHOT_SET), [r['shot'] for r in table])

    # ---------------------------------------------------------------- readability and the numbering convention (from the script itself)
    lines_json = json.loads(LINES.read_text(encoding='utf-8'))['lines']
    script_lines = []
    for r in table:
        script_lines.append({'shot': r['shot'], 'text': r['head'], 'limit': 20 if r['shot'] == '3.3' else 14})
        if r['sup']:
            script_lines.append({'shot': r['shot'], 'text': r['sup'], 'limit': 14})
    check('test/fraud-lines.json holds the 25 on-screen lines of the shot table, verbatim',
          len(lines_json) == 25 and [(l['shot'], l['text']) for l in lines_json] == [(l['shot'], l['text']) for l in script_lines],
          f'{len(lines_json)} lines in the JSON, {len(script_lines)} in the script')
    read = [{'shot': l['shot'], 'words': len(words(l['text'])), 'limit': l['limit'], 'grade': round(grade(l['text']), 1), 'text': l['text']} for l in script_lines]
    over = [x for x in read if x['words'] > x['limit'] or x['grade'] > 8]
    total = sum(x['words'] for x in read)
    check('readability: every line within its word limit and at Flesch-Kincaid grade 8 or lower', not over,
          over or f'{len(read)} lines, {total} words, highest grade {max(x["grade"] for x in read)}')
    rates = [(r['shot'], round((len(words(r['head'])) + len(words(r['sup']))) / r['dur'], 2)) for r in table]
    check('reading rate: headline + support words per second <= 4.5 in every shot', all(v <= 4.5 for _, v in rates), rates)
    digits = [l['text'] for l in script_lines if re.search(r'\d', l['text'])]
    check('numbering convention: no digit in any on-screen line', not digits, digits or 'none')

    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=GL_ARGS)
        pg = browser.new_page(viewport={'width': 1280, 'height': 720})
        pg.on('pageerror', lambda e: errors.append(f'pageerror: {e}'))
        pg.on('console', lambda m: errors.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
        pg.goto(film.as_uri(), wait_until='load', timeout=60000)
        pg.wait_for_function('window.FILM && window.FILM.ready === true', timeout=45000)
        pg.evaluate('FILM.pause()')
        cfg = pg.evaluate('window.FILM_CONFIG')
        beats = cfg['beats']

        # ------------------------------------------------------------ script parity, row by row
        diff = []
        for r, b in zip(table, beats):
            want = {'start': r['start'], 'dur': r['dur'], 'setting': r['setting'], 'source': f'AI Canvas: {r["tag"]}' if r['tag'] else '',
                    'head': r['head'], 'sup': r['sup'], 'beat0': r['shot'] in ('Open', 'Close')}
            got = {'start': b['start'], 'dur': b['dur'], 'setting': b.get('setting', ''), 'source': b.get('source', ''),
                   'head': b['head'], 'sup': b.get('sup', ''), 'beat0': b['beat'] == 0}
            bad = {k: (got[k], v) for k, v in want.items() if got[k] != v}
            if r['shot'][0].isdigit() and b['beat'] != int(r['shot'][0]):
                bad['beat'] = (b['beat'], int(r['shot'][0]))
            if bad:
                diff.append({'shot': r['shot'], 'diff': bad})
        check('script parity: every scene matches its shot (start, dur, setting, AI Canvas tag, headline, support line)',
              len(beats) == len(table) and not diff, diff or f'{len(beats)} scenes')
        extra = [b['name'] for b in beats if b.get('note') or b.get('chips') or b.get('cards') or b.get('stages')]
        check('no on-screen text beyond the script (no notes, chips or cards)', not extra, extra or 'none')
        acc = cfg['accent']
        check('accent: violet on beats 1-4, neutral on the open and close cards',
              all(acc[str(n)].lower() == VIOLET for n in (1, 2, 3, 4)) and acc['0'].lower() == NEUTRAL, acc)

        # ------------------------------------------------------------ each shot is staged in its own set
        where = []
        for r, b in zip(table, beats):
            for f in (0.05, 0.5, 0.95):
                cam = pg.evaluate('t => FILM.clearance(t).cam', b['start'] + b['dur'] * f)
                lo, hi = SETS[SHOT_SET[r['shot']]]
                if not lo <= cam[0] <= hi:
                    where.append({'shot': r['shot'], 't': round(b['start'] + b['dur'] * f, 2), 'camX': round(cam[0], 2), 'set': SHOT_SET[r['shot']]})
        check('staging: every shot is filmed in its set (open/close city block, flat, review desk, systems aisle, board room)', not where, where or 'all 13 shots')

        # ------------------------------------------------------------ camera clearance by shot: 2.5 m outdoors, 1.0 m indoors
        worst = []
        ok = True
        for r, b in zip(table, beats):
            need = 2.5 if SHOT_SET[r['shot']] == 'E' else 1.0
            n = int(round(b['dur'] / 0.1))
            ds = pg.evaluate("""([s, n]) => { let w = null; for (let i = 0; i <= n; i++) { const c = FILM.clearance(Math.min(s.start + i * 0.1, s.start + s.dur - 1e-3)); if (!w || c.d < w.d) w = c; } return w; }""", [b, n])
            worst.append({'shot': r['shot'], 'min': round(ds['d'], 2), 'who': ds['who'], 'need': need})
            ok = ok and ds['d'] >= need
        check('camera clearance per shot: >= 2.5 m in the exterior shots, >= 1.0 m in the interior sets (0.1 s steps)', ok, worst)

        # ------------------------------------------------------------ the phone inset
        settle = "!FILM.present().pending && !FILM.present().dirty"   # in the 2D presentation path a seek during a readback is drawn when it completes

        def seek(t):
            pg.evaluate('t => FILM.seek(t)', t)
            pg.wait_for_function(settle, timeout=10000)
        inset_state = lambda t: (seek(t), pg.evaluate("""t => { const e = document.getElementById('inset');
            return e ? { op: parseFloat(getComputedStyle(e).opacity), aria: e.getAttribute('aria-hidden'), tag: e.tagName, text: e.textContent } : null; }""", t))[1]
        shown = [(t, inset_state(t)) for t in INSET_SHOWN]
        hidden = [(t, inset_state(t)) for t in INSET_HIDDEN]
        check('phone inset: shown in shots 1.1, 3.3 and the 4.1 cut-in; hidden in every other shot; glyphs only (a canvas, no text)',
              all(s and s['op'] > 0.9 and s['tag'] == 'CANVAS' and s['aria'] == 'true' and not s['text'] for _, s in shown) and all(s and s['op'] < 0.01 for _, s in hidden),
              {'shown': [(t, s and s['op']) for t, s in shown], 'hidden': [(t, s and s['op']) for t, s in hidden]})
        inset_png = lambda t: (seek(t), pg.evaluate("() => document.getElementById('inset').toDataURL()"))[1]
        a1 = inset_png(48.6)
        b1 = inset_png(47.3)
        inset_png(7.0)
        a2 = inset_png(48.6)
        check('phone inset: the spinner becomes a green tick in the 4.1 cut-in, and its picture is a pure function of t', a1 == a2 and a1 != b1, f'same at 48.6: {a1 == a2}; tick differs from spinner: {a1 != b1}')

        # ------------------------------------------------------------ the rendered frame is a pure function of t (own canvases included)
        def frame(t):
            # the world only: the HTML overlay is hidden while capturing (its text and state are checked by the shared test;
            # its pill edges and backdrop blur vary by a few pixels between captures and would make this check flaky)
            seek(t)
            pg.evaluate("() => { document.getElementById('ui').style.visibility = 'hidden'; }")
            pg.wait_for_timeout(120)
            h = hashlib.sha1(pg.locator('#stage').screenshot()).hexdigest()
            pg.evaluate("() => { document.getElementById('ui').style.visibility = ''; }")
            return h
        probe = [7.6, 13.0, 19.0, 23.4, 26.9, 33.0, 38.0, 42.4, 46.0, 52.5, 56.5, 62.0]
        first = {t: frame(t) for t in probe}
        for t in probe:
            frame((t * 7.3) % cfg['duration'])
        again = {t: frame(t) for t in reversed(probe)}
        differ = [t for t in probe if first[t] != again[t]]
        check('determinism of the picture: the rendered frame at t is identical whatever was shown before', not differ, f'{len(probe)} times; differing at {differ}')
        for t in (6.9, 17.3, 23.6, 38.6, 50.2):
            seek(t)
            pg.wait_for_timeout(150)
            pg.screenshot(path=str(out / f'frame-{t:05.1f}.png'))
        browser.close()

    check('no console errors or warnings, no page errors', not errors, errors[:20])
    failed = [k for k, v in checks.items() if not v['ok']]
    result = {'film': str(film), 'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks, 'errors': errors}
    (out / 'report.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
