"""Test for the controls the marketing video shows beside each mitigation: video/data/controls_hiring.json.

Usage:  python test/marketing_video_controls_test.py

Each mitigation card names its control by key and objective, as the prototype's controlButton does, so the video
must use the prototype's own objectives. Checks:
  - the file holds exactly the controls of the mitigations the timeline shows, each once
  - each objective equals the objective of the same key in CONTROLS in index.html
  - the guard: a changed objective and a missing control are each rejected
Prints a JSON report; exit code 1 on any failure.
"""
import copy
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'video' / 'data' / 'controls_hiring.json'


def prototype_controls(html):
    """{key: objective} from CONTROLS in index.html."""
    block = html[html.index('var CONTROLS'):html.index('];', html.index('var CONTROLS'))]
    return dict(re.findall(r'key:"([^"]+)",objective:"([^"]+)"', block))


def needed_keys(root):
    """The control keys of the mitigations the timeline's mitigations scene shows."""
    timeline = json.loads((root / 'video' / 'src' / 'timeline.json').read_text(encoding='utf-8'))
    data = json.loads((root / 'tools' / 'data' / 'mitigation_suggestions.json').read_text(encoding='utf-8'))
    shown = next(s for s in timeline['scenes'] if s['id'] == 'mitigations')['dataRefs']['mitigations']['shown']
    by_id = {m['id']: m for ms in data['risks'].values() for m in ms}
    return {by_id[m]['controlKey'] for m in shown}


def problems(data, controls, keys):
    """Every rule the file breaks, as readable strings; empty when it is sound."""
    if not isinstance(data, dict) or set(data) != {'controls'} or not isinstance(data['controls'], list):
        return ['top level must be exactly {controls: [...]}']
    got = [c.get('key') for c in data['controls'] if isinstance(c, dict)]
    bad = [] if sorted(got) == sorted(keys) and len(set(got)) == len(got) else [f'keys {got} must be exactly {sorted(keys)}']
    bad += [f'{c.get("key")}: objective {c.get("objective")!r} is not the prototype\'s {controls.get(c.get("key"))!r}'
            for c in data['controls'] if isinstance(c, dict) and c.get('objective') != controls.get(c.get('key'))]
    return bad


def main():
    checks = {}

    def check(name, found):
        checks[name] = {'ok': not found, 'detail': json.dumps(found)[:1500] if found else 'sound'}

    controls, keys = prototype_controls((ROOT / 'index.html').read_text(encoding='utf-8')), needed_keys(ROOT)
    check('index.html holds every control the shown mitigations use', sorted(keys - set(controls)))
    try:
        data = json.loads(DATA.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        data = None
        check('video/data/controls_hiring.json exists and parses', [repr(e)])
    if data is not None:
        found = problems(data, controls, keys)
        check("each control is the prototype's own, and exactly those the mitigations use", found)
        if not found:
            changed, missing = copy.deepcopy(data), copy.deepcopy(data)
            changed['controls'][0]['objective'] += ' (edited)'
            missing['controls'].pop()
            check('each rule rejects a broken copy',
                  [k for k, d in {'a changed objective': changed, 'a missing control': missing}.items()
                   if not problems(d, controls, keys)])

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
