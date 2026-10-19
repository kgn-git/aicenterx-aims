"""Film-specific checks for simulation/credit-scoring/Retail Credit Risk Scoring.html (issue #2, phase 2).

Usage:  python test/credit-scoring_test.py [--write-lines]

The shared test (test/film_controls_test.py) covers controls, layout, determinism, clearance and the fallback. This test checks
the film against its approved script, "Retail Credit Risk Scoring - Script and Protocols.md":
  - one scene per shot-table row, with the same start, dur, beat, setting, headline and support line (verbatim) and accent
  - every beat scene's source line equals the script's source-line table (cards have none); the initiative label top right
  - the fallback title is the open headline; every fallback entry names its beat and setting
  - the word-count and readability limits of Part 1: headline and support line <= 14 words each, Flesch-Kincaid grade <= 8,
    reading pace <= 5.5 words per second, 300 words in total; no digits on screen except the record's "90" and "30"
  - the staged world follows the shot table at the script's local times (read through the film's debug hook window.FILM_RCR):
    the app submits then spins; in shot 6 a clear approval passes into the chute untouched (0-1.0 s), Nadia's referral card lands
    in the underwriter's tray (1.0 s), the underwriter takes the decline at 2.5 s and the app shows the decline at 3.5 s; the
    agent's reason slots are empty with a red ring in shot 7 and the call is logged as a complaint (3.5-4.5 s), and filled in
    shot 10; the drift steps out of its band in shot 8 with no alert, and a model-risk analyst lays the month-end figures beside
    the chart and points to the gap (2.5-3.5 s); the third cohort bar turns amber in shot 9; the weekly check raises the amber
    alert in shot 11, the challenger waits beside an empty sign-off box and the window slides three segments; six people sit at
    the board in shot 12 and the 30-day ring fills once; the close shows the decline and the pending review ticket
  - the decline notice shows the bureau searched and a number to call, but no reasons (SA3)
  - red (a recorded fault) appears only in beat 3; a decline is never drawn in red
  - the camera keeps >= 1.5 m from every object of the abstract set (its colliders are padded by 0.9 m, checked at >= 0.6 m),
    and >= 0.9 m from every human figure in the room sets (measured to each figure's meshes)
--write-lines writes test/credit-scoring-lines.json (every on-screen line with its words, grade and pace), as the script asks.
Prints a JSON report; exit code 1 on any failure.
"""
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
FILM = ROOT / 'simulation' / 'credit-scoring' / 'Retail Credit Risk Scoring.html'
SCRIPT = ROOT / 'simulation' / 'credit-scoring' / 'Retail Credit Risk Scoring - Script and Protocols.md'
LINES = ROOT / 'test' / 'credit-scoring-lines.json'
GL_ARGS = ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
ACCENT = {'neutral': '#e8e6e1', 'credit blue': '#4a7fd4', 'red': '#d84a3a', 'green': '#3fa34d'}
BEATS = {'Open': 0, 'The situation': 1, 'The AI at work': 2, 'What can go wrong': 3, 'How it is kept safe': 4, 'Close': 0}


def shot_table():
    rows = []
    for line in SCRIPT.read_text(encoding='utf-8').splitlines():
        m = re.match(r'^\| (\d+) \| (\d+) \| (\d+) \| ', line)
        if not m:
            continue
        c = [x.strip() for x in line.strip().strip('|').split('|')]
        rows.append({'n': int(c[0]), 'start': float(c[1]), 'dur': float(c[2]), 'beat': BEATS[c[3]], 'setting': c[4].strip('`'),
                     'head': c[7], 'sup': c[8], 'accent': ACCENT[c[9]]})
    return rows


def source_table():
    # Part 1 "Source lines" table: | shot | `source line` | record it names |
    out = {}
    for line in SCRIPT.read_text(encoding='utf-8').splitlines():
        m = re.match(r'^\| (\d+) \| `([^`]+)` \| [^|]+\|\s*$', line)
        if m:
            out[int(m.group(1))] = m.group(2)
    return out


def words(s):
    return [w for w in s.split() if re.search(r'[A-Za-z0-9]', w)]


def grade(s):
    ws = words(s)
    sentences = max(1, len(re.findall(r'[.!?]', s)))
    syl = sum(max(1, len(re.findall(r'[aeiouy]+', w.lower()))) for w in ws)
    return 0.39 * len(ws) / sentences + 11.8 * syl / len(ws) - 15.59


# world state at film time t, read through the film's debug hook after FILM.signature(t) has staged that exact frame
STATE_JS = """t => { FILM.pause(); FILM.signature(t); const o = window.FILM_RCR, w = s => JSON.parse(JSON.stringify(s.want));
  const vis = n => Object.keys(o.sets).filter(k => o.sets[k].visible);
  return { sets: vis(), hand: w(o.handPhone), table: w(o.tablePhone), tableShown: o.tableP.visible, ticket13: o.ticket13.visible,
    oldPhone: w(o.oldPhone), markA: o.markA.visible, markB: o.markB.visible, uw: w(o.uwMon), pip: w(o.pip), agent: w(o.agentMon), inset: o.f7.visible,
    ticket: o.ticket.visible, ticketPos: [o.ticket.position.x, o.ticket.position.y, o.ticket.position.z], chart: w(o.chart), fair: w(o.fair),
    lamp: '#' + o.lampM.emissive.getHexString(), lampI: o.lampM.emissiveIntensity, alertTok: o.alertTok.visible, shadow: w(o.shadow), board: w(o.board),
    analyst: o.rk3.visible, needle: o.needle.rotation.z, wallet: o.wallet.position.x,
    autoTick: o.autoTick.visible, autoTickX: o.autoTick.position.x, refCard: o.refCard.visible, refCardY: o.refCard.position.y,
    complaint: o.complaint.visible, complaintY: o.complaint.position.y, sheet: o.sheet.visible, sheetS: o.sheet.scale.x,
    rk2: [o.rk2.position.x, o.rk2.position.z], rk2arm: o.rk2.userData.ra.rotation.x, pipShown: o.pipF.visible,
    members: o.members.filter(m => m.visible).length }; }"""


def main():
    checks = {}

    def check(name, ok, detail=''):
        checks[name] = {'ok': bool(ok), 'detail': detail if isinstance(detail, str) else json.dumps(detail)[:1500]}

    rows = shot_table()
    check('script: shot table parsed (13 shots)', len(rows) == 13, f'{len(rows)} rows')
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

        # ---- the film against the script, scene by scene
        diff = []
        for r, b in zip(rows, beats):
            want = {'start': r['start'], 'dur': r['dur'], 'beat': r['beat'], 'setting': r['setting'], 'head': r['head'], 'sup': r['sup'], 'accent': r['accent']}
            got = {'start': b['start'], 'dur': b['dur'], 'beat': b['beat'], 'setting': b['setting'], 'head': b['head'], 'sup': b.get('sup', ''), 'accent': cfg['accent'][str(b['beat'])].lower()}
            bad = {k: (got[k], v) for k, v in want.items() if got[k] != v}
            if bad:
                diff.append({'shot': r['n'], 'diff': bad})
        check('every scene matches its shot: start, dur, beat, setting, headline, support line (verbatim), accent', len(beats) == len(rows) and not diff, diff or f'{len(beats)} scenes')
        core = sum(b['dur'] for b in beats if b['beat'])
        per_beat = [sum(b['dur'] for b in beats if b['beat'] == n) for n in (1, 2, 3, 4)]
        check('runtime: 59 s; beats 8 / 14 / 14 / 15 s (51 s); cards 4 s each', cfg['duration'] == 59 and core == 51 and per_beat == [8, 14, 14, 15] and beats[0]['dur'] == 4 and beats[-1]['dur'] == 4, f'film {cfg["duration"]} beats {per_beat}')
        src_want = source_table()
        src_diff = [{'shot': r['n'], 'film': b.get('source', ''), 'script': src_want.get(r['n'], '')} for r, b in zip(rows, beats)
                    if b.get('source', '') != src_want.get(r['n'], '')]
        check("source line of every scene matches the script's source-line table (none on the cards); initiative label",
              len(src_want) == 11 and not src_diff and cfg.get('initiative') == 'Retail Credit Risk Scoring', src_diff or f'{len(src_want)} source lines')
        check('fallback title is the open headline', cfg['fallbackTitle'] == rows[0]['head'], cfg['fallbackTitle'])
        check('each beat scene is named "<beat> — <setting>"; cards Introduction and Close',
              all((b['name'] == f'{cfg["beatLabels"][b["beat"] - 1]} — {b["setting"]}') if b['beat'] else b['name'] in ('Introduction', 'Close') for b in beats), [b['name'] for b in beats])

        # ---- words, readability, pace, digits
        lines, over = [], []
        for r, b in zip(rows, beats):
            hw, sw = len(words(b['head'])), len(words(b.get('sup', '')))
            pace = (hw + sw) / b['dur']
            item = {'shot': r['n'], 'setting': b['setting'], 'head': b['head'], 'sup': b.get('sup', ''), 'headWords': hw, 'supWords': sw,
                    'gradeHead': round(grade(b['head']), 1), 'gradeSup': round(grade(b['sup']), 1), 'wordsPerSecond': round(pace, 2), 'source': b.get('source', '')}
            lines.append(item)
            if hw > 14 or sw > 14 or item['gradeHead'] > 8.0 or item['gradeSup'] > 8.0 or pace > 5.5 + 1e-9:
                over.append(item)
            if b.get('source') and len(words(b['source'])) > 10:
                over.append({'shot': r['n'], 'source too long': b['source']})
        total = sum(x['headWords'] + x['supWords'] for x in lines)
        check('words: headline and support <= 14 words, grade <= 8, pace <= 5.5 words/s, source line <= 10 words', not over, over or f'max grade {max(max(x["gradeHead"], x["gradeSup"]) for x in lines)}')
        check('words: 300 headline and support words in total (script table)', total == 300, f'{total} words')
        digits = sorted({d for b in beats for s in (b['head'], b.get('sup', ''), b.get('source', ''), b['setting']) for d in re.findall(r'\d+', s)})
        check('digits on screen only from the record ("90" days, "30" days)', digits == ['30', '90'], digits)
        if '--write-lines' in sys.argv:
            LINES.write_text(json.dumps({'film': FILM.name, 'script': SCRIPT.name, 'totalWords': total, 'lines': lines}, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

        # ---- the staged world at the script's local times
        S = lambda t: pg.evaluate(STATE_JS, t)
        exp = []

        def at(t, label, ok):
            exp.append((round(t, 2), label, bool(ok)))
        sets = ['kit', 'kit', 'old', 'abs', 'abs', 'cc', 'cc', 'risk', 'risk', 'cc', 'risk', 'board', 'kit']
        for b, s in zip(beats, sets):
            st = S(b['start'] + b['dur'] / 2)
            at(b['start'] + b['dur'] / 2, f'set {s} alone on screen', st['sets'] == [s])
        s = S(4 + 1.0); at(5.0, 'shot 2: the loan-size slider moves', s['hand']['mode'] == 'form' and 0.3 < s['hand']['s'] < 0.62)
        s = S(4 + 2.1); at(6.1, 'shot 2: submit is tapped', s['hand'].get('tap') is True)
        s = S(4 + 3.0); at(7.0, 'shot 2: the spinner starts', s['hand']['mode'] == 'spin')
        s = S(8 + 1.0); at(9.0, 'shot 3: no marks yet', not s['markA'] and not s['markB'])
        s = S(8 + 3.0); at(11.0, 'shot 3: two marks on one file; the inset phone goes dark', s['markA'] and s['markB'] and s['oldPhone']['mode'] == 'off')
        s0, s1 = S(16 + 1.0), S(16 + 2.8); at(18.8, 'shot 5: the wallet rides the slider and the needle only rises', s1['wallet'] > s0['wallet'] + 0.5 and s1['needle'] < s0['needle'])
        s0, s1 = S(21 + 0.2), S(21 + 0.6); at(21.6, 'shot 6: a clear approval (green tick) passes the desk without stopping', s0['autoTick'] and s1['autoTick'] and s1['autoTickX'] < s0['autoTickX'] - 0.5)
        s = S(21 + 1.1); at(22.1, "shot 6: the approval has gone into the chute; Nadia's referral card has landed in the tray", not s['autoTick'] and s['refCard'] and abs(s['refCardY'] - 0.81) < 0.01)
        s = S(21 + 2.0); at(23.0, 'shot 6: not yet decided; the app still waits', s['uw']['dec'] is False and s['pip']['mode'] == 'spin' and s['pipShown'])
        s = S(21 + 2.7); at(23.7, 'shot 6: the underwriter takes the decline at 2.5 s', s['uw']['dec'] is True)
        s = S(21 + 3.7); at(24.7, 'shot 6: the app shows the decline at 3.5 s', s['pip']['mode'] == 'decl')
        s = S(26 + 1.0); at(27.0, 'shot 7: Nadia calls (inset); reason slots empty; no ring yet', s['inset'] and s['agent']['full'] is False and s['agent']['red'] == 0 and not s['pipShown'])
        s = S(26 + 3.0); at(29.0, 'shot 7: a red ring pulses round the empty slots; no complaint logged yet', s['agent']['full'] is False and s['agent']['red'] > 0.4 and not s['complaint'])
        s = S(26 + 4.7); at(30.7, 'shot 7: the call is logged; the amber complaint card is in the complaints tray', s['complaint'] and abs(s['complaintY'] - 0.785) < 0.01)
        s = S(31 + 0.5); at(31.5, 'shot 8: approvals still in band', s['chart']['drift'] == 0)
        s = S(31 + 2.2); at(33.2, 'shot 8: the line steps out (four grid steps); red ring; the lamp stays dark; no figures sheet yet', s['chart']['drift'] == 1 and s['chart']['red'] > 0.4 and s['lampI'] < 0.2 and not s['sheet'])
        s = S(31 + 3.6); at(34.6, 'shot 8: no alert; an analyst has laid the month-end figures by the chart and points to the gap', s['lampI'] < 0.2 and not s['alertTok'] and s['sheet'] and s['sheetS'] > 0.99 and s['rk2arm'] < -1.2 and abs(s['rk2'][0] - 157.0) < 0.01)
        s = S(35 + 0.3); at(35.3, 'shot 9: bars not risen yet', s['fair']['b'] == [0, 0, 0])
        s = S(35 + 3.4); at(38.4, 'shot 9: two bars green, the third amber, red ring, flag; the analyst at the panel',
                            s['fair']['col'] == ['#3fa34d', '#3fa34d', '#e9a23b'] and s['fair']['red'] > 0.4 and s['fair']['flag'] > 0.9 and s['analyst'])
        s = S(40 + 1.5); at(41.5, 'shot 10: the reasons are on screen with the reading guide; no red', s['agent']['full'] is True and s['agent']['book'] is True and s['agent']['red'] == 0 and s['agent']['hi'] >= 0)
        s = S(40 + 4.8); at(44.8, "shot 10: the review ticket is in the underwriting team's referral tray", s['agent']['rev'] is True and s['ticket'] and abs(s['ticketPos'][0] - 122.8) < 0.05 and abs(s['ticketPos'][2] + 2.25) < 0.05)
        s = S(45 + 0.6); at(45.6, 'shot 11: before the first tick after the marker, no alert', s['chart']['alert'] is False and not s['alertTok'])
        s = S(45 + 1.6); at(46.6, 'shot 11: the weekly check raises the amber alert; the lamp turns amber', s['chart']['alert'] is True and s['alertTok'] and s['lamp'] == '#e9a23b')
        s = S(45 + 3.0); at(48.0, 'shot 11: the challenger runs in the shadow beside an empty sign-off box; window not yet moved', s['shadow']['k'] > 0.9 and s['shadow']['so'] > 0.9 and s['shadow']['sh'] == 0)
        s = S(45 + 4.7); at(49.7, 'shot 11: the training window slides three segments', s['shadow']['sh'] == 3)
        s0, s1 = S(50 + 0.5), S(50 + 4.0); at(54.0, 'shot 12: six people at the board; the 30-day ring fills once', s1['members'] == 6 and s0['board']['k'] == 0 and s1['board']['k'] == 30)
        s = S(55 + 2.0); at(57.0, 'close: the phone on the table shows the decline; the review ticket waits', s['tableShown'] and s['table']['mode'] == 'decl' and s['ticket13'])
        bad = [e for e in exp if not e[2]]
        check('staged world follows the shot table at the script\'s local times', not bad, bad or f'{len(exp)} checks')

        # ---- colour rules: red only in beat 3; a decline is slate
        red_at = pg.evaluate("""() => { const out = []; for (let k = 0; k < 590; k++) { const t = k / 10; FILM.signature(t); const o = window.FILM_RCR;
            if ((o.agentMon.want.red || 0) > 0 || (o.chart.want.red || 0) > 0 || (o.fair.want.red || 0) > 0) out.push(t); } return out; }""")
        check('red fault rings appear only in beat 3 (26-40 s)', red_at and all(26 <= t < 40 for t in red_at), f'{len(red_at)} samples, {red_at[:1]}..{red_at[-1:]}')
        src = FILM.read_text(encoding='utf-8')  # the painters are private to the film's closure, so this rule is checked in the source
        check('a decline is drawn slate, never red', "slate:'#7a8691'" in src and "rcG(c, 'bar', W*0.5, H*0.37, W*0.25, null, { disc:RC.slate })" in src
              and "rcG(c, 'bar', W*0.25, H*0.3, H*0.1, null, { disc:RC.slate })" in src, 'phone and agent-screen decline glyphs')
        check('the decline notice shows the bureau searched and a number to call, but no reasons (SA3)',
              "rcG(c, 'bureau', W*0.3, H*0.7, W*0.13, '#33414c', { bg:RC.paper });" in src
              and "rcG(c, 'handset', W*0.7, H*0.7, W*0.15, null, { disc:RC.blue });" in src, 'phone decl mode')

        # ---- abstract set: the camera keeps >= 1.5 m from every object (padded colliders >= 0.6 m)
        worst = pg.evaluate("() => { let w = null; for (let t = 12; t < 21; t += 0.1) { const c = FILM.clearance(t); if (!w || c.d < w.d) w = c; } return w; }")
        check('abstract set (12-21 s): camera >= 1.5 m from every object', worst['d'] >= 0.6, worst)
        rooms = pg.evaluate("() => { let w = null; for (let t = 0; t < 59; t += 0.1) { if (t >= 12 && t < 21) continue; const c = FILM.clearance(t); if (!w || c.d < w.d) w = c; } return w; }")
        check('room sets: camera >= 0.6 m from every collider and person', rooms['d'] >= 0.6, rooms)
        # the script's Part 1 conventions also keep the camera >= 0.9 m from every human figure; FILM.clearance measures people from
        # the body centre, so here the distance is taken to each visible mesh of each figure (its own oriented bounding box)
        people = pg.evaluate("""() => {
            let root = window.FILM_RCR.nadia; while (root.parent) root = root.parent;
            const figs = []; root.traverse(x => { if (x.userData && x.userData.kind === 'person') figs.push(x); });
            let w = null;
            for (let k = 0; k < 590; k++) { const t = k / 10; const c = FILM.clearance(t), cam = window.FILM_RCR.nadia.position.clone().set(c.cam[0], c.cam[1], c.cam[2]);
              figs.forEach(f => { let v = f.visible, q = f.parent; while (v && q) { v = q.visible; q = q.parent; } if (!v) return;
                f.traverse(m => { if (!m.isMesh || !m.visible) return; if (!m.geometry.boundingBox) m.geometry.computeBoundingBox();
                  const l = cam.clone().applyMatrix4(m.matrixWorld.clone().invert()); m.geometry.boundingBox.clampPoint(l, l); l.applyMatrix4(m.matrixWorld);
                  const d = l.distanceTo(cam); if (!w || d < w.d) w = { t: +t.toFixed(1), d: +d.toFixed(3) }; }); }); }
            return Object.assign({ figures: figs.length }, w); }""")
        check('room sets: camera >= 0.9 m from every human figure (script Part 1)', people['d'] >= 0.9, people)
        br.close()
    check('no console errors or warnings', not errors, errors[:10])
    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'film': str(FILM), 'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
