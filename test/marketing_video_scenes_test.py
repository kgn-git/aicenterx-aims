"""Test for how the marketing video's scenes follow the narration: video/src/scenes/*.tsx against
video/src/captions.json.

Usage:  python test/marketing_video_scenes_test.py

A scene times its zoom, ticks and next button to the narration. Indexing the caption cues by number ties those
moments to how the captions happen to be split, so a reworded line silently moves them or crashes the render;
a scene names the words it waits for instead. Checks:
  - no scene indexes its cues by number (cues[2], cues.at(2)); the first and last cue may still be reached by length
  - every phrase a scene waits for, cueWith(cues, "...") or saidAt(cues, "..."), lies inside one caption cue of that
    scene, exactly as the code searches, so the scene finds it
  - every phrase a scene times from its narration, spokenAt(scene.narration, "...") or End.tsx's at("..."), is in
    that scene's narration with the same case, as spokenAt searches; the problem scene's marks (onScreen[3:6]) are
    each spoken in its statement, which marks them as they are said
  - each scene that imports cueWith, saidAt or spokenAt yields at least one phrase, so no check passes on nothing
  - the dotted background stays off in the hook and starts in the problem scene on "The challenge", as the user asked
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
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'video' / 'src'
SCENES = SRC / 'scenes'
CAPTIONS = SRC / 'captions.json'
TIMELINE = SRC / 'timeline.json'
THEME = SRC / 'theme.ts'
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
    problem = scenes['problem']['onScreen']
    check('every phrase a scene times from its narration is spoken, and so is each problem mark',
          [f'{name}: "{phrase}" is not in the {scene_of(name)} narration' for name, phrases in spoken.items()
           for phrase in phrases if phrase not in scenes.get(scene_of(name), {}).get('narration', '')]
          + [f'problem: the mark "{m}" is not spoken in "{problem[0]}"' for m in problem[3:6]
             if m.lower() not in problem[0]])
    check('the dotted background is off in the hook and starts on "The challenge" in the problem scene',
          ([] if '<Background dots={0}>' in sources['Hook.tsx'] else ['Hook.tsx does not render <Background dots={0}>'])
          + ([] if 'spokenAt(scene.narration, "The challenge"' in sources['Problem.tsx']
                   and 'dots={' in sources['Problem.tsx']
             else ['Problem.tsx does not start its dots on "The challenge"']))
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
