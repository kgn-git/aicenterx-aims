"""Test for the marketing video's caption cues: video/src/captions.json, built by video/scripts/cues.mjs.

Usage:  python test/marketing_video_captions_test.py

The captions are burned into each fragment and become the .srt, so they must say exactly what the voice says, fit
on screen and stay inside their own fragment and clip. Checks:
  - captions.json is what cues.mjs builds from the current timeline, so new audio cannot ship with old cues
  - the cues of each scene repeat its narration word for word, in order
  - each cue has 1 or 2 lines of at most 42 characters
  - each cue names its fragment and scene, lies inside that scene's clip (times are seconds from the fragment's
    start, each scene starting where the one before it ends), and overlaps no other cue
  - the last cue ends within 66 s of the video's start (the user's tolerance until the combined review)
Prints a JSON report; exit code 1 on any failure.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIDEO = ROOT / 'video'
CAPTIONS = VIDEO / 'src' / 'captions.json'
CUES = VIDEO / 'scripts' / 'cues.mjs'
TAIL, MAX_TOTAL, LINE, LINES, EPS = 0.3, 66.0, 42, 2, 0.0005


def scene_windows(timeline):
    """{scene id: (fragment id, scene start, clip end)} in seconds from the fragment's start."""
    scenes, windows = {s['id']: s for s in timeline['scenes']}, {}
    for f in timeline['fragments']:
        at = 0.0
        for sid in f['scenes']:
            s = scenes[sid]
            windows[sid] = (f['id'], at, at + s.get('audioSeconds', 0))
            at += max(s['seconds'], s.get('audioSeconds', 0) + TAIL)
    return windows


def fragment_starts(timeline):
    """{fragment id: its start in seconds from the video's start}."""
    scenes, starts, at = {s['id']: s for s in timeline['scenes']}, {}, 0.0
    for f in timeline['fragments']:
        starts[f['id']] = at
        at += sum(max(scenes[s]['seconds'], scenes[s].get('audioSeconds', 0) + TAIL) for s in f['scenes'])
    return starts


def problems(captions, timeline):
    """Every rule the cues break, as readable strings; empty when they are sound."""
    if not isinstance(captions, dict) or set(captions) != {'cues'} or not isinstance(captions['cues'], list):
        return ['top level must be exactly {cues: [...]}']
    cues, windows, bad = captions['cues'], scene_windows(timeline), []
    for i, c in enumerate(cues):
        if not (isinstance(c, dict) and set(c) == {'fragment', 'scene', 'start', 'end', 'lines'}
                and c['scene'] in windows and windows[c['scene']][0] == c['fragment']
                and isinstance(c['lines'], list) and all(isinstance(x, str) for x in c['lines'])
                and all(isinstance(c[k], (int, float)) for k in ('start', 'end'))):
            return [f'cue {i} must be {{fragment, scene, start, end, lines}} with a scene of that fragment']
        fid, lo, hi = windows[c['scene']]
        if not 1 <= len(c['lines']) <= LINES or any(not 0 < len(x) <= LINE for x in c['lines']):
            bad.append(f'cue {i}: {len(c["lines"])} lines, longest {max(map(len, c["lines"]), default=0)} characters')
        if not lo - EPS <= c['start'] < c['end'] <= hi + EPS:
            bad.append(f'cue {i}: {c["start"]}-{c["end"]} s is outside {c["scene"]}\'s clip, {lo:.3f}-{hi:.3f} s')
    for a, b in zip(cues, cues[1:]):
        if a['fragment'] == b['fragment'] and b['start'] < a['end'] - EPS:
            bad.append(f'cues at {a["start"]} and {b["start"]} s overlap in {a["fragment"]}')
    for s in timeline['scenes']:
        said = ' '.join(x for c in cues if c['scene'] == s['id'] for x in c['lines']).split()
        if said != s['narration'].split():
            bad.append(f'{s["id"]}: the cues do not repeat the narration word for word')
    starts = fragment_starts(timeline)
    last = max((starts[c['fragment']] + c['end'] for c in cues), default=0)
    if last > MAX_TOTAL:
        bad.append(f'the last cue ends at {last:.2f} s, after {MAX_TOTAL:g} s')
    return bad


def main():
    checks = {}

    def check(name, found):
        checks[name] = {'ok': not found, 'detail': json.dumps(found)[:1500] if found else 'sound'}

    timeline = json.loads((VIDEO / 'src' / 'timeline.json').read_text(encoding='utf-8'))
    try:
        captions = json.loads(CAPTIONS.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        captions = None
        check('video/src/captions.json exists and parses', [repr(e)])
    if captions is not None:
        node = shutil.which('node')
        built = subprocess.run([node, str(CUES), '--stdout'], capture_output=True, text=True, timeout=60,
                               cwd=ROOT) if node else None
        fresh = built is not None and built.returncode == 0 and json.loads(built.stdout or 'null') == captions
        check('captions.json is what cues.mjs builds from the current timeline',
              [] if fresh else ['run npm run video:cues and commit video/src/captions.json'])
        try:
            found = problems(captions, timeline)
        except Exception as e:  # noqa: BLE001 - a malformed shape is reported as a failure, never a crash
            found = [f'validator crashed: {e!r}']
        check('the cues repeat the narration, fit on screen and stay inside their clips', found)

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
