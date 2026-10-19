"""Film-specific checks for simulation/demand-forecasting/Demand Forecasting.html (initiative `forecast`, issue #6 phase 2).

Usage:  python test/demand-forecasting_test.py

The shared test (test/film_controls_test.py) checks controls, layout, determinism, clearance and the fallback. This test checks
the film against its approved script, "simulation/demand-forecasting/Demand Forecasting - Script and Protocols.md":
  - one scene per shot of the Part 1 shot table, with the same start, duration, beat, setting, headline and support line (verbatim)
  - scene names as the script sets them (Introduction, "<beat> - <setting>", What comes next) and the fallback title
  - the source line of every beat shot verbatim from the script's "Source lines" table (at most 10 words), none on the cards
  - the script's beat accents and its 2.5 m camera clearance rule
  - the script's word and readability limits: headline and support line 14 words or fewer, Flesch-Kincaid grade 8 or lower,
    reading pace 5.0 words per second of shot or lower, 300 words in all (same formula as the script: vowel-group syllables)
  - no digit in any overlay text the film sets (the beat numeral and the numbered navigation dots are template furniture,
    and the time readout is a clock; no headline, support line, setting or source line carries a digit)
  - camera heights and distances at the script's design parameters (crane heights, the 1.6 m dolly, the orbit radii)
  - no Math.random or Date in the film's CONFIG (frames are a pure function of t)
Prints a JSON report; exit code 1 on any failure.
"""
import json
import math
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
FILM = ROOT / 'simulation' / 'demand-forecasting' / 'Demand Forecasting.html'
SCRIPT = ROOT / 'simulation' / 'demand-forecasting' / 'Demand Forecasting - Script and Protocols.md'
GL_ARGS = ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
BEAT_OF = {'Introduction': 0, 'Introduction (close)': 0, 'The situation': 1, 'The AI at work': 2, 'What can go wrong': 3, 'How it is kept safe': 4}
ACCENT = {0: '#e8e6e1', 1: '#3b7dd8', 2: '#3b7dd8', 3: '#d84a3a', 4: '#3fa34d'}   # script, Part 1 "Beat accents"


def shot_rows():
    """The Part 1 shot table: one dict per row (#, start, dur, beat, setting, headline, support)."""
    rows = []
    for line in SCRIPT.read_text(encoding='utf-8').splitlines():
        if not re.match(r'^\| (Open|Close|\d\.\d) \|', line):
            continue
        cells = [c.strip() for c in line.strip().strip('|').split(' | ')]
        if len(cells) != 10:   # the word-count table further down also starts with shot ids; only the shot table has 10 columns
            continue
        rows.append({'id': cells[0], 'start': float(cells[1]), 'dur': float(cells[2]), 'beat': BEAT_OF[cells[3]], 'setting': cells[4],
                     'head': cells[7], 'sup': cells[8]})
    if len(rows) != 13:   # Open, eleven story shots, Close
        raise ValueError(f'expected 13 shot rows in the script, found {len(rows)}')
    return rows


def source_rows():
    """The Part 1 "Source lines" table: {shot id: exact source line}. Its rows are the only 4-column rows that start with a shot id."""
    out = {}
    for line in SCRIPT.read_text(encoding='utf-8').splitlines():
        if not re.match(r'^\| \d\.\d \|', line):
            continue
        cells = [c.strip() for c in line.strip().strip('|').split(' | ')]
        if len(cells) == 4:
            out[cells[0]] = cells[1]
    if len(out) != 11:   # one per story shot
        raise ValueError(f'expected 11 source-line rows in the script, found {len(out)}')
    return out


def words(s):
    return [w for w in s.split() if re.search(r'[A-Za-z0-9]', w)]


def fk_grade(s):
    ws = words(s)
    sentences = max(1, len(re.findall(r'[.!?]', s)))
    syll = sum(max(1, len(re.findall(r'[aeiouy]+', re.sub(r'[^a-z]', '', w.lower())))) for w in ws)
    return 0.39 * len(ws) / sentences + 11.8 * syll / len(ws) - 15.59


def main():
    checks = {}

    def check(name, ok, detail=''):
        checks[name] = {'ok': bool(ok), 'detail': detail if isinstance(detail, str) else json.dumps(detail)[:1500]}

    rows = shot_rows()
    src = FILM.read_text(encoding='utf-8')
    cfg_src = src[src.index('var CONFIG = {'):src.index('END OF CONFIG')]
    check('CONFIG uses no Math.random or Date (a pure function of t)', not re.search(r'Math\.random|\bDate\b', cfg_src))

    with sync_playwright() as pw:
        br = pw.chromium.launch(args=GL_ARGS)
        pg = br.new_page(viewport={'width': 1280, 'height': 720})
        errors = []
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.goto(FILM.as_uri(), wait_until='load', timeout=60000)
        pg.wait_for_function('window.FILM && window.FILM.ready === true', timeout=45000)
        pg.evaluate('FILM.pause()')
        cfg = pg.evaluate('window.FILM_CONFIG')
        beats = cfg['beats']

        # ---- scenes against the script's shot table
        diffs = []
        if len(beats) != len(rows):
            diffs.append(f'{len(beats)} scenes, script has {len(rows)} shots')
        for r, b in zip(rows, beats):
            for key in ('start', 'dur', 'beat', 'setting', 'head', 'sup'):
                got, want = b.get(key, ''), r[key]
                if (abs(got - want) > 1e-9) if isinstance(want, float) else got != want:
                    diffs.append({'shot': r['id'], 'field': key, 'film': got, 'script': want})
        check('one scene per script shot: start, duration, beat, setting, headline and support line verbatim', not diffs, diffs or f'{len(rows)} shots')
        want_names = ['Introduction' if r['id'] == 'Open' else 'What comes next' if r['id'] == 'Close' else
                      f"{cfg['beatLabels'][r['beat'] - 1]} — {r['setting']}" for r in rows]
        check('scene names as the script sets them (Introduction, "<beat> — <setting>", What comes next)', [b['name'] for b in beats] == want_names, [b['name'] for b in beats])
        srcs = source_rows()
        src_diffs = [{'shot': r['id'], 'film': b.get('source', ''), 'script': srcs.get(r['id'], '')} for r, b in zip(rows, beats) if b.get('source', '') != srcs.get(r['id'], '')]
        check('source line of every beat shot verbatim from the script (none on the open and close cards)', not src_diffs, src_diffs or f'{len(srcs)} source lines')
        check('fallback title is the open headline', cfg['fallbackTitle'] == rows[0]['head'], cfg['fallbackTitle'])
        check('initiative label', cfg['initiative'] == 'Demand Forecasting', cfg['initiative'])
        check('beat accents as the script sets them', all(cfg['accent'][str(n)].lower() == c for n, c in ACCENT.items()), cfg['accent'])
        check('camera clearance rule is the script\'s 2.5 m', abs(cfg['minClearance'] - 2.5) < 1e-9, cfg['minClearance'])

        # ---- the script's word, readability and pace limits
        table, total, bad = [], 0, []
        for r, b in zip(rows, beats):
            nh, ns = len(words(b['head'])), len(words(b['sup']))
            gh, gs = fk_grade(b['head']), fk_grade(b['sup'])
            pace = (nh + ns) / b['dur']
            total += nh + ns
            table.append([r['id'], nh, round(gh, 1), ns, round(gs, 1), round(pace, 2)])
            if nh > 14 or ns > 14 or gh > 8 or gs > 8 or pace > 5.0 + 1e-9:
                bad.append(table[-1])
            src_line = b.get('source', '')
            if b['beat'] and len(words(src_line)) > 10:
                bad.append([r['id'], 'source line over 10 words', src_line])
        check('words: headline and support <= 14 words, FK grade <= 8, pace <= 5.0 words/s, every scene', not bad, bad or table)
        check('words: film total <= 300 (script budget)', total <= 300, f'{total} words')
        digits = [(b['name'], k, b.get(k, '')) for b in beats for k in ('setting', 'head', 'sup', 'source', 'name', 'nav') if re.search(r'\d', b.get(k, ''))]
        check('no digit in any overlay text the film sets (the script allows only the time readout)', not digits, digits or 'none')

        # ---- camera at the script's design parameters (heights in metres, distances to the subject)
        def cam(t):
            return pg.evaluate('t => FILM.clearance(t).cam', t)

        def hdist(c, x, z):
            return math.hypot(c[0] - x, c[2] - z)
        cams = []

        def at(label, t, ok_fn, c=None):
            c = c or cam(t)
            cams.append({'shot': label, 't': t, 'cam': [round(v, 2) for v in c], 'ok': bool(ok_fn(c))})
        at('Open crane starts at 30 m', 0.0, lambda c: abs(c[1] - 30) < 0.3)
        at('Open crane ends at 18 m', 3.999, lambda c: abs(c[1] - 18) < 0.3)
        for t in (4.05, 6.5, 8.95):
            at('1.1 tracking at 12 m, 25 m off the road', t, lambda c: abs(c[1] - 12) < 0.05 and abs(c[2] - 10 - 25) < 0.05)
        for t in (9.05, 11.0, 12.5):
            at('1.2 low dolly at 1.6 m, 6-7 m from the open shop front', t, lambda c: abs(c[1] - 1.6) < 0.05 and 6.0 <= hdist(c, 30, 21.75) <= 7.0)
        for t in (14.05, 18.45):
            at('2.1 at 2.2 m height, about 6 m from the ERP cabinet', t, lambda c: abs(c[1] - 2.2) < 0.05 and 5.5 <= hdist(c, 10.2, -14.9) <= 6.5)
        at('2.2 crane along the pipe at 14 m', 20.0, lambda c: abs(c[1] - 14) < 0.05)
        at('2.2 settles 8 m from the cube at 4 m up', 22.99, lambda c: abs(c[1] - 4) < 0.05 and abs(hdist(c, 2, -46) - 8) < 0.4)
        at('2.3 over-shoulder about 3 m behind the planner', 23.05, lambda c: 2.7 <= hdist(c, 0, -2.15) <= 3.3)
        at('2.3 crane ends at 15 m', 27.999, lambda c: abs(c[1] - 15) < 0.3)
        at('3.1 high crane starts at 14 m', 28.0, lambda c: abs(c[1] - 14) < 0.05)
        at('3.1 high crane ends at 22 m', 32.999, lambda c: abs(c[1] - 22) < 0.3)
        for t in (33.05, 35.0, 36.95):
            at('3.2 orbit at 7 m and 3.5 m up around the cube', t, lambda c: abs(c[1] - 3.5) < 0.05 and abs(hdist(c, 2, -46) - 7) < 0.05)
        at('3.3 wide through the open roof at 9 m', 37.05, lambda c: abs(c[1] - 9) < 0.1)
        at('3.3 push-in ends about 4 m behind the desk', 41.999, lambda c: 3.6 <= hdist(c, 0, -3.0) <= 4.4)
        at('4.1 about 5 m from the desk, 3 m up and over', 42.05, lambda c: abs(c[1] - 3.3) < 0.05 and 4.5 <= hdist(c, -14, -14.6) <= 5.5)
        at('4.2 over-shoulder as in 2.3', 46.55, lambda c: 2.7 <= hdist(c, 0, -2.15) <= 3.3)
        at('4.3 starts 9 m above the office', 51.05, lambda c: abs(c[1] - 9) < 0.1)
        at('4.3 crane ends at 16 m', 55.999, lambda c: abs(c[1] - 16) < 0.3)
        at('Close pull back from 16 m', 56.0, lambda c: abs(c[1] - 16) < 0.05)
        at('Close pull back to 24 m', 59.999, lambda c: abs(c[1] - 24) < 0.3)
        check('camera heights and distances match the script\'s design parameters', all(c['ok'] for c in cams), [c for c in cams if not c['ok']] or f'{len(cams)} samples')
        check('no page errors', not errors, errors[:5])
        br.close()

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'film': str(FILM), 'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
