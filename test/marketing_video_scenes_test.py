"""Test for how the marketing video's scenes follow the narration: video/src/scenes/*.tsx and the timings they take
from video/src/moments.mjs, against video/src/captions.json.

Usage:  python test/marketing_video_scenes_test.py

A scene times its zoom, ticks and next button to the narration. Indexing the caption cues by number ties those
moments to how the captions happen to be split, so a reworded line silently moves them or crashes the render;
a scene names the words it waits for instead. Checks:
  - no scene indexes its cues by number (cues[2], cues.at(2)); the first and last cue may still be reached by length
  - every phrase a scene waits for, cueWith(cues, "...") or saidAt(cues, "..."), lies inside one caption cue of that
    scene, exactly as the code searches, so the scene finds it
  - every phrase a scene times from its narration, spokenAt(scene.narration, "...") or End.tsx's at("..."), is in
    that scene's narration with the same case, as spokenAt searches
  - each scene that imports cueWith, saidAt or spokenAt yields at least one phrase, so no check passes on nothing
  - the dotted background stays off in the hook and starts in the problem scene on "The challenge", as the user asked
  - the moments of each scene, computed by moments.mjs through node from the real timeline and captions:
    no zoom anywhere, so the cursor stays in view; the hand-off button after risks and mitigations glows for at least
    0.8 s before the cut; every tick lands after its card and before the save; the first mitigation and enhancement
    card lands within 0.25 s of the click; the enhancements toast stays up for at least 1.5 s, also in a scene cut
    to 4.8 s, where the ticks must start earlier to keep it; the risks and
    mitigations scenes light a chip as each of their two spoken sources is named; the problem's Venn diagram is on
    screen from the start; the close's message and its footer can each be read for at least 2 s
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
GLOW, CARD_DELAY, TOAST, READ, VENN_FROM = 0.8, 0.25, 1.5, 2.0, 0.3
# A shorter enhancements scene than the real one, where the toast's time would be lost without its floor.
TIGHT = 4.8
PRESS, PRESS_SCALE, CURSOR_EASE = 0.12, 0.96, [0.22, 1, 0.36, 1]
USERS = {'Risks.tsx': 'stageMoments(', 'Mitigations.tsx': 'stageMoments(', 'Enhancements.tsx': 'stageMoments(',
         'Problem.tsx': 'problemMoments(', 'End.tsx': 'closeMoments('}
# Each module is imported as a namespace, so a missing export fails its own check instead of the whole run.
PROGRAM = """
import {readFileSync} from "node:fs";
import * as m from %(moments)s;
import {sceneSeconds} from %(timing)s;
const timeline = JSON.parse(readFileSync(%(timeline)s, "utf8"));
const captions = JSON.parse(readFileSync(%(captions)s, "utf8"));
const scenes = Object.fromEntries(timeline.scenes.map((s) => [s.id, s]));
const TIGHT = %(tight)s;
const attempt = (f) => { try { return f(); } catch (e) { return {error: String(e.message)}; } };
const at = (id, f) => attempt(() => {
  const seconds = sceneSeconds(scenes[id]);
  return {seconds, ...f(scenes[id], m.sceneCues(captions, timeline, id), seconds)};
});
const out = {consts: {PRESS: m.PRESS, PRESS_SCALE: m.PRESS_SCALE, CURSOR_EASE: m.CURSOR_EASE,
  pressed: attempt(() => [m.pressed(1, [1]), m.pressed(1.061, [1]), m.pressed(0.939, [1])])}};
for (const id of ["risks", "mitigations", "enhancements"]) {
  out[id] = at(id, (scene, cues, seconds) => {
    const {shown, saved} = scene.dataRefs[id];
    return {...m.stageMoments(scene, cues, seconds), savedAt: saved.map((x) => shown.indexOf(x))};
  });
}
// The enhancements again in a scene so short that the toast's floor must pull the ticks earlier.
out.tight = at("enhancements", (scene, cues) => {
  const {shown, saved} = scene.dataRefs.enhancements;
  return {...m.stageMoments(scene, cues, TIGHT), seconds: TIGHT, savedAt: saved.map((x) => shown.indexOf(x))};
});
out.problem = at("problem", (scene, cues) => m.problemMoments(scene, cues));
out.end = at("end", (scene, cues, seconds) => m.closeMoments(scene, cues, seconds));
console.log(JSON.stringify(out));
"""
SPOKEN = re.compile(r'spokenAt\(scene\.narration,\s*"([^"]+)"')
# End.tsx wraps spokenAt as at("..."), so its phrases are read through the wrapper.
AT_WRAPPER, AT = 'const at = (phrase: string) => spokenAt(scene.narration', re.compile(r'\bat\("([^"]+)"')
NUMBERED = re.compile(r'\bcues(\[\d+\]|\.at\()')
WAITS = re.compile(r'(?:cueWith|saidAt)\(cues,\s*"([^"]+)"\)')
USES = re.compile(r'\b(cueWith|saidAt|spokenAt)\b')
RUN_ONLY_IN = {'Risks.tsx'}
STATUS_IN = {'Risks.tsx', 'Mitigations.tsx', 'Enhancements.tsx'}
STAGES = {'Risks.tsx': 'risks', 'Mitigations.tsx': 'mitigations', 'Enhancements.tsx': 'enhancements'}


def cue_texts(captions):
    """{scene id: [the text of each of its cues]}."""
    out = {}
    for c in captions['cues']:
        out.setdefault(c['scene'], []).append(' '.join(c['lines']))
    return out


def scene_of(name):
    return Path(name).stem.lower()


def theme_colours(theme):
    """{STAGE key: hex}, resolving color.* through the color object."""
    palette = dict(re.findall(r'(\w+): "(#[0-9a-f]{6})"', re.search(r'export const color = \{(.*?)\};', theme, re.S).group(1)))
    accents = re.search(r'export const STAGE = \{(.*?)\};', theme, re.S)
    pairs = re.findall(r'(\w+): (?:color\.(\w+)|"(#[0-9a-f]{6})")', accents.group(1)) if accents else []
    return {k: palette.get(ref) if ref else hexa for k, ref, hexa in pairs}


def moment_problems(got):
    """Each AC limit the computed moments break, per scene."""
    bad = []
    for sid in ('risks', 'mitigations', 'enhancements', 'tight'):
        g = got.get(sid, {})
        if 'error' in g or 'ticks' not in g:
            bad.append(f'{sid}: {g.get("error", "no moments")}')
            continue
        ticks, cards, secs = g['ticks'], g['cards'], g['seconds']
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
        if sid in ('risks', 'mitigations') and (len(named) != 2 or not all(0 < x < secs for x in named)):
            bad.append(f'{sid}: want a chip lit as each of its two sources is named, got {named}')
    pr = got.get('problem', {})
    if 'error' in pr or not (pr.get('circles', 9) <= VENN_FROM < pr.get('meet', 0) and pr.get('dots', 0) > 0):
        bad.append(f'problem: the Venn diagram must be on screen from the start, got {pr}')
    end = got.get('end', {})
    if 'error' in end or 'message' not in end:
        bad.append(f'end: {end.get("error", "no moments")}')
    else:
        if end['scaleAt'] - (end['message'] + 0.6) < READ:
            bad.append(f'end: the message reads {end["scaleAt"] - end["message"] - 0.6:.2f} s, want {READ} s')
        if end['seconds'] - end['footer'] < READ:
            bad.append(f'end: the footer reads {end["seconds"] - end["footer"]:.2f} s, want {READ} s')
        if not end['collapse'] < end['tallies'] < end['scaleAt'] < end['brandAt']:
            bad.append(f'end: the beats are out of order: {end}')
    return bad


def main():
    checks = {}

    def check(name, problems):
        checks[name] = {'ok': not problems, 'detail': json.dumps(problems)[:1500] if problems else 'sound'}

    sources = {p.name: p.read_text(encoding='utf-8') for p in sorted(SCENES.glob('*.tsx'))}
    texts = cue_texts(json.loads(CAPTIONS.read_text(encoding='utf-8')))
    scenes = {s['id']: s for s in json.loads(TIMELINE.read_text(encoding='utf-8'))['scenes']}

    check('no scene indexes its cues by number',
          [f'{name}: cues{m}' for name, src in sources.items() for m in NUMBERED.findall(src)])
    waits = {name: WAITS.findall(src) for name, src in sources.items()}
    spoken = {name: SPOKEN.findall(src) + (AT.findall(src) if AT_WRAPPER in src else []) for name, src in sources.items()}
    check('each scene that times from the narration names at least one phrase',
          [f'{name} imports a timing helper but names no phrase' for name, src in sources.items()
           if USES.search(src.split('export const', 1)[-1]) and not waits[name] + spoken[name]])
    check('every phrase a scene waits for lies inside one of its caption cues',
          [f'{name}: "{phrase}" is in no {scene_of(name)} cue' for name, phrases in waits.items() for phrase in phrases
           if not any(phrase in t for t in texts.get(scene_of(name), []))])
    check('every phrase a scene times from its narration is spoken',
          [f'{name}: "{phrase}" is not in the {scene_of(name)} narration' for name, phrases in spoken.items()
           for phrase in phrases if phrase not in scenes.get(scene_of(name), {}).get('narration', '')])
    moments = MOMENTS.read_text(encoding='utf-8') if MOMENTS.is_file() else ''
    check('the dotted background is off in the hook and starts on "The challenge" in the problem scene',
          ([] if '<Background dots={0}>' in sources['Hook.tsx'] else ['Hook.tsx does not render <Background dots={0}>'])
          + ([] if '"The challenge"' in moments and 'dots={' in sources['Problem.tsx']
             else ['Problem.tsx does not start its dots on "The challenge"']))

    node = shutil.which('node')
    kit = KIT.read_text(encoding='utf-8')
    root = (SRC / 'Root.tsx').read_text(encoding='utf-8')
    check('every scene takes its moments from moments.mjs, and nothing zooms',
          [f'{name} does not call {call}' for name, call in USERS.items() if call not in sources[name]]
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
            'timeline': json.dumps(str(TIMELINE)), 'captions': json.dumps(str(CAPTIONS)), 'tight': TIGHT}],
            capture_output=True, text=True, timeout=60)
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
                  + ([] if 'Easing.bezier(...CURSOR_EASE)' in kit and 'PRESS_SCALE' in kit else
                     ['kit.tsx does not use CURSOR_EASE and PRESS_SCALE'])
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
