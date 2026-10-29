"""Test for the marketing video's traceability graph, built by video/src/trace.mjs.

Usage:  python test/marketing_video_trace_test.py

The trace scene shows every saved enhancement traced back to its mitigation and risk. It is the video's claim that
governance is traceable, so it must draw only links the curated data holds. Reads the rows through
video/scripts/trace.mjs, so the rule is checked where the scene takes it from. Checks:
  - one row per saved enhancement, grouped by risk so each risk is drawn once beside its rows: the risks in the order
    their first enhancement is saved, and within a risk the saving order
  - each row's mitigation is the one the enhancement puts into effect, and is saved
  - each row's risk is the saved risk whose mitigations include that mitigation
  - each row's articles are exactly those its mitigation's EU AI Act sources cite; other EUR-Lex law such as the GDPR
    is not the EU AI Act
  - every label is the one video/data/trace_labels.json holds, 1 to 6 words, and that file labels exactly the saved
    risks and the mitigations drawn
  - the guard: a row naming another risk is rejected, and the article rule skips a GDPR source
Prints a JSON report; exit code 1 on any failure.
"""
import copy
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from video_keys import hiring_mitigations

ROOT = Path(__file__).resolve().parent.parent
VIDEO = ROOT / 'video'
SCRIPT = VIDEO / 'scripts' / 'trace.mjs'
LABELS = VIDEO / 'data' / 'trace_labels.json'


def load(p):
    return json.loads(p.read_text(encoding='utf-8'))


def articles(mitigation):
    """The article numbers a mitigation's EU AI Act sources cite, in order."""
    return [int(n) for s in mitigation['sources'] if s.get('title', '').startswith('EU AI Act')
            for n in re.findall(r'Article (\d+)', s['title'])]


def validate(rows, data):
    """Every rule the rows break, as readable strings; empty when they are sound."""
    by_scene = {s['id']: s for s in data['timeline']['scenes']}
    saved = {k: by_scene[k]['dataRefs'][k]['saved'] for k in ('risks', 'mitigations', 'enhancements')}
    enh = {e['id']: e for e in data['enhancements']['enhancements']}
    mits = {m['id']: m for ms in data['mitigations']['risks'].values() for m in ms}
    answers = hiring_mitigations(data['risks'], data['mitigations'])
    labels = data['labels']
    if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
        return ['trace.mjs must print a list of rows']
    bad = []
    first = {}
    for e in saved['enhancements']:
        first.setdefault(answers.get(enh.get(e, {}).get('mitigationId')), len(first))
    grouped = sorted(saved['enhancements'], key=lambda e: first[answers.get(enh.get(e, {}).get('mitigationId'))])
    if [r.get('enhancement', {}).get('id') for r in rows] != grouped:
        bad.append(f'the rows must be the saved enhancements grouped by risk, {grouped}')
    for r in rows:
        e, m, k = (r.get(x, {}) for x in ('enhancement', 'mitigation', 'risk'))
        eid = e.get('id')
        if eid not in enh:
            continue
        if m.get('id') != enh[eid]['mitigationId'] or m.get('id') not in saved['mitigations']:
            bad.append(f'{eid}: the mitigation must be the saved one it puts into effect')
            continue
        if k.get('id') != answers.get(m['id']) or k.get('id') not in saved['risks']:
            bad.append(f'{eid}: the risk must be the saved risk that {m["id"]} answers')
        if m.get('articles') != articles(mits[m['id']]):
            bad.append(f'{eid}: the articles must be those {m["id"]} cites, {articles(mits[m["id"]])}')
        if e.get('label') != enh[eid]['name'] or m.get('label') != labels.get(m['id']) \
                or k.get('label') != labels.get(k.get('id')):
            bad.append(f'{eid}: labels must come from model_enhancements.json and trace_labels.json')
    drawn = set(saved['risks']) | {r.get('mitigation', {}).get('id') for r in rows}
    if set(labels) != drawn:
        bad.append(f'trace_labels.json must label exactly {sorted(drawn, key=str)}')
    bad += [f'label of {i} must have 1-6 words' for i, s in labels.items()
            if not (isinstance(s, str) and 1 <= len(s.split()) <= 6)]
    return bad


def main():
    checks = {}

    def check(name, ok, detail=''):
        checks[name] = {'ok': bool(ok), 'detail': detail if isinstance(detail, str) else json.dumps(detail)[:1500]}

    node = shutil.which('node')
    rows, why = None, 'node is not on PATH'
    if node:
        r = subprocess.run([node, str(SCRIPT)], capture_output=True, text=True, timeout=60, cwd=ROOT)
        try:
            rows, why = json.loads(r.stdout), 'printed'
        except ValueError:
            why = f'trace.mjs failed: {r.stderr[-300:]!r}'
    check('video/scripts/trace.mjs prints the rows', rows is not None, why)
    if rows is not None:
        try:
            data = {'timeline': load(VIDEO / 'src' / 'timeline.json'), 'labels': load(LABELS),
                    'enhancements': load(VIDEO / 'data' / 'model_enhancements.json'),
                    'risks': load(ROOT / 'tools' / 'data' / 'risk_suggestions.json'),
                    'mitigations': load(ROOT / 'tools' / 'data' / 'mitigation_suggestions.json')}
            problems = validate(rows, data)
        except Exception as e:  # noqa: BLE001 - a malformed input is reported as a failure, never a crash
            problems = [f'validator crashed: {e!r}']
        check('every row is a link the curated data holds', not problems, problems or 'sound')
        if not problems:
            wrong = copy.deepcopy(rows)
            others = [k for k in data['timeline']['scenes'][3]['dataRefs']['risks']['saved'] if k != wrong[0]['risk']['id']]
            wrong[0]['risk'] = {'id': others[0], 'label': data['labels'][others[0]]}
            check('validator rejects a row naming another risk', any('the risk must be' in x for x in validate(wrong, data)))
            gdpr = {'sources': [{'title': 'GDPR (Regulation (EU) 2016/679), Article 22', 'url': 'https://eur-lex.europa.eu/eli/reg/2016/679/oj'},
                                {'title': 'EU AI Act (Regulation (EU) 2024/1689), Article 10: Data', 'url': 'https://eur-lex.europa.eu/eli/reg/2024/1689/oj'}]}
            check('the article rule skips a GDPR source', articles(gdpr) == [10], articles(gdpr))

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
