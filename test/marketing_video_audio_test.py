"""Test for the marketing video's narration: video/public/audio/<scene>.wav and the audioSeconds in the timeline.

Usage:  python test/marketing_video_audio_test.py

Each clip is committed, so the video renders without the text-to-speech model, and each scene plays for its planned
seconds or for its clip plus a short tail, whichever is longer. Checks:
  - the guard: video/scripts/narrate.mjs, run without its env file, fails closed when OPENAI_API_KEY or
    OPENAI_TTS_MODEL is missing or the fragment is unknown: it exits non-zero with no stack trace, never prints the
    key, and changes no clip and not timeline.json
  - every timeline scene has a clip and there is no other clip; each is a 24 kHz 16-bit mono PCM WAV whose header
    sizes match the file
  - each scene's audioSeconds equals its clip's length, and the scenes, each stretched to its clip plus 0.3 s, run
    66 s at most (the user's tolerance of 60 +/- 6 s until the combined review)
Prints a JSON report; exit code 1 on any failure.
"""
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIDEO = ROOT / 'video'
AUDIO = VIDEO / 'public' / 'audio'
TIMELINE = VIDEO / 'src' / 'timeline.json'
NARRATE = VIDEO / 'scripts' / 'narrate.mjs'
RATE, TAIL, MAX_TOTAL = 24000, 0.3, 66.0
FAKE_KEY = 'sk-test-0000-not-a-real-key'


def snapshot():
    """The bytes of timeline.json and a {clip name: sha256} map of the audio folder, empty when it is absent."""
    clips = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(AUDIO.glob('*'))} if AUDIO.is_dir() else {}
    return TIMELINE.read_bytes(), clips


def guard_problems(node, ids):
    """Each refused narrate run that exits 0, prints a stack trace or the key, or touches a clip or the timeline."""
    env = {k: v for k, v in os.environ.items() if not k.startswith('OPENAI_')}
    cases = {'no key': ([], env, 'OPENAI_API_KEY'),
             'a key but no model': ([], {**env, 'OPENAI_API_KEY': FAKE_KEY}, 'OPENAI_TTS_MODEL'),
             'an unknown fragment': (['../x'], {**env, 'OPENAI_API_KEY': FAKE_KEY, 'OPENAI_TTS_MODEL': 'm'},
                                     ', '.join(ids))}
    bad = []
    for name, (args, child_env, named) in cases.items():
        before = snapshot()
        r = subprocess.run([node, str(NARRATE), *args], capture_output=True, text=True, timeout=60, cwd=ROOT,
                           env=child_env)
        out = r.stdout + r.stderr
        if r.returncode == 0 or '    at ' in out or FAKE_KEY in out or snapshot() != before or named not in r.stderr:
            bad.append(f'{name}: exit {r.returncode}, output {out[-200:]!r}')
    return bad


def wav_problems(path):
    """What is wrong with a clip's header, and its length in seconds; the length is None when it cannot be read."""
    data = path.read_bytes()
    if len(data) < 44:
        return [f'{path.name} is shorter than a WAV header'], None
    riff, size, wave, fmt, fmt_len, pcm, channels, rate, byte_rate, align, bits, tag, data_len = struct.unpack(
        '<4sI4s4sIHHIIHH4sI', data[:44])
    want = (b'RIFF', len(data) - 8, b'WAVE', b'fmt ', 16, 1, 1, RATE, RATE * 2, 2, 16, b'data', len(data) - 44)
    got = (riff, size, wave, fmt, fmt_len, pcm, channels, rate, byte_rate, align, bits, tag, data_len)
    bad = [f'{path.name}: header {got} is not 24 kHz 16-bit mono PCM sized to the file'] if got != want else []
    return bad, data_len / (RATE * 2)


def main():
    checks = {}

    def check(name, problems):
        checks[name] = {'ok': not problems, 'detail': json.dumps(problems)[:1500] if problems else 'sound'}

    timeline = json.loads(TIMELINE.read_text(encoding='utf-8'))
    ids = list(json.loads((VIDEO / 'src' / 'compositions.json').read_text(encoding='utf-8')).values())
    node = shutil.which('node')
    check('narrate fails closed without its settings or with an unknown fragment',
          guard_problems(node, ids) if node else ['node is not on PATH'])

    scenes = {s['id']: s for s in timeline['scenes']}
    clips = {p.stem: p for p in AUDIO.glob('*.wav')} if AUDIO.is_dir() else {}
    others = sorted(p.name for p in AUDIO.glob('*') if p.suffix != '.wav' or p.stem not in scenes) if AUDIO.is_dir() else []
    check('every scene has a clip, and there is no other file', [f'no clip for {s}' for s in scenes if s not in clips]
          + [f'unexpected {n}' for n in others])
    lengths, problems = {}, []
    for sid, path in clips.items():
        bad, lengths[sid] = wav_problems(path)
        problems += bad
    check('each clip is a 24 kHz 16-bit mono PCM WAV sized to its header', problems)
    check("each scene's audioSeconds equals its clip's length",
          [f'{s}: audioSeconds {scenes[s].get("audioSeconds")}, clip {n:.3f} s' for s, n in lengths.items()
           if n is not None and abs(scenes[s].get('audioSeconds', -1) - n) > 0.001])
    total = sum(max(s['seconds'], s.get('audioSeconds', 0) + TAIL) for s in timeline['scenes'])
    check(f'the scenes, stretched to fit their clips, run {MAX_TOTAL:g} s at most',
          [] if total <= MAX_TOTAL else [f'{total:.2f} s'])

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
