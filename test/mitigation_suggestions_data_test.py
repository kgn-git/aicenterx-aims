"""Schema test for the mitigation agent's curated output, tools/data/mitigation_suggestions.json.

Usage:  python test/mitigation_suggestions_data_test.py

The mitigation run replays this data for the risks a user selects, so every selectable risk must have its mitigations
and every value must be one the prototype knows. Checks:
  - the curated data: 1-2 mitigations for each selectable risk of the pilots (each register risk, and each risk
    suggestion that matches no register risk) and for nothing else; each with an id m-<risk>-<n>, a description, a
    TREATMENT_STRATEGIES strategy, a CONTROLS key whose closure is not not-applicable, a rationale, a LIFECYCLE_STAGES
    stage, a subcategory of MIT's draft AI Risk Mitigation Taxonomy, and at least one source; a source is either a
    DECISIONS or EVIDENCE id of the risk's own initiative, or a titled url on an allowed host; at least one mitigation
    sits on an implemented control; an attribution (key, name, licence, licence link, source link, citation, changes)
    per external source
  - the guard: one broken copy per rule above, each rejected by the validator for that rule; a not-applicable control
    is shown by tampering with the prototype's controls, because no control is not-applicable today
  - the build: index.html carries MITIGATION_SUGGESTIONS as exactly the escaped literal of the JSON
The prototype's lists are read from the built index.html source; test/source_url.py holds the link rule.
Prints a JSON report; exit code 1 on any failure.
"""
import copy
import json
import re
import sys
from pathlib import Path

from source_url import url_ok

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
from inline_json import script_literal  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'tools' / 'data' / 'mitigation_suggestions.json'
RISK_DATA = ROOT / 'tools' / 'data' / 'risk_suggestions.json'
INDEX = ROOT / 'index.html'
PILOTS = ('rcr', 'chatbot', 'hiring')
HOSTS = ('airisk.mit.edu', 'incidentdatabase.ai', 'eur-lex.europa.eu')
SOURCES = {'mit': ('MIT AI Risk Mitigation Taxonomy (draft)', 'airisk.mit.edu', 'creativecommons.org'),
           'eurlex': ('EUR-Lex', 'eur-lex.europa.eu', 'eur-lex.europa.eu')}
# The draft taxonomy's 23 subcategories, as published at https://airisk.mit.edu/ai-risk-mitigations (28 July 2025).
MIT_MITIGATIONS = [
    '1.1 Board Structure & Oversight', '1.2 Risk Management', '1.3 Conflict of Interest Protections',
    '1.4 Whistleblower Reporting & Protection', '1.5 Safety Decision Frameworks', '1.6 Environmental Impact Management',
    '1.7 Societal Impact Assessment', '2.1 Model & Infrastructure Security', '2.2 Model Alignment',
    '2.3 Model Safety Engineering', '2.4 Content Safety Controls', '3.1 Testing & Auditing', '3.2 Data Governance',
    '3.3 Access Management', '3.4 Staged Deployment', '3.5 Post-deployment Monitoring', '3.6 Incident Response & Recovery',
    '4.1 System Documentation', '4.2 Risk Disclosure', '4.3 Incident Reporting', '4.4 Governance Disclosure',
    '4.5 Third-Party System Access', '4.6 User Rights & Recourse']


def prototype(html, risk_data):
    """The prototype's own lists, read from the built page's source, and the risks a user can select on each pilot."""
    def arr(name):
        m = re.search(rf'^var {name} = (\[.*?\]);', html, re.M)
        return json.loads(m.group(1)) if m else []

    risks = dict(re.findall(r'\{id:"(r\d+)",init:"(\w+)"', html))
    selectable = {r: i for r, i in risks.items() if i in PILOTS}
    for init in PILOTS:
        for s in risk_data['initiatives'][init]['suggestions']:
            if not s['matchesRisk']:
                selectable[s['id']] = init
    records = dict(re.findall(r'\{id:"(e\d+)",init:"(\w+)"', html))
    records.update(re.findall(r'\{id:"(d\d+)",kind:"[\w-]+",subject:"[^"]*",init:"(\w+)"', html))
    built = re.search(r'^var MITIGATION_SUGGESTIONS=(.*);$', html, re.M)
    return {'strategies': arr('TREATMENT_STRATEGIES'), 'stages': arr('LIFECYCLE_STAGES'),
            'controls': dict(re.findall(r'\{key:"(A\.\d+)",objective:"[^"]*",closure:"([\w-]+)"', html)),
            'selectable': selectable, 'records': records, 'built': built.group(1) if built else None}


def validate(data, proto):
    """Every rule broken by data, as readable strings; empty when the data is sound."""
    if not isinstance(data, dict) or set(data) != {'attribution', 'risks'}:
        return ['top level must be exactly {attribution, risks}']
    bad = []
    attr = data['attribution'] if isinstance(data['attribution'], list) else []
    if sorted(str(a.get('key')) for a in attr) != sorted(SOURCES):
        bad.append(f'attribution must hold each source key once: {sorted(SOURCES)}')
    for a in attr:
        name, host, licence_host = SOURCES.get(a.get('key'), (None, '', ''))
        if a.get('source') != name or not url_ok(a.get('url'), host):
            bad.append(f'attribution {a.get("key")!r}: source name and an https url on its own host')
        if not url_ok(a.get('licenceUrl'), licence_host) or not all(a.get(k) for k in ('licence', 'citation', 'changes')):
            bad.append(f'attribution {a.get("key")!r}: needs licence, an https licence url, citation and changes')
    risks = data['risks'] if isinstance(data['risks'], dict) else {}
    if sorted(risks) != sorted(proto['selectable']):
        bad.append(f'risks must be exactly the selectable risks: missing {sorted(set(proto["selectable"]) - set(risks))}, '
                   f'extra {sorted(set(risks) - set(proto["selectable"]))}')
    implemented = False
    for rid, mits in risks.items():
        init = proto['selectable'].get(rid)
        mits = mits if isinstance(mits, list) else []
        if not 1 <= len(mits) <= 2:
            bad.append(f'{rid}: {len(mits)} mitigations, want 1-2')
        ids = [str(m.get('id')) for m in mits]
        if len(set(ids)) != len(ids):
            bad.append(f'{rid}: duplicate mitigation ids')
        for m in mits:
            mid = str(m.get('id'))
            if not re.fullmatch(rf'm-{re.escape(rid)}-\d+', mid):
                bad.append(f'{rid}: id {mid!r} is not m-{rid}-<n>')
            for field in ('description', 'why'):
                if not m.get(field):
                    bad.append(f'{mid}: no {field}')
            if m.get('strategy') not in proto['strategies']:
                bad.append(f'{mid}: unknown strategy {m.get("strategy")!r}')
            if m.get('lifecycleStage') not in proto['stages']:
                bad.append(f'{mid}: unknown lifecycleStage {m.get("lifecycleStage")!r}')
            closure = proto['controls'].get(m.get('controlKey'))
            if closure is None:
                bad.append(f'{mid}: unknown controlKey {m.get("controlKey")!r}')
            elif closure == 'not-applicable':
                bad.append(f'{mid}: control {m.get("controlKey")} is not-applicable')
            implemented = implemented or closure == 'implemented'
            if m.get('mit') not in MIT_MITIGATIONS:
                bad.append(f'{mid}: {m.get("mit")!r} is not an MIT mitigation subcategory')
            sources = m.get('sources') if isinstance(m.get('sources'), list) else []
            if not sources:
                bad.append(f'{mid}: no source')
            for s in sources:
                if 'record' in s:
                    if proto['records'].get(s['record']) != init:
                        bad.append(f'{mid}: record {s["record"]!r} is not a decision or evidence of {init}')
                elif not (s.get('title') and any(url_ok(s.get('url'), h) for h in HOSTS)):
                    bad.append(f'{mid}: source {s.get("url")!r} needs a title and an https url on an allowed host')
    if risks and not implemented:
        bad.append('no mitigation sits on an implemented control')
    return bad


def broken_copies(data, proto):
    """{rule: (data, prototype) breaking only that rule, and a fragment its rejection must contain}."""
    rid = next(r for r in data['risks'] if r.startswith('r'))
    other = next(r for r, i in proto['selectable'].items() if i != proto['selectable'][rid])
    foreign = next(k for k, i in proto['records'].items() if i != proto['selectable'][rid])

    def edit(fn):
        d = copy.deepcopy(data)
        fn(d['risks'][rid][0], d)
        return d, proto

    def control_na():
        p = copy.deepcopy(proto)
        p['controls'][data['risks'][rid][0]['controlKey']] = 'not-applicable'
        return copy.deepcopy(data), p

    return {
        'unknown strategy': (edit(lambda m, d: m.update(strategy='reduce')), 'unknown strategy'),
        'unknown control': (edit(lambda m, d: m.update(controlKey='A.99')), 'unknown controlKey'),
        'unknown stage': (edit(lambda m, d: m.update(lifecycleStage='Someday')), 'unknown lifecycleStage'),
        'not-applicable control': (control_na(), 'is not-applicable'),
        'no rationale': (edit(lambda m, d: m.pop('why')), 'no why'),
        'no description': (edit(lambda m, d: m.update(description='')), 'no description'),
        'unknown MIT subcategory': (edit(lambda m, d: m.update(mit='9.9 Wishful Thinking')), 'MIT mitigation'),
        'no source': (edit(lambda m, d: m.update(sources=[])), 'no source'),
        'record of another initiative': (edit(lambda m, d: m['sources'].append({'record': foreign})), 'is not a decision'),
        'unknown record': (edit(lambda m, d: m['sources'].append({'record': 'd99'})), 'is not a decision'),
        'url off the allowed hosts': (edit(lambda m, d: m['sources'].append({'url': 'https://example.com/x', 'title': 'x'})), 'allowed host'),
        'url without a title': (edit(lambda m, d: m['sources'].append({'url': 'https://eur-lex.europa.eu/x'})), 'allowed host'),
        'malformed id': (edit(lambda m, d: m.update(id=f'm-{other}-1')), 'is not m-'),
        'duplicate id': (edit(lambda m, d: d['risks'][rid].append(copy.deepcopy(m))), 'duplicate'),
        'no mitigations': (edit(lambda m, d: d['risks'].update({rid: []})), 'want 1-2'),
        'three mitigations': (edit(lambda m, d: d['risks'].update({rid: [dict(copy.deepcopy(m), id=f'm-{rid}-{k}') for k in (7, 8, 9)]})), 'want 1-2'),
        'a selectable risk missing': (edit(lambda m, d: d['risks'].pop(other)), 'missing'),
        'a risk that is not selectable': (edit(lambda m, d: d['risks'].update({'r99': d['risks'][rid]})), 'extra'),
        'nothing on an implemented control': (edit(lambda m, d: [x.update(controlKey='A.6') for ms in d['risks'].values() for x in ms]),
                                              'implemented control'),
        'attribution missing a source': (edit(lambda m, d: d.update(attribution=d['attribution'][:1])), 'each source key once'),
        'attribution without changes': (edit(lambda m, d: d['attribution'][0].pop('changes')), 'citation and changes'),
        'licence link on another host': (edit(lambda m, d: d['attribution'][0].update(licenceUrl='https://example.com/l')), 'citation and changes'),
        'attribution under another name': (edit(lambda m, d: d['attribution'][0].update(source='Wrong')), 'its own host'),
    }


def main():
    checks = {}

    def check(name, ok, detail=''):
        checks[name] = {'ok': bool(ok), 'detail': detail if isinstance(detail, str) else json.dumps(detail)[:1500]}

    proto = prototype(INDEX.read_text(encoding='utf-8'), json.loads(RISK_DATA.read_text(encoding='utf-8')))
    check('index.html carries the lists, controls and records the data is checked against',
          proto['strategies'] and proto['stages'] and len(proto['controls']) >= 9 and len(proto['selectable']) == 18
          and proto['records'], {k: len(v) for k, v in proto.items() if k != 'built' and v})
    try:
        data, why = json.loads(DATA.read_text(encoding='utf-8')), str(DATA)
    except (OSError, ValueError) as e:
        data, why = None, repr(e)
    check('tools/data/mitigation_suggestions.json exists and parses', data is not None, why)
    if data is not None:
        try:
            problems = validate(data, proto)
        except Exception as e:  # noqa: BLE001 - a malformed shape is reported as a failure, never a crash
            problems = [f'validator crashed: {e!r}']
        check('curated data passes every rule', not problems, problems or 'sound')
        if not problems:
            missed = [rule for rule, ((d, p), why) in broken_copies(data, proto).items()
                      if not any(why in x for x in validate(d, p))]
            check('validator rejects each broken copy for its own rule', not missed, missed or 'all rejected')
        check('index.html carries MITIGATION_SUGGESTIONS as the escaped literal of the JSON', proto['built'] == script_literal(data),
              'missing: rebuild with npm run build' if proto['built'] is None else 'differs from script_literal(JSON): rebuild')

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
