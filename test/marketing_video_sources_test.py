"""Test for the law chips of the marketing video's mitigations, built by video/src/sources.mjs.

Usage:  python test/marketing_video_sources_test.py

A mitigation's EU AI Act chip must cite only that act: other EUR-Lex law, such as the GDPR, sits on the same site, so
a host-based rule would label a GDPR article as an EU AI Act article. Reads the chip text of every mitigation shown
through video/scripts/sources.mjs, so the rule is checked where the scene takes it from. Checks:
  - each shown mitigation's chip is "EU AI Act · Article N" or "EU AI Act · Articles N, M and K" from exactly the
    article numbers in its sources titled "EU AI Act ...", in order, or empty when it has none
Prints a JSON report; exit code 1 on any failure.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIDEO = ROOT / 'video'
SCRIPT = VIDEO / 'scripts' / 'sources.mjs'


def label(mitigation):
    """The chip text the rule gives a mitigation."""
    n = [int(x) for s in mitigation['sources'] if s.get('title', '').startswith('EU AI Act')
         for x in re.findall(r'Article (\d+)', s['title'])]
    if not n:
        return ''
    return f'EU AI Act · Article {n[0]}' if len(n) == 1 else f'EU AI Act · Articles {", ".join(map(str, n[:-1]))} and {n[-1]}'


def main():
    checks = {}

    def check(name, ok, detail=''):
        checks[name] = {'ok': bool(ok), 'detail': detail if isinstance(detail, str) else json.dumps(detail)[:1500]}

    node = shutil.which('node')
    got, why = None, 'node is not on PATH'
    if node:
        r = subprocess.run([node, str(SCRIPT)], capture_output=True, encoding='utf-8', timeout=60, cwd=ROOT)
        try:
            got, why = json.loads(r.stdout), 'printed'
        except ValueError:
            why = f'sources.mjs failed: {r.stderr[-300:]!r}'
    check('video/scripts/sources.mjs prints each shown mitigation with its chip', got is not None, why)
    if got is not None:
        timeline = json.loads((VIDEO / 'src' / 'timeline.json').read_text(encoding='utf-8'))
        shown = next(s for s in timeline['scenes'] if s['id'] == 'mitigations')['dataRefs']['mitigations']['shown']
        data = json.loads((ROOT / 'tools' / 'data' / 'mitigation_suggestions.json').read_text(encoding='utf-8'))
        by_id = {m['id']: m for ms in data['risks'].values() for m in ms}
        want = {i: label(by_id[i]) for i in shown}
        gdpr = any('GDPR' in s.get('title', '') for i in shown for s in by_id[i]['sources'])
        check('a shown mitigation cites the GDPR, so the rule is exercised', gdpr)
        check('every chip cites only the EU AI Act articles of its mitigation', got == want, {'got': got, 'want': want})

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
