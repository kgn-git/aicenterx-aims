"""Test for how the marketing video's scenes follow the narration: video/src/scenes/*.tsx against
video/src/captions.json.

Usage:  python test/marketing_video_scenes_test.py

A scene times its zoom, ticks and next button to the narration. Indexing the caption cues by number ties those
moments to how the captions happen to be split, so a reworded line silently moves them or crashes the render;
a scene names the words it waits for instead. Checks:
  - no scene indexes its cues by number (cues[2]); the first and last cue may still be reached by length
  - every phrase a scene waits for, cueWith(cues, "..."), lies inside one caption cue of that scene, so the scene
    finds it, and the check sees at least one such phrase so it cannot pass on an empty list
  - only the risks scene shows the agent's full working checklist (AgentRun); mitigations and enhancements show the
    status line (AgentStatus) alone, so the video shows the agent at work once and then cuts to results
Prints a JSON report; exit code 1 on any failure.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCENES = ROOT / 'video' / 'src' / 'scenes'
CAPTIONS = ROOT / 'video' / 'src' / 'captions.json'
NUMBERED = re.compile(r'\bcues\[\d+\]')
WAITS = re.compile(r'cueWith\(cues,\s*"([^"]+)"\)')
RUN_ONLY_IN = {'Risks.tsx'}
STATUS_IN = {'Risks.tsx', 'Mitigations.tsx', 'Enhancements.tsx'}


def cue_texts(captions):
    """{scene id: [the text of each of its cues]}."""
    out = {}
    for c in captions['cues']:
        out.setdefault(c['scene'], []).append(' '.join(c['lines']))
    return out


def main():
    checks = {}

    def check(name, problems):
        checks[name] = {'ok': not problems, 'detail': json.dumps(problems)[:1500] if problems else 'sound'}

    sources = {p.name: p.read_text(encoding='utf-8') for p in sorted(SCENES.glob('*.tsx'))}
    texts = cue_texts(json.loads(CAPTIONS.read_text(encoding='utf-8')))

    check('no scene indexes its cues by number',
          [f'{name}: {m}' for name, src in sources.items() for m in NUMBERED.findall(src)])
    waits = [(name, phrase) for name, src in sources.items() for phrase in WAITS.findall(src)]
    check('every phrase a scene waits for lies inside one of its caption cues',
          (['no scene waits for a phrase'] if not waits else [])
          + [f'{name}: "{phrase}" is in no {Path(name).stem.lower()} cue' for name, phrase in waits
             if not any(phrase in t for t in texts.get(Path(name).stem.lower(), []))])
    check('only the risks scene shows the full agent run; the others show its status line',
          [f'{name} renders AgentRun' for name, src in sources.items() if '<AgentRun' in src and name not in RUN_ONLY_IN]
          + [f'{name} does not render AgentRun' for name in RUN_ONLY_IN if '<AgentRun' not in sources.get(name, '')]
          + [f'{name} does not render AgentStatus' for name in STATUS_IN if '<AgentStatus' not in sources.get(name, '')])

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
