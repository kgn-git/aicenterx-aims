"""Test for cutting one continuous narration take into scene clips: splitTake in video/scripts/take.mjs.

Usage:  python test/marketing_video_take_test.py

The narration is voiced in one take so the voice keeps one pace and energy, then cut where each scene's words begin
and end, using a transcript's word timings. A wrong cut would put words in the wrong scene, so the transcript is
matched to the script word by word and the cut is refused when too little of it matches. It runs on synthetic
24 kHz 16-bit PCM through node, so no voice or network is needed. Checks:
  - each clip runs from just before its scene's first word to just after its last, and clips never overlap
  - a transcript with one misheard word and different case and punctuation still cuts in the same places
  - a transcript that matches too little of the script is refused
Prints a JSON report; exit code 1 on any failure.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAKE = ROOT / 'video' / 'scripts' / 'take.mjs'

PROGRAM = """
import {splitTake} from %s;
const RATE = 24000;
const pcm = Buffer.alloc(10 * RATE * 2);
const scenes = ["One two three.", "Four five.", "Six seven eight nine."];
const at = (word, start, end) => ({word, start, end});
const words = [at("One", 0.5, 0.9), at("two", 1.0, 1.4), at("three.", 1.5, 2.0), at("Four", 3.0, 3.4),
  at("five", 3.5, 4.0), at("Six", 5.0, 5.4), at("seven", 5.5, 5.9), at("eight", 6.0, 6.4), at("nine", 6.5, 7.0)];
const misheard = words.map((w) => (w.word === "five" ? {...w, word: "Fine,"} : {...w, word: w.word.toUpperCase()}));
const secs = (clips) => clips.map((c) => Math.round((c.length / 2 / RATE) * 100) / 100);
const run = (ws) => {
  try {
    return {clips: secs(splitTake(pcm, scenes, ws))};
  } catch (e) {
    return {refused: String(e.message)};
  }
};
console.log(JSON.stringify({good: run(words), misheard: run(misheard), poor: run(words.slice(0, 3))}));
"""


def main():
    checks = {}

    def check(name, found):
        checks[name] = {'ok': not found, 'detail': json.dumps(found)[:1500] if found else 'sound'}

    node = shutil.which('node')
    if not node:
        check('node is on PATH', ['node is not on PATH'])
    elif not TAKE.is_file():
        check('video/scripts/take.mjs exists', ['missing'])
    else:
        r = subprocess.run([node, '--input-type=module', '-e', PROGRAM % json.dumps(TAKE.as_uri())],
                           capture_output=True, text=True, timeout=60)
        try:
            got = json.loads(r.stdout)
        except ValueError:
            got = None
            check('splitTake runs', [r.stderr[-400:]])
        if got:
            # Scenes span 0.5-2.0, 3.0-4.0 and 5.0-7.0 s; each clip adds 0.15 s before and 0.08 s after, so
            # the first consonant of a scene is never clipped.
            want = [1.73, 1.23, 2.23]
            clips = got['good'].get('clips')
            check("each clip runs from its scene's first word to its last",
                  [] if clips and all(abs(a - b) < 0.02 for a, b in zip(clips, want)) and len(clips) == 3
                  else [got['good']])
            check('a misheard word and other case or punctuation cut in the same places',
                  [] if got['misheard'].get('clips') == clips else [got['misheard']])
            check('a transcript that matches too little of the script is refused',
                  [] if 'refused' in got['poor'] else [got['poor']])

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
