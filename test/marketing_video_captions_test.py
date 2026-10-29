"""Test for the marketing video's caption cues: video/src/captions.json, built by video/scripts/cues.mjs.

Usage:  python test/marketing_video_captions_test.py

The captions are burned into each fragment and become the .srt, so they must say exactly what the voice says, fit
on screen, be readable, and follow the clip they caption. Scene lengths come from video/src/timing.mjs through
video/scripts/scene-seconds.mjs, the same rule the compositions use. Checks:
  - captions.json is what cues.mjs builds from the current timeline, so new audio cannot ship with old cues
  - the cues of each scene repeat its narration word for word, in order
  - each cue has 1 or 2 lines of at most 42 characters, lasts at least 0.83 s and reads at 17 characters a second
    or less
  - each cue names its fragment and scene; a scene's cues start with its clip, follow each other without gap or
    overlap, end with its clip, and each lasts its share of the clip by characters (times are seconds from the
    fragment's start, each scene starting where the one before it ends)
  The video's total length is pinned once, in test/marketing_video_audio_test.py.
  - each built scene has the cues it times its beats from
  - the guard: one broken copy per rule is rejected
Prints a JSON report; exit code 1 on any failure.
"""
import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIDEO = ROOT / 'video'
CAPTIONS = VIDEO / 'src' / 'captions.json'
CUES = VIDEO / 'scripts' / 'cues.mjs'
SCENE_SECONDS = VIDEO / 'scripts' / 'scene-seconds.mjs'
LINE, LINES, MIN_CUE, MAX_CPS, EPS = 42, 2, 0.83, 17.0, 0.002
# The scenes time their beats from these cues by index, so each needs at least this many.
MIN_CUES = {'canvas': 3, 'risks': 4, 'mitigations': 4, 'enhancements': 3}


def windows(timeline, seconds):
    """{scene id: (fragment id, scene start, clip end)} in seconds from the fragment's start."""
    scenes, out = {s['id']: s for s in timeline['scenes']}, {}
    for f in timeline['fragments']:
        at = 0.0
        for sid in f['scenes']:
            out[sid] = (f['id'], at, at + scenes[sid].get('audioSeconds', 0))
            at += seconds[sid]
    return out


def problems(captions, timeline, seconds):
    """Every rule the cues break, as readable strings; empty when they are sound."""
    if not isinstance(captions, dict) or set(captions) != {'cues'} or not isinstance(captions['cues'], list):
        return ['top level must be exactly {cues: [...]}']
    cues, win, bad = captions['cues'], windows(timeline, seconds), []
    for i, c in enumerate(cues):
        if not (isinstance(c, dict) and set(c) == {'fragment', 'scene', 'start', 'end', 'lines'}
                and c['scene'] in win and win[c['scene']][0] == c['fragment']
                and isinstance(c['lines'], list) and all(isinstance(x, str) for x in c['lines'])
                and all(isinstance(c[k], (int, float)) for k in ('start', 'end'))):
            return [f'cue {i} must be {{fragment, scene, start, end, lines}} with a scene of that fragment']
        text, length = ' '.join(c['lines']), c['end'] - c['start']
        if not 1 <= len(c['lines']) <= LINES or any(not 0 < len(x) <= LINE for x in c['lines']):
            bad.append(f'cue {i}: {len(c["lines"])} lines, longest {max(map(len, c["lines"]), default=0)} characters')
        if length < MIN_CUE - EPS or len(text) > MAX_CPS * length + EPS:
            bad.append(f'cue {i}: {len(text)} characters in {length:.3f} s is too short or too fast to read')
    bad += [f'{sid}: {n} cues at least, its scene times its beats from them' for sid, n in MIN_CUES.items()
            if sum(c['scene'] == sid for c in cues) < n]
    for s in timeline['scenes']:
        own = [c for c in cues if c['scene'] == s['id']]
        if ' '.join(x for c in own for x in c['lines']).split() != s['narration'].split():
            bad.append(f'{s["id"]}: the cues do not repeat the narration word for word')
        if not own:
            continue
        _, lo, hi = win[s['id']]
        ordered = sorted(own, key=lambda c: c['start'])
        chars = sum(len(' '.join(c['lines'])) for c in own)
        if abs(ordered[0]['start'] - lo) > EPS or abs(ordered[-1]['end'] - hi) > EPS or any(
                abs(a['end'] - b['start']) > EPS for a, b in zip(ordered, ordered[1:])):
            bad.append(f'{s["id"]}: the cues must run from {lo:.3f} to {hi:.3f} s, each meeting the next')
        if any(abs((c['end'] - c['start']) - (hi - lo) * len(' '.join(c['lines'])) / chars) > EPS for c in own):
            bad.append(f'{s["id"]}: a cue does not last its share of the clip by characters')
    by_fragment = {}
    for c in cues:
        by_fragment.setdefault(c['fragment'], []).append(c)
    for fid, own in by_fragment.items():
        ordered = sorted(own, key=lambda c: c['start'])
        if any(b['start'] < a['end'] - EPS for a, b in zip(ordered, ordered[1:])):
            bad.append(f'cues overlap in {fid}')
    return bad


def broken_copies(captions, timeline):
    """{rule: (a copy of the captions breaking that rule, a fragment its rejection must contain)}."""
    def edit(fn):
        c = copy.deepcopy(captions)
        fn(c['cues'])
        return c

    return {
        'a line over 42 characters': (edit(lambda cs: cs[0]['lines'].__setitem__(0, 'x' * 43)), 'characters'),
        'three lines': (edit(lambda cs: cs[0]['lines'].append('more')), 'lines'),
        'a dropped word': (edit(lambda cs: cs[0]['lines'].__setitem__(-1, cs[0]['lines'][-1].rsplit(' ', 1)[0])),
                           'word for word'),
        'a cue past its clip': (edit(lambda cs: cs[0].update(end=cs[0]['end'] + 1)), 'must run from'),
        'a cue of another fragment': (edit(lambda cs: cs[0].update(fragment='f2')), 'must be'),
        'a cue too short to read': (edit(lambda cs: cs[0].update(end=cs[0]['start'] + 0.5)), 'too short'),
    }


def main():
    checks = {}

    def check(name, found):
        checks[name] = {'ok': not found, 'detail': json.dumps(found)[:1500] if found else 'sound'}

    timeline = json.loads((VIDEO / 'src' / 'timeline.json').read_text(encoding='utf-8'))
    node = shutil.which('node')
    try:
        captions = json.loads(CAPTIONS.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        captions = None
        check('video/src/captions.json exists and parses', [repr(e)])
    if captions is not None and not node:
        check('node is on PATH', ['node is not on PATH'])
    elif captions is not None:
        built = subprocess.run([node, str(CUES), '--stdout'], capture_output=True, text=True, timeout=60, cwd=ROOT)
        lengths = subprocess.run([node, str(SCENE_SECONDS)], capture_output=True, text=True, timeout=60, cwd=ROOT)
        try:
            fresh, seconds = json.loads(built.stdout) == captions, json.loads(lengths.stdout)
        except ValueError:
            fresh, seconds = False, None
        check('captions.json is what cues.mjs builds from the current timeline',
              [] if fresh else [f'run npm run video:cues and commit video/src/captions.json {built.stderr[-200:]}'])
        if seconds is None:
            check('scene-seconds.mjs reports each scene', [lengths.stderr[-300:]])
        else:
            try:
                found = problems(captions, timeline, seconds)
            except Exception as e:  # noqa: BLE001 - a malformed shape is reported as a failure, never a crash
                found = [f'validator crashed: {e!r}']
            check('the cues repeat the narration, fit on screen, read well and follow their clips', found)
            if not found:
                missed = [rule for rule, (c, why) in broken_copies(captions, timeline).items()
                          if not any(why in x for x in problems(c, timeline, seconds))]
                check('each rule rejects a broken copy', missed)

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
