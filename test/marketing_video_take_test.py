"""Test for cutting one continuous narration take into scene clips: splitTake and wordsFromAlignment in
video/scripts/take.mjs.

Usage:  python test/marketing_video_take_test.py

The narration is voiced in one take so the voice keeps one pace and energy, then cut where each scene's words begin
and end, using a transcript's word timings. A wrong cut would put words in the wrong scene, so the transcript is
matched to the script word by word and the cut is refused when too little of it matches. It runs on synthetic
24 kHz 16-bit PCM through node, so no voice or network is needed. Checks:
  - the voice's per-character timings become words, each from its first character's start to its last one's end,
    split at any whitespace; timings that do not line up with the characters are refused
  - each clip runs from just before its scene's first word to just after its last, and clips never overlap
  - a pause longer than 0.35 s between two words of one scene is shortened to 0.35 s, cut from its middle, so the
    voice keeps its pace without dead air (the user approved the sample)
  - every cut fades in and out over 20 ms, so no cut clicks: each clip's sound starts and ends near zero, and so does
    the join where a pause was shortened
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
import * as take from %s;
const {splitTake} = take;
const wordsFromAlignment = (a) => take.wordsFromAlignment(a);
const RATE = 24000;
const pcm = Buffer.alloc(10 * RATE * 2, 7);
const scenes = ["One two three.", "Four five.", "Six seven eight nine."];
const at = (word, start, end) => ({word, start, end});
const words = [at("One", 0.5, 0.9), at("two", 1.0, 1.4), at("three.", 1.5, 2.0), at("Four", 3.0, 3.4),
  at("five", 3.5, 4.0), at("Six", 5.0, 5.4), at("seven", 5.5, 5.9), at("eight", 6.0, 6.4), at("nine", 6.5, 7.0)];
const misheard = words.map((w) => (w.word === "five" ? {...w, word: "Fine,"} : {...w, word: w.word.toUpperCase()}));
const secs = (clips) => clips.map((c) => Math.round((c.length / 2 / RATE) * 100) / 100);
const run = (ws) => {
  try {
    const clips = splitTake(pcm, scenes, ws);
    return {clips: secs(clips), quiet: clips.every((c) => c.subarray(0, 0.2 * RATE * 2).every((b) => b === 0))};
  } catch (e) {
    return {refused: String(e.message)};
  }
};
const aligned = (() => {
  const text = "Hi  there,\\nyou.";
  const chars = [...text];
  const starts = chars.map((_, i) => i * 0.1);
  try {
    return {
      words: wordsFromAlignment({characters: chars, character_start_times_seconds: starts,
        character_end_times_seconds: starts.map((s) => s + 0.08)}),
      refused: (() => {
        try {
          wordsFromAlignment({characters: chars, character_start_times_seconds: starts.slice(1),
            character_end_times_seconds: starts});
          return false;
        } catch {
          return true;
        }
      })(),
    };
  } catch (e) {
    return {error: String(e.message)};
  }
})();
// One scene whose two words sit a full second apart: 0.35-2.38 s of take, less 0.65 s of pause, after 0.2 s of PAD.
const paused = splitTake(pcm, ["One two."], [at("One", 0.5, 0.9), at("two", 1.9, 2.3)])[0];
const level = (clip, s) => Math.abs(clip.readInt16LE(Math.round(s * RATE) * 2));
const clip = splitTake(pcm, scenes, words)[1];
const last = clip.length / 2 / RATE - 1 / RATE;
// The join sits where the shortened pause was cut: 0.2 s PAD + 0.55 s of take before the pause's middle + 0.175 s.
const join = 0.2 + (0.9 - 0.35) + 0.5 * 0.35;
console.log(JSON.stringify({good: run(words), misheard: run(misheard), poor: run(words.slice(0, 3)), aligned,
  paused: Math.round((paused.length / 2 / RATE) * 100) / 100,
  fades: {start: level(clip, 0.2), settled: level(clip, 0.25), end: level(clip, last),
          join: level(paused, join), beside: level(paused, join + 0.05)}}));
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
            # the first consonant of a scene is never clipped, then opens with 0.2 s of silence as a breath.
            want = [1.93, 1.43, 2.43]
            clips = got['good'].get('clips')
            check("each clip runs from its scene's first word to its last",
                  [] if clips and all(abs(a - b) < 0.02 for a, b in zip(clips, want)) and len(clips) == 3
                  else [got['good']])
            check('each clip opens with 0.2 s of silence', [] if got['good'].get('quiet') else [got['good']])
            check('a misheard word and other case or punctuation cut in the same places',
                  [] if got['misheard'].get('clips') == clips else [got['misheard']])
            check('a transcript that matches too little of the script is refused',
                  [] if 'refused' in got['poor'] else [got['poor']])
            want_words = [{'word': 'Hi', 'start': 0, 'end': 0.18}, {'word': 'there,', 'start': 0.4, 'end': 0.98},
                          {'word': 'you.', 'start': 1.1, 'end': 1.58}]
            words = got['aligned'].get('words')
            check("the voice's character timings become words, and misaligned timings are refused",
                  [] if words and len(words) == 3 and got['aligned'].get('refused') and all(
                      w['word'] == v['word'] and abs(w['start'] - v['start']) < 1e-6 and abs(w['end'] - v['end']) < 1e-6
                      for w, v in zip(words, want_words)) else [got['aligned']])
            check('a pause over 0.35 s inside a scene is shortened to 0.35 s',
                  [] if got['paused'] == 1.58 else [got['paused']])
            # The synthetic take is a constant 1799 (bytes of 7), so a faded edge reads far below it.
            f = got['fades']
            check('every cut fades in and out, including the join of a shortened pause',
                  [] if f['start'] < 200 and f['end'] < 200 and f['join'] < 200 and f['settled'] == 1799
                  and f['beside'] == 1799 else [f])

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
