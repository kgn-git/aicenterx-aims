"""Test for splitting one continuous narration take into scene clips: splitTake in video/scripts/take.mjs.

Usage:  python test/marketing_video_take_test.py

The narration is voiced in one take so the voice keeps one pace and energy, then cut at the pauses between scenes.
A wrong cut would put words in the wrong scene, so the split must find the scene pauses and refuse when it cannot.
It runs on synthetic 24 kHz 16-bit PCM through node, so no voice or network is needed. Checks:
  - a take of three tones parted by two long pauses, with a shorter pause inside the first, splits at the two long
    pauses, and each clip keeps its speech without the pauses
  - a take with too few pauses is refused
  - a split whose clip lengths stray far from the scenes' word shares is refused
Prints a JSON report; exit code 1 on any failure.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAKE = (ROOT / 'video' / 'scripts' / 'take.mjs').as_uri()

# Each case builds PCM from [(seconds, loud?)] segments and calls splitTake(pcm, wordCounts).
PROGRAM = """
import {splitTake} from %s;
const RATE = 24000;
const pcm = (parts) => {
  const chunks = parts.map(([s, loud]) => {
    const b = Buffer.alloc(Math.round(s * RATE) * 2);
    if (loud) for (let i = 0; i < b.length / 2; i++) b.writeInt16LE(Math.round(8000 * Math.sin(i / 3)), i * 2);
    return b;
  });
  return Buffer.concat(chunks);
};
const run = (parts, words) => {
  try {
    return {clips: splitTake(pcm(parts), words).map((c) => Math.round((c.length / 2 / RATE) * 100) / 100)};
  } catch (e) {
    return {refused: String(e.message)};
  }
};
console.log(JSON.stringify({
  good: run([[0.2, 0], [1.0, 1], [0.35, 0], [1.0, 1], [1.2, 0], [2.0, 1], [1.1, 0], [1.0, 1], [0.2, 0]], [4, 4, 2]),
  fewPauses: run([[2.0, 1], [0.3, 0], [2.0, 1]], [2, 2, 2]),
  stray: run([[1.0, 1], [1.2, 0], [4.0, 1], [1.2, 0], [1.0, 1]], [10, 1, 10]),
}));
"""


def main():
    checks = {}

    def check(name, found):
        checks[name] = {'ok': not found, 'detail': json.dumps(found)[:1500] if found else 'sound'}

    node = shutil.which('node')
    if not node:
        check('node is on PATH', ['node is not on PATH'])
    elif not (ROOT / 'video' / 'scripts' / 'take.mjs').is_file():
        check('video/scripts/take.mjs exists', ['missing'])
    else:
        r = subprocess.run([node, '--input-type=module', '-e', PROGRAM % json.dumps(TAKE)], capture_output=True,
                           text=True, timeout=60)
        try:
            got = json.loads(r.stdout)
        except ValueError:
            got = None
            check('splitTake runs', [r.stderr[-400:]])
        if got:
            clips = got['good'].get('clips')
            check('a take splits at the two long pauses, keeping each scene\'s speech',
                  [] if clips and len(clips) == 3 and abs(clips[0] - 2.35) < 0.2 and abs(clips[1] - 2.0) < 0.2
                  and abs(clips[2] - 1.0) < 0.2 else [got['good']])
            check('a take with too few pauses is refused', [] if 'refused' in got['fewPauses'] else [got['fewPauses']])
            check("a split far from the scenes' word shares is refused",
                  [] if 'refused' in got['stray'] else [got['stray']])

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
