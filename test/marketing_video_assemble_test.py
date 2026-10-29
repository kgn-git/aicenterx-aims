"""Test for the step that joins the marketing video's fragments: video/scripts/assemble.mjs.

Usage:  python test/marketing_video_assemble_test.py

The join copies the approved fragments without re-encoding them, so it must refuse to run on an incomplete set rather
than release a shorter video. Rendering needs video/node_modules, so this checks the wiring and the refusal only.
Checks:
  - the root package.json runs video:assemble through npm --prefix video, and video/package.json runs the script
  - with any fragment missing, the script exits non-zero, names the missing fragment and the command that renders it,
    prints no stack trace, and writes no joined video
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
        first = next(iter(json.loads((VIDEO / 'src' / 'compositions.json').read_text(encoding='utf-8')).values()))
        with tempfile.TemporaryDirectory() as empty:
            r = subprocess.run([node, str(SCRIPT)], capture_output=True, text=True, timeout=60, cwd=VIDEO,
                               env={**os.environ, 'VIDEO_OUT': empty})
            written = sorted(os.listdir(empty))
        out = r.stdout + r.stderr
        check('with a fragment missing, it refuses, names it and how to render it, and writes nothing',
              [] if r.returncode != 0 and first in r.stderr and 'video:render:fragment' in r.stderr
              and '    at ' not in out and not written else [r.returncode, out[-300:], written])

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
