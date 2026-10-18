"""Film-specific checks for simulation/cv-screening/CV Screening Assistant.html (issue #4, phase 2).

Usage:  python test/cv-screening_test.py [--write-lines]

The shared controls and layout test (test/film_controls_test.py) covers the player. This test covers what is particular to this
film and its approved script ("CV Screening Assistant - Script and Protocols.md", Part 1):
  - one CONFIG entry per shot of the script's shot table, in order, with the same start and dur
  - beat, setting, headline and support line copied verbatim from the script; scene name "<beat> - <setting>" for the fallback
  - the script's fixed overlay: top-right pill, People / HR violet accent on beats 1-4, neutral cards, fallback title, 0.6 m clearance
  - readability, computed the script's way (whitespace tokens with a letter or digit; Flesch-Kincaid with vowel-group syllables,
    sentences at . ! ?): headline <= 14 words (the shot 3.1 safety question <= 20), support <= 14, grade <= 8 on every line,
    pace <= 5.5 words per second of shot, film total equal to the script's 278 words; source lines <= 10 words (template README)
  - the 26 on-screen lines kept as JSON beside the film (the script asks for it), in step with the film
  - no readable text drawn into the 3D world (no fillText / strokeText in the film)
Grades that differ from the script's own table are reported (not failed), so a stale table value is visible.
Prints a JSON report; exit code 1 on any failure.
"""
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
FILM = ROOT / 'simulation' / 'cv-screening' / 'CV Screening Assistant.html'
SCRIPT = ROOT / 'simulation' / 'cv-screening' / 'CV Screening Assistant - Script and Protocols.md'
LINES = ROOT / 'simulation' / 'cv-screening' / 'CV Screening Assistant - lines.json'
BEATS = {'Open card': 0, 'The situation': 1, 'The AI at work': 2, 'What can go wrong': 3, 'How it is kept safe': 4, 'Close card': 0}
VIOLET, NEUTRAL = '#8e6cc9', '#e8e6e1'


def words(s):
    return [w for w in s.split() if re.search(r'[A-Za-z0-9]', w)]


def grade(s):
    ws = words(s)
    n = len(ws)
    sent = max(1, len(re.findall(r'[.!?]', s)))
    syl = sum(max(1, len(re.findall(r'[aeiouy]+', w.lower()))) for w in ws)
    return n, round(0.39 * n / sent + 11.8 * syl / n - 15.59, 1)


def script_shots():
    """Rows of the Part 1 shot table: #, start, dur, beat, setting, camera, world action, headline, support, traces to."""
    rows = []
    for line in SCRIPT.read_text(encoding='utf-8').splitlines():
        if re.match(r'^\| (0|C|[1-4]\.[1-3]) \| [\d.]+ \| [\d.]+ \|', line):
            c = [x.strip() for x in line.strip().strip('|').split('|')]
            rows.append({'shot': c[0], 'start': float(c[1]), 'dur': float(c[2]), 'beat': c[3], 'setting': c[4], 'head': c[7], 'sup': c[8]})
    return rows


def script_grades():
    """The script's own word-count table: (shot, element) -> (words, FK grade)."""
    out = {}
    for line in SCRIPT.read_text(encoding='utf-8').splitlines():
        m = re.match(r'^\| (0|C|[1-4]\.[1-3]) \| (headline|support)[^|]*\| (\d+) \| [^|]+\| (-?[\d.]+) \|', line)
        if m:
            out[(m.group(1), m.group(2))] = (int(m.group(3)), float(m.group(4)))
    return out


def film_lines(beats):
    out = []
    for b in beats:
        out.append({'shot': b['shot'], 'kind': 'headline', 'text': b['head'], 'limit': 20 if b['shot'] == '3.1' else 14})
        out.append({'shot': b['shot'], 'kind': 'support', 'text': b['sup'], 'limit': 14})
    return out


def main():
    checks, notes = {}, []

    def check(name, ok, detail=''):
        checks[name] = {'ok': bool(ok), 'detail': detail if isinstance(detail, str) else json.dumps(detail, ensure_ascii=False)[:1500]}

    html = FILM.read_text(encoding='utf-8')
    with sync_playwright() as pw:  # FILM_CONFIG is published before WebGL starts, so the text-only path is enough here
        br = pw.chromium.launch(args=['--disable-webgl', '--disable-3d-apis'])
        pg = br.new_page()
        pg.goto(FILM.as_uri(), wait_until='load', timeout=60000)
        pg.wait_for_function('window.FILM && window.FILM_CONFIG', timeout=30000)
        cfg = pg.evaluate('window.FILM_CONFIG')
        br.close()
    beats, shots = cfg['beats'], script_shots()

    check('script table parsed: 13 shots (0, 1.1 ... 4.3, C)', len(shots) == 13, [s['shot'] for s in shots])
    check('one CONFIG entry per script shot, in order', [b.get('shot') for b in beats] == [s['shot'] for s in shots], [b.get('shot') for b in beats])
    bad = []
    for b, s in zip(beats, shots):
        want = {'start': s['start'], 'dur': s['dur'], 'beat': BEATS.get(s['beat']), 'setting': s['setting'], 'head': s['head'], 'sup': s['sup'],
                'name': f"{s['beat']} — {s['setting']}"}
        diff = {k: (b.get(k), v) for k, v in want.items() if b.get(k) != v}
        if diff:
            bad.append({'shot': s['shot'], 'diff': diff})
    check('timing, beat, setting, headline, support and scene name match the script verbatim', not bad, bad or '13 shots')
    check('fixed overlay: top-right pill, title, fallback title',
          cfg['initiative'] == 'Held at the gate · made-up applicants' and cfg['title'] == 'CV Screening Assistant' and cfg['fallbackTitle'] == 'CV Screening Assistant, as it is proposed.',
          {k: cfg[k] for k in ('initiative', 'title', 'fallbackTitle')})
    acc = cfg['accent']
    check('accent: People / HR violet on beats 1-4, neutral paper on the cards', all(acc[str(i)].lower() == VIOLET for i in range(1, 5)) and acc['0'].lower() == NEUTRAL, acc)
    check('camera clearance set to the script\'s 0.6 m', cfg['minClearance'] == 0.6, cfg['minClearance'])
    core = sum(b['dur'] for b in beats if b['beat'] > 0)
    check('runtime: 59 s film, beats 1-4 run 51 s', cfg['duration'] == 59 and core == 51, f'film {cfg["duration"]} s, beats {core} s')

    # readability, computed the script's way
    lines, table, over, total, rows = film_lines(beats), script_grades(), [], 0, []
    for ln in lines:
        n, g = grade(ln['text'])
        total += n
        rows.append({**ln, 'words': n, 'fk': g})
        if n > ln['limit'] or g > 8:
            over.append({'shot': ln['shot'], 'kind': ln['kind'], 'words': n, 'limit': ln['limit'], 'fk': g})
        ref = table.get((ln['shot'], ln['kind']))
        if ref and (ref[0] != n or abs(ref[1] - g) > 0.05):
            notes.append(f'script table for shot {ln["shot"]} {ln["kind"]} says {ref[0]} words / grade {ref[1]}; computed {n} / {g} (still within the limits)' if n <= ln['limit'] and g <= 8 else f'shot {ln["shot"]} {ln["kind"]}: table {ref}, computed {(n, g)}')
    check('every on-screen line within its word limit and at grade 8 or lower', not over, over or f'{len(lines)} lines, max grade {max(r["fk"] for r in rows)}')
    pace = [(b['shot'], round((len(words(b['head'])) + len(words(b['sup']))) / b['dur'], 2)) for b in beats]
    check('pace: at most 5.5 words per second of shot (headline + support)', all(p <= 5.5 for _, p in pace), pace)
    check('film total equals the script\'s 278 words', total == 278, f'{total} words')
    src = [(b['shot'], b.get('source', ''), len(words(b.get('source', '')))) for b in beats if b['beat'] > 0]
    check('source lines present on every beat shot, 10 words or fewer', all(s[1] and s[2] <= 10 for s in src), src)

    # the 26 lines kept beside the film
    doc = {'film': 'CV Screening Assistant', 'script': SCRIPT.name, 'method': 'words: whitespace tokens with a letter or digit; FK grade 0.39*w/s + 11.8*syl/w - 15.59, vowel-group syllables',
           'lines': [{k: r[k] for k in ('shot', 'kind', 'text', 'words', 'limit', 'fk')} | {'client': False} for r in rows]}
    if '--write-lines' in sys.argv:
        LINES.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    kept = json.loads(LINES.read_text(encoding='utf-8')) if LINES.exists() else None
    check('lines JSON beside the film is in step with the film (26 lines)', kept == doc and len(doc['lines']) == 26, 'missing; run with --write-lines' if kept is None else ('in step' if kept == doc else 'differs; re-run with --write-lines'))

    check('no readable text drawn into the 3D world (no fillText / strokeText)', not re.search(r'fillText|strokeText', html), 'film source scanned')

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'film': str(FILM), 'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks, 'notes': notes}, indent=2, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
