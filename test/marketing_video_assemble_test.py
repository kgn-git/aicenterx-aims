"""Test for the step that renders the final marketing video: video/scripts/assemble.mjs.

Usage:  python test/marketing_video_assemble_test.py

The final video is rendered as one piece, the CvScreeningJourney composition, so its scenes can crossfade; the
fragments stay for review only. Rendering needs video/node_modules, so this checks the wiring and the refusal only.
Checks:
  - the root package.json runs video:assemble through npm --prefix video, and video/package.json runs the script
  - the script renders CvScreeningJourney and keeps the result only after its length, size and codec check
  - it ends the audio inside the last video frame and refuses a video whose audio outlasts the picture, since a
    player that seeks or stops past the last frame shows a blank screen instead of the closing card
  - given an argument it does not take, it exits non-zero with its usage, prints no stack trace, and writes nothing
Prints a JSON report; exit code 1 on any failure.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIDEO = ROOT / 'video'
SCRIPT = VIDEO / 'scripts' / 'assemble.mjs'


def main():
    checks = {}

    def check(name, found):
        checks[name] = {'ok': not found, 'detail': json.dumps(found)[:1500] if found else 'sound'}

    def scripts(p):
        try:
            return json.loads(p.read_text(encoding='utf-8')).get('scripts', {})
        except (OSError, ValueError):
            return {}

    root, video = scripts(ROOT / 'package.json'), scripts(VIDEO / 'package.json')
    check('video:assemble runs the join script through npm --prefix video',
          [f'{k} is {v!r}' for k, v, want in (('video:assemble', root.get('video:assemble'), 'npm --prefix video run assemble'),
                                              ('assemble', video.get('assemble'), 'node scripts/assemble.mjs'))
           if v != want])

    node = shutil.which('node')
    if not node:
        check('node is on PATH', ['node is not on PATH'])
    elif not SCRIPT.is_file():
        check('video/scripts/assemble.mjs exists', [str(SCRIPT)])
    else:
        text = SCRIPT.read_text(encoding='utf-8')
        check('it renders CvScreeningJourney and checks the result before keeping it',
              [] if '"CvScreeningJourney"' in text and 'ffprobe' in text and 'renameSync' in text else ['missing'])
        check('it ends the audio inside the last video frame and refuses audio that outlasts the picture',
              [] if 'atrim=end=' in text and '-c:v", "copy"' in text and 'outlasts the picture' in text else ['missing'])
        with tempfile.TemporaryDirectory() as empty:
            r = subprocess.run([node, str(SCRIPT), '--bogus'], capture_output=True, text=True, timeout=60, cwd=VIDEO,
                               env={**os.environ, 'VIDEO_OUT': empty})
            written = sorted(os.listdir(empty))
        out = r.stdout + r.stderr
        check('given an argument it does not take, it refuses with its usage and writes nothing',
              [] if r.returncode != 0 and 'npm run video:assemble' in r.stderr and '    at ' not in out and not written
              else [r.returncode, out[-300:], written])

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
