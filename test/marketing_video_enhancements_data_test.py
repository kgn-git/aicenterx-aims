"""Schema test for the marketing video's model enhancements, video/data/model_enhancements.json.

Usage:  python test/marketing_video_enhancements_data_test.py

Step 4 of the video shows enhancements that put a saved mitigation into effect, so each must point at a real mitigation
of the CV Screening Assistant, and together they may need no more than the 3 risks the video saves. Checks:
  - the key rule in test/video_keys.py: a matched suggestion resolves to its register risk
  - the curated data: 3-4 entries with a unique enh-<slug> id, one of the three kinds (each used at least once), a
    name of at most 6 words, a how of at most 20 words, a human-feedback entry whose name and how both say the
    feedback is audited (unaudited recruiter ratings would re-learn the bias the video names as a risk), a
    mitigationId of a CV Screening Assistant risk, all of them within 3 risks, and a source that is either a titled https url on an allowed host or exactly {"illustrative": true}
  - the guard: one broken copy per rule that spans files (unknown mitigation, another initiative's mitigation, more
    than 3 risks), each rejected by the validator for that rule
Prints a JSON report; exit code 1 on any failure.
"""
import copy
import json
import re
import sys
from pathlib import Path

from source_url import url_ok
from video_keys import hiring_mitigations, mitigation_key

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'video' / 'data' / 'model_enhancements.json'
RISK_DATA = ROOT / 'tools' / 'data' / 'risk_suggestions.json'
MITIGATION_DATA = ROOT / 'tools' / 'data' / 'mitigation_suggestions.json'
KINDS = ('fine-tuning', 'agent workflow', 'human feedback')
HOSTS = ('eur-lex.europa.eu', 'airisk.mit.edu')
MAX_RISKS = 3


def text_of(s, most):
    """A string of 1 to most words."""
    return isinstance(s, str) and 1 <= len(s.split()) <= most


def validate(data, hiring):
    """Every rule broken by data, as readable strings; empty when the data is sound."""
    if not isinstance(data, dict) or set(data) != {'enhancements'} or not isinstance(data['enhancements'], list):
        return ['top level must be exactly {enhancements: [...]}']
    items = data['enhancements']
    bad = [] if 3 <= len(items) <= 4 else [f'{len(items)} enhancements, want 3-4']
    ids = [str(e.get('id')) for e in items]
    if len(set(ids)) != len(ids):
        bad.append('duplicate enhancement ids')
    if not set(KINDS) <= {e.get('kind') for e in items}:
        bad.append(f'every kind must be used at least once: {KINDS}')
    for e in items:
        eid = str(e.get('id'))
        if not re.fullmatch(r'enh-[a-z0-9]+(?:-[a-z0-9]+)*', eid):
            bad.append(f'id {eid!r} is not enh-<slug>')
        if e.get('kind') not in KINDS:
            bad.append(f'{eid}: unknown kind {e.get("kind")!r}')
        if not text_of(e.get('name'), 6):
            bad.append(f'{eid}: name must have 1-6 words')
        if not text_of(e.get('how'), 20):
            bad.append(f'{eid}: how must have 1-20 words')
        elif e.get('kind') == 'human feedback' and not all(re.search(r'\baudit', str(e.get(k)), re.I) for k in ('name', 'how')):
            bad.append(f'{eid}: a human-feedback enhancement must say in its name and how that the feedback is audited')
        if e.get('mitigationId') not in hiring:
            bad.append(f'{eid}: {e.get("mitigationId")!r} is not a mitigation of a CV Screening Assistant risk')
        s = e.get('source')
        if s != {'illustrative': True} and not (isinstance(s, dict) and set(s) == {'title', 'url'} and text_of(s['title'], 99)
                                                and any(url_ok(s['url'], h) for h in HOSTS)):
            bad.append(f'{eid}: source must be a titled https url on {HOSTS} or exactly {{"illustrative": true}}')
    risks = {hiring[e.get('mitigationId')] for e in items if e.get('mitigationId') in hiring}
    if len(risks) > MAX_RISKS:
        bad.append(f'entries span {len(risks)} risks {sorted(risks)}, at most {MAX_RISKS}')
    return bad


def broken_copies(data, hiring, mitigation_data):
    """{rule: data breaking only that rule, and a fragment its rejection must contain}."""
    foreign = mitigation_data['risks']['r2'][0]['id']
    spread = [next(m for m, k in hiring.items() if k == r) for r in sorted(set(hiring.values()))[:MAX_RISKS + 1]]

    def edit(fn):
        d = copy.deepcopy(data)
        fn(d['enhancements'])
        return d

    def widen(es):
        es[:] = [dict(es[i % len(es)], id=f'enh-spread-{i}', mitigationId=mid) for i, mid in enumerate(spread)]

    return {
        'unknown mitigation': (edit(lambda es: es[0].update(mitigationId='m-r4-9')), 'is not a mitigation'),
        "another initiative's mitigation": (edit(lambda es: es[0].update(mitigationId=foreign)), 'is not a mitigation'),
        f'more than {MAX_RISKS} risks': (edit(widen), f'at most {MAX_RISKS}'),
    }


def main():
    checks = {}

    def check(name, ok, detail=''):
        checks[name] = {'ok': bool(ok), 'detail': detail if isinstance(detail, str) else json.dumps(detail)[:1500]}

    risk_data = json.loads(RISK_DATA.read_text(encoding='utf-8'))
    mitigation_data = json.loads(MITIGATION_DATA.read_text(encoding='utf-8'))
    hiring = hiring_mitigations(risk_data, mitigation_data)
    by_id = {s['id']: s for s in risk_data['initiatives']['hiring']['suggestions']}
    check('a matched suggestion keeps its mitigations under its register risk, any other under its own id',
          mitigation_key(by_id['s-hiring-1']) == 'r4' and mitigation_key(by_id['s-hiring-3']) == 's-hiring-3'
          and hiring.get('m-r4-1') == 's-hiring-1' and 'm-r2-1' not in hiring, sorted(set(hiring.values())))
    try:
        data, why = json.loads(DATA.read_text(encoding='utf-8')), str(DATA)
    except (OSError, ValueError) as e:
        data, why = None, repr(e)
    check('video/data/model_enhancements.json exists and parses', data is not None, why)
    if data is not None:
        try:
            problems = validate(data, hiring)
        except Exception as e:  # noqa: BLE001 - a malformed shape is reported as a failure, never a crash
            problems = [f'validator crashed: {e!r}']
        check('curated enhancements pass every rule', not problems, problems or 'sound')
        if not problems:
            missed = [rule for rule, (d, why) in broken_copies(data, hiring, mitigation_data).items()
                      if [why in x for x in validate(d, hiring)] != [True]]
            check('validator rejects each broken copy for its own rule and no other', not missed, missed or 'all rejected')

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
