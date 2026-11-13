"""Test for the marketing video's stock footage: video/src/footage.json and video/scripts/footage.mjs.

Usage:  python test/marketing_video_footage_test.py

The people in the pitch are Pexels stock clips. The repo is public and the clips are not ours to redistribute, so
they are downloaded into a git-ignored folder; what is committed is where each comes from and its sha256, so the
same bytes come back on any machine. Checks:
  - footage.json is {clips: {id: {pexels, url, sha256, from}}}: a Pexels video id, an https URL on
    videos.pexels.com under that id, a 64-hex sha256 and a start second of 0 or more
  - the clips are exactly the ones the timeline's scenes play, so none is missing and none is fetched for nothing
  - video/public/footage/ is ignored by git, so no clip is ever committed
  - the guard: footage.mjs, run against a footage.json copy that points off Pexels or carries a malformed hash,
    exits non-zero with a message naming the clip, without a stack trace and without writing a file
  - when the clips are present, each matches its recorded sha256 (skipped, and said so, when they are not)
Prints a JSON report; exit code 1 on any failure.
"""
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIDEO = ROOT / 'video'
FOOTAGE = VIDEO / 'src' / 'footage.json'
TIMELINE = VIDEO / 'src' / 'timeline.json'
SCRIPT = VIDEO / 'scripts' / 'footage.mjs'
FOLDER = VIDEO / 'public' / 'footage'
HEX = re.compile(r'[0-9a-f]{64}')


def clip_problems(clips):
    """Every malformed clip entry, as readable strings."""
    if not isinstance(clips, dict) or not clips:
        return ['clips must be a non-empty {id: entry} object']
    bad = []
    for cid, c in clips.items():
        if not (re.fullmatch(r'[a-z][a-z0-9-]*', cid) and isinstance(c, dict) and set(c) == {'pexels', 'url', 'sha256', 'from'}):
            bad.append(f'{cid}: must be a lower-case id with exactly pexels, url, sha256 and from')
            continue
        if not (isinstance(c['pexels'], int) and c['pexels'] > 0 and isinstance(c['url'], str)
                and re.fullmatch(rf'https://videos\.pexels\.com/video-files/{c["pexels"]}/[\w.-]+\.mp4', c['url'])):
            bad.append(f'{cid}: url must be an https mp4 on videos.pexels.com under video {c["pexels"]}')
        if not (isinstance(c['sha256'], str) and HEX.fullmatch(c['sha256'])):
            bad.append(f'{cid}: sha256 must be 64 lower-case hex characters')
        if not (isinstance(c['from'], (int, float)) and not isinstance(c['from'], bool) and c['from'] >= 0):
            bad.append(f'{cid}: from must be a start second of 0 or more')
    return bad


def guard_problems(node, data):
    """Each broken footage.json that footage.mjs accepts, or refuses badly."""
    first = next(iter(data['clips']))
    cases = {'a URL off Pexels': ('url', 'https://example.com/clip.mp4'), 'a malformed hash': ('sha256', 'abc')}
    bad = []
    for name, (key, value) in cases.items():
        broken = copy.deepcopy(data)
        broken['clips'][first][key] = value
        with tempfile.TemporaryDirectory() as tmp:
            plan, out = Path(tmp) / 'footage.json', Path(tmp) / 'out'
            plan.write_text(json.dumps(broken), encoding='utf-8')
            r = subprocess.run([node, str(SCRIPT)], capture_output=True, text=True, timeout=60, cwd=ROOT,
                               env={**os.environ, 'FOOTAGE_PLAN': str(plan), 'FOOTAGE_DIR': str(out)})
            text = r.stdout + r.stderr
            if r.returncode == 0 or '    at ' in text or first not in r.stderr or (out.exists() and any(out.iterdir())):
                bad.append(f'{name}: exit {r.returncode}, output {text[-200:]!r}')
    return bad


def main():
    checks = {}

    def check(name, problems):
        checks[name] = {'ok': not problems, 'detail': json.dumps(problems)[:1500] if problems else 'sound'}

    try:
        data = json.loads(FOOTAGE.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        data = None
        check('video/src/footage.json exists and parses', [repr(e)])
    if data is not None:
        clips = data.get('clips') if isinstance(data, dict) and set(data) == {'clips'} else None
        check('footage.json names each clip by its Pexels id, URL, sha256 and start', clip_problems(clips)
              if clips is not None else ['top level must be exactly {clips: {...}}'])
        timeline = json.loads(TIMELINE.read_text(encoding='utf-8'))
        played = {c for s in timeline['scenes'] for c in s['dataRefs'].get('footage', [])}
        listed = set(clips or {})
        check('the clips are exactly those the scenes play',
              [f'{c} is played but not listed' for c in sorted(played - listed)]
              + [f'{c} is listed but never played' for c in sorted(listed - played)])
        r = subprocess.run(['git', 'check-ignore', '-q', 'video/public/footage/x.mp4'], cwd=ROOT)
        check('video/public/footage/ is ignored by git', [] if r.returncode == 0 else ['not ignored'])
        node = shutil.which('node')
        if clips and not clip_problems(clips):
            check('footage.mjs refuses a clip off Pexels or with a malformed hash, naming it and writing nothing',
                  guard_problems(node, data) if node and SCRIPT.is_file() else ['node or footage.mjs is missing'])
            present = {c: FOLDER / f'{c}.mp4' for c in clips if (FOLDER / f'{c}.mp4').is_file()}
            if present:
                check('each downloaded clip matches its recorded sha256',
                      [f'{c} differs' for c, p in present.items()
                       if hashlib.sha256(p.read_bytes()).hexdigest() != clips[c]['sha256']])
            else:
                checks['each downloaded clip matches its recorded sha256'] = {
                    'ok': True, 'detail': 'skipped: no clip downloaded; run npm run video:footage'}

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
