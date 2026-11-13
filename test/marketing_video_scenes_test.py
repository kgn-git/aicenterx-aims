"""Test for how the marketing video's four beats follow the narration: video/src/scenes/*.tsx and the timings they
take from video/src/moments.mjs, against video/src/captions.json.

Usage:  python test/marketing_video_scenes_test.py

A scene times its figures, cards and ticks to the narration. moments.mjs names the words it waits for, and stops with
an error when a phrase is no longer said, so running it on the real captions proves every phrase is there. Checks:
  - no scene and not moments.mjs indexes its cues by number (cues[2], cues.at(2))
  - each scene is exactly one of world, break, fix and proof, and plays its stock footage through <Footage>
  - the moments of each beat, computed by moments.mjs through node from the real timeline and captions, measured to
    the start of the 0.3 s crossfade out of the scene:
      - world: the footage plays alone for at least 0.3 s, then 56% lands within 0.3 s of its number being said
      - break: 40%+ then ~5% land within 0.3 s of their numbers, the footage cuts from the whiteboard to the desk
        between them, and "The risks show up too late" lands at least 0.5 s after ~5% and holds 1 s
      - fix: the team footage gives way to the product as "simulate" is said; the risk cards land after the click,
        their AIID and MIT chips light as "documented incidents" and "industry standards" are said, once every card is
        up; each tick lands after its card; the mitigations open as "select" is said, and their ticks land after their
        rows and end at least 0.5 s before the crossfade; a fix too short for its ticks stops with an error naming it
      - proof: "< 10 min" lands on the first words, the brand card as "AI Center X" is said, and the footer reads
        for at least 2 s
      - a world line that no longer says its figure, and a break that says its figures out of order, each stop with
        an error naming the words
  - each scene uses what moments.mjs gives it, and takes its footage from shots() there
  - no clip runs out while it is on screen: each shot, from when it appears to when it leaves or the scene ends, fits
    the clip's recorded length from its start second, at its playback rate; <Footage> starts a clip when it appears
    rather than at the scene's start, so a clip cut to mid-scene is not already spent
  - the user's motion choices: a button presses to 0.96 and back within 120 ms, from the one definition in
    moments.mjs that kit.tsx uses
  - the fix marks its risk cards and mitigation rows with their own accents (STAGE.risks, STAGE.mitigations), and
    secondary text uses the brighter mutedInk rather than the prototype's inkMuted anywhere in video/src
Prints a JSON report; exit code 1 on any failure.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'video' / 'src'
SCENES = SRC / 'scenes'
CAPTIONS = SRC / 'captions.json'
TIMELINE = SRC / 'timeline.json'
THEME = SRC / 'theme.ts'
KIT = SRC / 'ui' / 'kit.tsx'
MOMENTS = SRC / 'moments.mjs'
FOOTAGE = SRC / 'footage.json'
FOOTAGE_UI = SRC / 'ui' / 'Footage.tsx'
TIMING = SRC / 'timing.mjs'
# TAIL in video/src/timing.mjs: the crossfade that starts this long before a scene's cut.
CROSSFADE = 0.3
FIGURE_SLACK, LIGHT_ALONE, LATE_AFTER, HOLD, READ, TICKS_DONE = 0.3, 0.3, 0.5, 1.0, 2.0, 0.5
# A fix scene too short for its montage.
CRAMPED = 6.0
PRESS, PRESS_SCALE = 0.12, 0.96
BEATS = {'World.tsx', 'Break.tsx', 'Fix.tsx', 'Proof.tsx'}
# {scene file: what it must call and use from moments.mjs}.
USERS = {'World.tsx': ('worldMoments(', 'm.figure', 'shots(', '<Footage'),
         'Break.tsx': ('breakMoments(', 'm.figures[i]', 'm.cut', 'm.late', 'shots(', '<Footage'),
         'Fix.tsx': ('fixMoments(', 'm.productAt', 'm.cards', 'm.named', 'm.ticks', 'm.rows', 'm.rowTicks', 'shots(',
                     '<Footage', 'accent={STAGE.risks}', 'accent={STAGE.mitigations}'),
         'Proof.tsx': ('proofMoments(', 'm.badge', 'm.brandAt', 'm.footer', 'shots(', '<Footage')}
# What <Footage> must do so a clip plays from its start second at the moment it appears, at its rate.
STARTS_ON_ENTRY = ('<Sequence', 'playbackRate')
SPOKEN = {'world': ['Fifty-six per cent'], 'break': ['forty per cent', 'five per cent']}
PROGRAM = """
import {readFileSync} from "node:fs";
import * as m from %(moments)s;
import {sceneSeconds} from %(timing)s;
const timeline = JSON.parse(readFileSync(%(timeline)s, "utf8"));
const captions = JSON.parse(readFileSync(%(captions)s, "utf8"));
const scenes = Object.fromEntries(timeline.scenes.map((s) => [s.id, s]));
const spoken = %(spoken)s;
const attempt = (f) => { try { return f(); } catch (e) { return {error: String(e.message)}; } };
const at = (id, f, seconds) => attempt(() => {
  const scene = scenes[id], cues = m.sceneCues(captions, timeline, id), length = seconds ?? sceneSeconds(scene);
  const end = cues[cues.length - 1].end;
  const said = (p) => m.spokenAt(scene.narration, p, end);
  return {seconds: length, said: Object.fromEntries((spoken[id] ?? []).map((p) => [p, said(p)])),
    words: Object.fromEntries(["simulate", "documented incidents", "industry standards", "select", "AI Center X"]
      .filter((p) => scene.narration.includes(p)).map((p) => [p, said(p)])), ...f(scene, cues, length)};
});
const out = {consts: {PRESS: m.PRESS, PRESS_SCALE: m.PRESS_SCALE}};
out.world = at("world", (s, c) => m.worldMoments(s, c));
out.break = at("break", (s, c) => m.breakMoments(s, c));
out.fix = at("fix", (s, c, n) => m.fixMoments(s, c, n));
out.proof = at("proof", (s, c, n) => m.proofMoments(s, c, n));
out.shots = Object.fromEntries(timeline.scenes.map((s) => [s.id, at(s.id, (x, c, n) => ({list: m.shots(x, c, n)}))]));
out.cramped = at("fix", (s, c, n) => m.fixMoments(s, c, n), %(cramped)s);
out.reworded = at("world", (s, c) => m.worldMoments({...s, narration: s.narration.replace("Fifty-six per cent", "Most")}, c));
out.swapped = at("break", (s, c) => {
  const [a, b, ...rest] = s.narration.split(". ");
  return m.breakMoments({...s, narration: [b, a, ...rest].join(". ")}, c);
});
console.log(JSON.stringify(out));
"""
NUMBERED = re.compile(r'\bcues(\[\d+\]|\.at\()')


def near(got, want):
    return abs(got - want) <= FIGURE_SLACK


def beat_problems(got):
    """Each AC limit the computed moments of the four beats break."""
    bad = []
    for sid in ('world', 'break', 'fix', 'proof'):
        if 'error' in got.get(sid, {'error': 'missing'}):
            bad.append(f'{sid}: {got.get(sid, {}).get("error", "missing")}')
    if bad:
        return bad
    w, b, f, p = (got[k] for k in ('world', 'break', 'fix', 'proof'))
    if w['figure'] < LIGHT_ALONE or not near(w['figure'], max(w['said']['Fifty-six per cent'], LIGHT_ALONE)):
        bad.append(f'world: 56% must land on its number after {LIGHT_ALONE} s of footage, got {w}')
    want = [b['said']['forty per cent'], b['said']['five per cent']]
    if len(b['figures']) != 2 or not all(near(x, y) for x, y in zip(b['figures'], want)):
        bad.append(f'break: the figures must land on their numbers {want}, got {b["figures"]}')
    elif not b['figures'][0] < b['cut'] < b['figures'][1]:
        bad.append(f'break: the footage must cut between the figures, got {b["cut"]}')
    if b['late'] - b['figures'][-1] < LATE_AFTER or b['seconds'] - CROSSFADE - b['late'] < HOLD:
        bad.append(f'break: "The risks show up too late" must follow ~5% by {LATE_AFTER} s and hold {HOLD} s, got {b}')
    cards, ticks, rows, row_ticks = f['cards'], f['ticks'], f['rows'], f['rowTicks']
    if not near(f['productAt'], f['words']['simulate']) or f['click'] < f['productAt'] or cards[0] <= f['click']:
        bad.append(f'fix: the product must arrive on "simulate", its click before the first card, got {f}')
    if not (near(f['named'][0], f['words']['documented incidents']) and near(f['named'][1], f['words']['industry standards'])
            and f['named'][0] >= cards[-1]):
        bad.append(f'fix: the chips must light as their sources are named, once the cards are up, got {f["named"]}')
    saved = f['savedAt']
    if ticks != sorted(ticks) or any(t < cards[i] + 0.2 for t, i in zip(ticks, saved)):
        bad.append(f'fix: each risk tick must follow its card, got {ticks} for cards {cards}')
    if not near(f['mitClick'], f['words']['select']) or rows[0] <= f['mitClick'] or row_ticks[0] < rows[-1]:
        bad.append(f'fix: the mitigations must open on "select" and be ticked once they are up, got {f}')
    if f['seconds'] - CROSSFADE - row_ticks[-1] < TICKS_DONE:
        bad.append(f'fix: the last tick lands {f["seconds"] - CROSSFADE - row_ticks[-1]:.2f} s before the crossfade, want {TICKS_DONE} s')
    if 'fix' not in got.get('cramped', {}).get('error', ''):
        bad.append(f'a {CRAMPED} s fix must stop with an error naming it, got {got.get("cramped")}')
    if p['badge'] > 0.5 or not near(p['brandAt'], p['words']['AI Center X']) or p['seconds'] - p['footer'] < READ:
        bad.append(f'proof: the badge opens it, the brand lands on "AI Center X" and the footer reads {READ} s, got {p}')
    if 'no longer says "Fifty-six per cent"' not in got.get('reworded', {}).get('error', ''):
        bad.append(f'a world line without its figure must stop with an error naming it, got {got.get("reworded")}')
    if 'in that order' not in got.get('swapped', {}).get('error', ''):
        bad.append(f'a break that says its figures out of order must stop with an error, got {got.get("swapped")}')
    return bad


def shot_problems(shots, timeline, clips):
    """Each shot that plays the wrong clip or outlasts its clip while on screen."""
    bad = []
    for scene in timeline['scenes']:
        got = shots.get(scene['id'], {'error': 'missing'})
        if 'error' in got:
            bad.append(f'{scene["id"]}: {got["error"]}')
            continue
        if [s['clip'] for s in got['list']] != scene['dataRefs']['footage']:
            bad.append(f'{scene["id"]}: plays {[s["clip"] for s in got["list"]]}, not its footage {scene["dataRefs"]["footage"]}')
            continue
        for s in got['list']:
            clip = clips[s['clip']]
            shown = s.get('to', got['seconds']) - s['from']
            lasts = (clip['seconds'] - clip['from']) / clip['rate']
            if shown > lasts:
                bad.append(f'{scene["id"]}: {s["clip"]} is on screen {shown:.2f} s but lasts {lasts:.2f} s, so it freezes')
    return bad


def main():
    checks = {}

    def check(name, problems):
        checks[name] = {'ok': not problems, 'detail': json.dumps(problems)[:1500] if problems else 'sound'}

    sources = {p.name: p.read_text(encoding='utf-8') for p in sorted(SCENES.glob('*.tsx'))}
    moments = MOMENTS.read_text(encoding='utf-8') if MOMENTS.is_file() else ''
    check('no scene and not moments.mjs indexes its cues by number',
          [f'{name}: cues{m}' for name, src in {**sources, 'moments.mjs': moments}.items() for m in NUMBERED.findall(src)])
    check('the scenes are exactly the four beats', [] if set(sources) == BEATS else [sorted(sources)])
    root = (SRC / 'Root.tsx').read_text(encoding='utf-8')
    check('every beat uses its moments from moments.mjs and plays its footage',
          [f'{name} does not use {token}' for name, tokens in USERS.items() for token in tokens
           if token not in sources.get(name, '')]
          + ([] if 'sceneCues(captions, timeline' in root else ['Root.tsx does not take its cues from sceneCues']))

    node = shutil.which('node')
    kit = KIT.read_text(encoding='utf-8')
    if not node:
        check('node is on PATH', ['node is not on PATH'])
    else:
        timeline = json.loads(TIMELINE.read_text(encoding='utf-8'))
        fix = next(s for s in timeline['scenes'] if s['id'] == 'fix')['dataRefs']['risks']
        r = subprocess.run([node, '--input-type=module', '-e', PROGRAM % {
            'moments': json.dumps(MOMENTS.as_uri()), 'timing': json.dumps(TIMING.as_uri()),
            'timeline': json.dumps(str(TIMELINE)), 'captions': json.dumps(str(CAPTIONS)),
            'spoken': json.dumps(SPOKEN), 'cramped': CRAMPED}], capture_output=True, text=True, encoding='utf-8', timeout=60)
        try:
            got = json.loads(r.stdout)
        except ValueError:
            got = None
            check('moments.mjs runs', [r.stderr[-400:]])
        if got:
            if isinstance(got.get('fix'), dict) and 'error' not in got['fix']:
                got['fix']['savedAt'] = [fix['shown'].index(x) for x in fix['saved']]
            check('each beat lands its figures, footage, cards and ticks on the words that call for them', beat_problems(got))
            clips = json.loads(FOOTAGE.read_text(encoding='utf-8'))['clips']
            ui = FOOTAGE_UI.read_text(encoding='utf-8')
            check('no clip runs out while it is on screen, each starting as it appears',
                  shot_problems(got.get('shots', {}), timeline, clips)
                  + [f'Footage.tsx does not use {x}' for x in STARTS_ON_ENTRY if x not in ui])
            c = got['consts']
            check('a button presses to 0.96 and back within 120 ms, from the one definition in moments.mjs',
                  ([] if c.get('PRESS') == PRESS and c.get('PRESS_SCALE') == PRESS_SCALE else [c])
                  + [f'kit.tsx does not use {x}' for x in ('(1 - PRESS_SCALE) * pressed',) if x not in kit])

    theme = THEME.read_text(encoding='utf-8')
    others = [p for ext in ('*.ts', '*.tsx', '*.mjs') for p in SRC.rglob(ext) if p != THEME]
    check('secondary text is the brighter ink',
          sorted(f'{p.relative_to(ROOT).as_posix()} uses color.inkMuted' for p in others
                 if 'color.inkMuted' in p.read_text(encoding='utf-8'))
          + ([] if re.search(r'export const STAGE = \{[^}]*risks:[^}]*mitigations:', theme) else ['theme.ts lacks STAGE accents']))

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
