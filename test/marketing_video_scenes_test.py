"""Test for how the marketing video's scenes follow the narration: video/src/scenes/*.tsx and the timings they take
from video/src/moments.mjs, against video/src/captions.json.

Usage:  python test/marketing_video_scenes_test.py

A scene times its cards, ticks and buttons to the narration. Indexing the caption cues by number ties those moments
to how the captions happen to be split, so a reworded line silently moves them or crashes the render; moments.mjs
names the words it waits for instead, and stops with an error when a phrase is no longer said, so running it on the
real captions proves every phrase is there. Checks:
  - no scene and not moments.mjs indexes its cues by number (cues[2], cues.at(2)); the first and last cue may still
    be reached by length
  - the dotted background stays off in the hook and starts in the problem scene on "The challenge", as the user asked
  - the moments of each scene, computed by moments.mjs through node from the real timeline and captions, measured to
    the start of the 0.3 s crossfade out of the scene:
      - no zoom anywhere, so the cursor stays in view
      - the canvas shows "Simulate risks" for at least 1.2 s, and the cursor reaches it on the way
      - the hand-off button after the canvas, risks and mitigations glows for at least 0.8 s
      - every tick lands after its card and before the save
      - the first mitigation and enhancement card lands within 0.25 s of the click
      - the enhancements toast is fully shown for at least 1.5 s, also in a scene cut to 5.1 s, where the ticks must
        start earlier to keep it
      - a scene too short for its ticks, save and hand-off stops with an error naming it, rather than ticking cards
        that have not landed
      - the risks and mitigations scenes light their chips as each of their two spoken sources is named, in order,
        once every card is on screen
      - the problem scene opens on the empty rings of its three costs, so the frame is never blank; the cost icons
        land in order as the voice says "time", "effort" and "harm" and are all shown, red, for at least 0.9 s;
        only then does the Venn diagram arrive and meet, and its bright target is lit for at least 1.2 s; the dots
        arrive by then
      - a reworded problem line or a reordered close stops with an error that names the missing or misplaced words
      - the close opens on the initiative's outcome card, whose risks, mitigations and enhancements rows count up
        one after another and can be read, filled, for at least 1.5 s; the card then folds into its own place in
        the portfolio before the portfolio arrives, ahead of "models"; the footer can be read for at least 2 s
  - each scene uses what moments.mjs gives it: the named times for the chips, the cost icons and the circles, the
    footer and the canvas glow, and the outcome card's rows and their count
  - the user's motion choices: the cursor eases with cubic-bezier(0.22, 1, 0.36, 1) and a button presses to 0.96 and
    back within 120 ms, from the one definition in moments.mjs that kit.tsx and every scene use
  - only the risks scene shows the agent's full working checklist (AgentRun); mitigations and enhancements show the
    status line (AgentStatus) alone, so the video shows the agent at work once and then cuts to results
  - the user's visual choices for a scannable cut: the risk, mitigation and enhancement cards land as whole blocks
    (no letter-by-letter Stream), each stage marks its cards with its own accent (accent={STAGE.risks} and so on,
    three different colours in theme.ts), and secondary text uses the brighter mutedInk rather than the prototype's
    inkMuted anywhere in video/src outside theme.ts
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
TIMING = SRC / 'timing.mjs'
GLOW, CARD_DELAY, TOAST, READ, HANDOFF_SHOWN, COSTS_SHOWN, TARGET_SHOWN = 0.8, 0.25, 1.5, 2.0, 1.2, 0.9, 1.2
OUTCOME_SHOWN = 1.5
# TAIL in video/src/timing.mjs: the crossfade that starts this long before a scene's cut.
CROSSFADE = 0.3
# A shorter enhancements scene than the real one, where the toast's time would be lost without its floor; and a
# mitigations scene too short for its ticks, save and hand-off at all.
TIGHT, CRAMPED = 5.1, 3.0
PRESS, PRESS_SCALE, CURSOR_EASE = 0.12, 0.96, [0.22, 1, 0.36, 1]
# {scene file: what it must call and use from moments.mjs}.
USERS = {'Risks.tsx': ('stageMoments(', 'bump(t, mitNamed', 'bump(t, aiidNamed', 'contextAt'),
         'Mitigations.tsx': ('stageMoments(', '[mitNamed, lawNamed][n]'),
         'Enhancements.tsx': ('stageMoments(',),
         'Canvas.tsx': ('canvasMoments(', 'ramp(t, glow'),
         'Problem.tsx': ('problemMoments(', 'm.marks', 'ramp(t, m.circles', 'ramp(t, m.costsOut', 'ramp(t, m.rings'),
         'End.tsx': ('closeMoments(', 'ramp(t, footer', 'from={portfolioIn}', '<Outcome'),
         'Acceleration.tsx': ('ramp(t, at.rows[i], TALLY_COUNT)', 'ramp(t, at.fold'),}
# Each module is imported as a namespace, so a missing export fails its own check instead of the whole run.
PROGRAM = """
import {readFileSync} from "node:fs";
import * as m from %(moments)s;
import {sceneSeconds} from %(timing)s;
const timeline = JSON.parse(readFileSync(%(timeline)s, "utf8"));
const captions = JSON.parse(readFileSync(%(captions)s, "utf8"));
const scenes = Object.fromEntries(timeline.scenes.map((s) => [s.id, s]));
const attempt = (f) => { try { return f(); } catch (e) { return {error: String(e.message)}; } };
const at = (id, f) => attempt(() => {
  const seconds = sceneSeconds(scenes[id]);
  return {seconds, ...f(scenes[id], m.sceneCues(captions, timeline, id), seconds)};
});
const stage = (id, seconds) => at(id, (scene, cues, real) => {
  const {shown, saved} = scene.dataRefs[id];
  return {...m.stageMoments(scene, cues, seconds ?? real), seconds: seconds ?? real,
    savedAt: saved.map((x) => shown.indexOf(x))};
});
const out = {consts: {PRESS: m.PRESS, PRESS_SCALE: m.PRESS_SCALE, CURSOR_EASE: m.CURSOR_EASE,
  TALLY_COUNT: m.TALLY_COUNT, pressed: attempt(() => [m.pressed(1, [1]), m.pressed(1.061, [1]), m.pressed(0.939, [1])])}};
for (const id of ["risks", "mitigations", "enhancements"]) out[id] = stage(id);
out.tight = stage("enhancements", %(tight)s);
out.cramped = stage("mitigations", %(cramped)s);
out.canvas = at("canvas", (scene, cues, seconds) => m.canvasMoments(cues, seconds));
out.problem = at("problem", (scene, cues) => m.problemMoments(scene, cues));
out.end = at("end", (scene, cues) => m.closeMoments(scene, cues));
// The same scenes with their words changed: a cost the problem line no longer says, and a close that names the
// capabilities before it scales up.
out.reworded = at("problem", (scene, cues) => m.problemMoments({...scene, narration: scene.narration.replace("effort", "work")}, cues));
out.reordered = at("end", (scene, cues) => m.closeMoments({...scene, narration: scene.narration.replace("Then scale up: ", "") + " Then scale up."}, cues));
console.log(JSON.stringify(out));
"""
NUMBERED = re.compile(r'\bcues(\[\d+\]|\.at\()')
RUN_ONLY_IN = {'Risks.tsx'}
STATUS_IN = {'Risks.tsx', 'Mitigations.tsx', 'Enhancements.tsx'}
STAGES = {'Risks.tsx': 'risks', 'Mitigations.tsx': 'mitigations', 'Enhancements.tsx': 'enhancements'}


def theme_colours(theme):
    """{STAGE key: hex}, resolving color.* through the color object."""
    palette = dict(re.findall(r'(\w+): "(#[0-9a-f]{6})"', re.search(r'export const color = \{(.*?)\};', theme, re.S).group(1)))
    accents = re.search(r'export const STAGE = \{(.*?)\};', theme, re.S)
    pairs = re.findall(r'(\w+): (?:color\.(\w+)|"(#[0-9a-f]{6})")', accents.group(1)) if accents else []
    return {k: palette.get(ref) if ref else hexa for k, ref, hexa in pairs}


def stage_problems(sid, g):
    """Each AC limit a risks, mitigations or enhancements scene's moments break."""
    if 'error' in g or 'ticks' not in g:
        return [f'{sid}: {g.get("error", "no moments")}']
    bad = []
    ticks, cards, secs = g['ticks'], g['cards'], g['seconds'] - CROSSFADE
    bad += [f'{sid}: tick {k} at {t:.2f} s comes before its card lands at {cards[i]:.2f} s'
            for k, (t, i) in enumerate(zip(ticks, g['savedAt'])) if t < cards[i] + 0.2]
    if ticks != sorted(ticks) or not ticks or g['saveAt'] < ticks[-1] + 0.3:
        bad.append(f'{sid}: the ticks must rise and the save follow them, got {ticks} then {g["saveAt"]}')
    if sid in ('enhancements', 'tight'):
        if g.get('nextAt') is not None or secs - (g['saveAt'] + 0.5) < TOAST:
            bad.append(f'{sid}: the toast shows {secs - g["saveAt"] - 0.5:.2f} s, want {TOAST} s and no next button')
    elif g.get('nextAt') is None or g['nextAt'] < g['saveAt'] or secs - g['nextAt'] < GLOW:
        bad.append(f'{sid}: the next button glows {secs - (g.get("nextAt") or secs):.2f} s, want {GLOW} s')
    if sid != 'risks' and cards[0] - g['click'] > CARD_DELAY + 1e-9:
        bad.append(f'{sid}: the first card lands {cards[0] - g["click"]:.2f} s after the click, want {CARD_DELAY} s')
    named = g.get('named', [])
    if sid in ('risks', 'mitigations') and not (len(named) == 2 and named == sorted(named)
                                                 and named[0] >= cards[-1] + 0.3 and named[1] < secs):
        bad.append(f'{sid}: want a chip lit as each of its two sources is named once the cards are up, got {named}')
    return bad


def moment_problems(got):
    """Each AC limit the computed moments break, per scene."""
    bad = [p for sid in ('risks', 'mitigations', 'enhancements', 'tight') for p in stage_problems(sid, got.get(sid, {}))]
    if 'mitigations' not in got.get('cramped', {}).get('error', ''):
        bad.append(f'a {CRAMPED} s mitigations scene must stop with an error naming it, got {got.get("cramped")}')
    cv = got.get('canvas', {})
    if 'error' in cv or 'appear' not in cv:
        bad.append(f'canvas: {cv.get("error", "no moments")}')
    else:
        secs = cv['seconds'] - CROSSFADE
        if not (cv['appear'] < cv['arrive'] <= secs and secs - cv['appear'] >= HANDOFF_SHOWN and secs - cv['glow'] >= GLOW):
            bad.append(f'canvas: "Simulate risks" must show {HANDOFF_SHOWN} s, glow {GLOW} s and meet the cursor, got {cv}')
    pr = got.get('problem', {})
    marks = pr.get('marks') if isinstance(pr.get('marks'), list) else []
    if 'error' in pr or len(marks) != 3 or 'costsOut' not in pr:
        bad.append(f'problem: want three cost times and when they leave, got {pr}')
    else:
        if not (pr['rings'] <= 0.3 and marks == sorted(marks) and marks[0] > pr['rings']):
            bad.append(f'problem: the rings must open the scene and the costs land in order, got {pr}')
        if pr['costsOut'] - (marks[-1] + 0.35) < COSTS_SHOWN:
            bad.append(f'problem: the three costs show together for {pr["costsOut"] - marks[-1] - 0.35:.2f} s, want {COSTS_SHOWN} s')
        if not (pr['costsOut'] <= pr['circles'] <= pr['meet'] and pr['dots'] <= pr['circles']):
            bad.append(f'problem: the Venn diagram must follow the costs, after the dots, got {pr}')
        if pr['seconds'] - CROSSFADE - (pr['target'] + 0.5) < TARGET_SHOWN:
            bad.append(f'problem: the target is lit {pr["seconds"] - CROSSFADE - pr["target"] - 0.5:.2f} s, want {TARGET_SHOWN} s')
    if 'no longer says "effort"' not in got.get('reworded', {}).get('error', ''):
        bad.append(f'a problem line without "effort" must stop with an error naming it, got {got.get("reworded")}')
    if 'in that order' not in got.get('reordered', {}).get('error', ''):
        bad.append(f'a close that says its words out of order must stop with an error, got {got.get("reordered")}')
    end = got.get('end', {})
    count = got['consts'].get('TALLY_COUNT') or 0
    if 'error' in end or not isinstance(end.get('rows'), list) or len(end['rows']) != 3:
        bad.append(f'end: want the outcome card and one time per row, got {end}')
    else:
        filled = max(end['rows']) + count
        if count < 0.5 or end['card'] > 0.3 or end['scaleAt'] - filled < OUTCOME_SHOWN:
            bad.append(f'end: the outcome card reads {end["scaleAt"] - filled:.2f} s once filled, want {OUTCOME_SHOWN} s')
        if end['portfolioIn'] - end['scaleAt'] < 0.4 or end['portfolioIn'] >= end['keywords'][0]:
            bad.append(f'end: the card must fold into the portfolio before it arrives, ahead of "models", got {end}')
        # The close is the last scene, so nothing fades in over its footer.
        if end['seconds'] - end['footer'] < READ:
            bad.append(f'end: the footer reads {end["seconds"] - end["footer"]:.2f} s, want {READ} s')
        if not end['card'] < min(end['rows']) and end['rows'] == sorted(end['rows']) and end['scaleAt'] < end['brandAt']:
            bad.append(f'end: the beats are out of order: {end}')
    return bad


def main():
    checks = {}

    def check(name, problems):
        checks[name] = {'ok': not problems, 'detail': json.dumps(problems)[:1500] if problems else 'sound'}

    sources = {p.name: p.read_text(encoding='utf-8') for p in sorted(SCENES.glob('*.tsx'))}
    moments = MOMENTS.read_text(encoding='utf-8') if MOMENTS.is_file() else ''
    check('no scene and not moments.mjs indexes its cues by number',
          [f'{name}: cues{m}' for name, src in {**sources, 'moments.mjs': moments}.items()
           for m in NUMBERED.findall(src)])
    check('the dotted background is off in the hook and starts on "The challenge" in the problem scene',
          ([] if '<Background dots={0}>' in sources['Hook.tsx'] else ['Hook.tsx does not render <Background dots={0}>'])
          + ([] if 'dots: at("The challenge")' in moments and 'ramp(t, m.dots' in sources['Problem.tsx']
             else ['Problem.tsx does not start its dots on "The challenge"']))

    node = shutil.which('node')
    kit = KIT.read_text(encoding='utf-8')
    root = (SRC / 'Root.tsx').read_text(encoding='utf-8')
    check('every scene uses its moments from moments.mjs, and nothing zooms',
          [f'{name} does not use {token}' for name, tokens in USERS.items() for token in tokens
           if token not in sources[name]]
          + [f'{name} still zooms' for name, src in sources.items() if '<Zoom' in src or 'zoomLevel' in src]
          + (['kit.tsx still exports Zoom'] if 'export const Zoom' in kit else [])
          + ([] if 'sceneCues(captions, timeline' in root else ['Root.tsx does not take its cues from sceneCues']))
    if not node:
        check('node is on PATH', ['node is not on PATH'])
    elif not MOMENTS.is_file():
        check('video/src/moments.mjs exists', ['missing'])
    else:
        r = subprocess.run([node, '--input-type=module', '-e', PROGRAM % {
            'moments': json.dumps(MOMENTS.as_uri()), 'timing': json.dumps(TIMING.as_uri()),
            'timeline': json.dumps(str(TIMELINE)), 'captions': json.dumps(str(CAPTIONS)), 'tight': TIGHT,
            'cramped': CRAMPED}], capture_output=True, text=True, encoding='utf-8', timeout=60)
        try:
            got = json.loads(r.stdout)
        except ValueError:
            got = None
            check('moments.mjs runs', [r.stderr[-400:]])
        if got:
            check('each scene leaves time to see its cards, ticks, save, hand-off and close', moment_problems(got))
            c = got['consts']
            check('the cursor eases with cubic-bezier(0.22, 1, 0.36, 1) and a button presses to 0.96 within 120 ms',
                  ([] if c.get('PRESS') == PRESS and c.get('PRESS_SCALE') == PRESS_SCALE
                   and c.get('CURSOR_EASE') == CURSOR_EASE and c.get('pressed') == [1, 0, 0] else [c])
                  + [f'kit.tsx does not use {x}' for x in ('Easing.bezier(...CURSOR_EASE)', '(1 - PRESS_SCALE) * pressed',
                                                            'pressed(t, clicks)') if x not in kit]
                  + [f'{name} times a press of its own' for name, src in {**sources, 'kit.tsx': kit}.items()
                     if '/ 0.15' in src])
    check('only the risks scene shows the full agent run; the others show its status line',
          [f'{name} renders AgentRun' for name, src in sources.items() if '<AgentRun' in src and name not in RUN_ONLY_IN]
          + [f'{name} does not render AgentRun' for name in RUN_ONLY_IN if '<AgentRun' not in sources.get(name, '')]
          + [f'{name} does not render AgentStatus' for name in STATUS_IN if '<AgentStatus' not in sources.get(name, '')])

    theme = THEME.read_text(encoding='utf-8')
    tones = theme_colours(theme)
    others = [p for ext in ('*.ts', '*.tsx', '*.mjs') for p in SRC.rglob(ext) if p != THEME]
    check('cards land as blocks, each stage has its own accent, and secondary text is the brighter ink',
          [f'{name} writes its cards letter by letter' for name in STAGES if '<Stream' in sources[name]]
          + [f'{name} does not give its cards accent={{STAGE.{s}}}' for name, s in STAGES.items()
             if f'accent={{STAGE.{s}}}' not in sources[name]]
          + ([] if set(tones) == set(STAGES.values()) and None not in tones.values() and len(set(tones.values())) == 3
             else [f'theme.ts STAGE must give risks, mitigations and enhancements three colours, got {tones}'])
          + sorted(f'{p.relative_to(ROOT).as_posix()} uses color.inkMuted' for p in others
                   if 'color.inkMuted' in p.read_text(encoding='utf-8')))

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
