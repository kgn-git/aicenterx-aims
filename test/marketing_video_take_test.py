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
  - silence is found in the sound itself, since the voice's character timings run back to back and hide its pauses:
    a silence longer than 0.35 s inside a scene is shortened to 0.35 s from its middle, so the voice keeps its pace
    without dead air (the user approved the sample), and silence the timings put before a scene's first word is cut
    back to the same 0.15 s lead as any other clip
  - every cut fades in and out over 20 ms, so no cut clicks: each clip's sound starts and ends near zero
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
    return {clips: secs(clips), quiet: clips.every((c) => c.subarray(0, 0.1 * RATE * 2).every((b) => b === 0))};
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
          // Sound times for all but the last character, so only the count is wrong.
          const short = starts.slice(0, -1);
          wordsFromAlignment({characters: chars, character_start_times_seconds: short,
            character_end_times_seconds: short.map((s) => s + 0.08)});
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
// A take silent except for two words, at 1.2-1.6 and 2.6-3.0 s, timed back to back from 0.5 s as the voice times
// them. Cut from 1.05 s (0.15 s before the sound) to 3.08 s, less 0.65 s of the second-long pause, after 0.1 s of PAD.
const gappy = Buffer.alloc(10 * RATE * 2);
for (const [a, b] of [[1.2, 1.6], [2.6, 3.0]]) gappy.fill(7, Math.round(a * RATE) * 2, Math.round(b * RATE) * 2);
const paused = splitTake(gappy, ["One two."], [at("One", 0.5, 1.6), at("two", 1.6, 3.0)])[0];
const firstSound = (clip) => [...Array(clip.length / 2).keys()].find((i) => clip.readInt16LE(i * 2) !== 0) / RATE;
const level = (clip, s) => Math.abs(clip.readInt16LE(Math.round(s * RATE) * 2));
const clip = splitTake(pcm, scenes, words)[1];
const last = clip.length / 2 / RATE - 1 / RATE;
console.log(JSON.stringify({good: run(words), misheard: run(misheard), poor: run(words.slice(0, 3)), aligned,
  paused: {seconds: Math.round((paused.length / 2 / RATE) * 100) / 100, sound: Math.round(firstSound(paused) * 100) / 100},
  fades: {start: level(clip, 0.1), settled: level(clip, 0.15), end: level(clip, last)}}));
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
            # the first consonant of a scene is never clipped, then opens with 0.1 s of silence as a breath.
            want = [1.83, 1.33, 2.33]
            clips = got['good'].get('clips')
            check("each clip runs from its scene's first word to its last",
                  [] if clips and all(abs(a - b) < 0.02 for a, b in zip(clips, want)) and len(clips) == 3
                  else [got['good']])
            check('each clip opens with 0.1 s of silence', [] if got['good'].get('quiet') else [got['good']])
            check('a misheard word and other case or punctuation cut in the same places',
                  [] if got['misheard'].get('clips') == clips else [got['misheard']])
            check('a transcript that matches too little of the script is refused',
                  [] if 'refused' in got['poor'] else [got['poor']])
            want_words = [{'word': 'Hi', 'start': 0, 'end': 0.18}, {'word': 'there,', 'start': 0.4, 'end': 0.98},
                          {'word': 'you.', 'start': 1.1, 'end': 1.48}]
            words = got['aligned'].get('words')
            check("the voice's character timings become words, and misaligned timings are refused",
                  [] if words and len(words) == 3 and got['aligned'].get('refused') and all(
                      w['word'] == v['word'] and abs(w['start'] - v['start']) < 1e-6 and abs(w['end'] - v['end']) < 1e-6
                      for w, v in zip(words, want_words)) else [got['aligned']])
            # The sound starts 0.25 s in: the 0.1 s PAD, then the 0.15 s lead the early timings had stretched.
            check('a silence over 0.35 s inside a scene is shortened, and the lead before the first word is 0.15 s',
                  [] if got['paused'] == {'seconds': 1.48, 'sound': 0.25} else [got['paused']])
            # The synthetic take is a constant 1799 (bytes of 7), so a faded edge reads far below it.
            f = got['fades']
            check('every cut fades in and out',
                  [] if f['start'] < 200 and f['end'] < 200 and f['settled'] == 1799 else [f])

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
