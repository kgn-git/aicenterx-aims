"""Schema test for the risk agent's curated output, tools/data/risk_suggestions.json.

Usage:  python test/risk_suggestions_data_test.py

The agent run on the initiative page replays this data, so every value must be one the prototype knows and every
citation must point at the source it names. Checks:
  - the curated data: 5-8 suggestions for each pilot (rcr, chatbot, hiring) and one AI Index context entry each; harm,
    likelihood, severity, lifecycle stage and trigger drawn from the prototype's own HARMS, LIKELIHOODS, SEVERITIES,
    LIFECYCLE_STAGES and CANVAS_BLOCKS; a description, and a why whose quotes are the initiative's own AI Canvas text;
    an MIT domain, subdomain and causal class from the MIT taxonomies; at least one incident, each id with one title
    and its /cite/<id>/ url; matchesRisk null or a RISKS id of the same initiative; every url plain https on the host
    its source allows; an attribution (key, name, licence, licence link, source link, citation, changes) per source
  - the guard: one broken copy per rule above, each rejected by the validator for that rule
  - the build: index.html carries RISK_SUGGESTIONS as exactly the escaped literal of the JSON (test/inline_json_test.py
    holds the escaping rule)
The prototype's lists and canvases are read from the built index.html source.
Prints a JSON report; exit code 1 on any failure.
"""
import copy
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
from inline_json import script_literal  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'tools' / 'data' / 'risk_suggestions.json'
INDEX = ROOT / 'index.html'
PILOTS = ('rcr', 'chatbot', 'hiring')
SOURCES = {'mit': ('MIT AI Risk Repository', 'airisk.mit.edu'), 'aiid': ('AI Incident Database', 'incidentdatabase.ai'),
           'aiindex': ('Stanford HAI AI Index', 'hai.stanford.edu')}
HOST = {k: h for k, (_, h) in SOURCES.items()}
LICENCE_HOST = 'creativecommons.org'
MIT_DOMAINS = {
    '1. Discrimination & Toxicity': ['1.1 Unfair discrimination and misrepresentation', '1.2 Exposure to toxic content',
                                     '1.3 Unequal performance across groups'],
    '2. Privacy & Security': ['2.1 Compromise of privacy by obtaining, leaking or correctly inferring sensitive information',
                              '2.2 AI system security vulnerabilities and attacks'],
    '3. Misinformation': ['3.1 False or misleading information', '3.2 Pollution of information ecosystem and loss of consensus reality'],
    '4. Malicious Actors': ['4.1 Disinformation, surveillance, and influence at scale',
                            '4.2 Cyberattacks, weapons development or use and mass harm', '4.3 Fraud, scams, and targeted manipulation'],
    '5. Human-Computer Interaction': ['5.1 Overreliance and unsafe use', '5.2 Loss of human agency and autonomy'],
    '6. Socioeconomic & Environmental': ['6.1 Power centralization and unfair distribution of benefits',
                                         '6.2 Increased inequality and decline in employment quality',
                                         '6.3 Economic and cultural devaluation of human effort', '6.4 Competitive dynamics',
                                         '6.5 Governance failure', '6.6 Environmental harm'],
    '7. AI System Safety, Failures, & Limitations': ['7.1 AI pursuing its own goals in conflict with human goals or values',
                                                     '7.2 AI possessing dangerous capabilities', '7.3 Lack of capability or robustness',
                                                     '7.4 Lack of transparency or interpretability', '7.5 AI welfare and rights',
                                                     '7.6 Multi-agent risks'],
}
CAUSAL = {'entity': {'Human', 'AI', 'Other'}, 'intent': {'Intentional', 'Unintentional', 'Other'},
          'timing': {'Pre-deployment', 'Post-deployment', 'Other'}}


def prototype(html):
    """The prototype's own value lists and canvases, read from the built page's source: they live inside its script's
    closure, so a browser cannot reach them from outside."""
    def arr(name):
        m = re.search(rf'^var {name} = (\[.*?\]);', html, re.M)
        return json.loads(m.group(1)) if m else []

    def canvas(init):
        m = re.search(rf'^\s*{init}:\{{init:"{init}",(businessProblem:.*?")\}}', html, re.M | re.S)
        return ' '.join(json.loads(f'"{v}"') for v in re.findall(r'\w+:"((?:[^"\\]|\\.)*)"', m.group(1))) if m else ''

    blocks = re.search(r'^var CANVAS_BLOCKS = \[(.*?)^\];', html, re.M | re.S)
    built = re.search(r'^var RISK_SUGGESTIONS=(.*);$', html, re.M)
    return {'harms': arr('HARMS'), 'likelihoods': arr('LIKELIHOODS'), 'severities': arr('SEVERITIES'), 'stages': arr('LIFECYCLE_STAGES'),
            'triggers': re.findall(r'\{f:"(\w+)"', blocks.group(1)) if blocks else [],
            'risks': re.findall(r'\{id:"(r\d+)",init:"(\w+)"', html),
            'canvases': {i: canvas(i) for i in PILOTS},
            'built': built.group(1) if built else None}


def url_ok(u, host):
    """A plain https url on exactly this host. A fixed prefix, not a parsed hostname: parsers and browsers read
    userinfo, ports and backslashes differently, so a parsed check can pass a url that a browser sends elsewhere."""
    return isinstance(u, str) and re.fullmatch(rf'https://{re.escape(host)}(?:[/?#]\S*)?', u) is not None


def quotes(text):
    """The canvas fragments a why quotes: each "..." passage, split at its ellipses."""
    return [p.strip(' .,;:') for q in re.findall(r'"([^"]+)"', text or '') for p in q.split('…') if p.strip(' .,;:')]


def validate(data, proto):
    """Every rule broken by data, as readable strings; empty when the data is sound."""
    if not isinstance(data, dict) or set(data) != {'attribution', 'initiatives'}:
        return ['top level must be exactly {attribution, initiatives}']
    bad = []
    attr = data['attribution'] if isinstance(data['attribution'], list) else []
    if sorted(str(a.get('key')) for a in attr) != sorted(SOURCES):
        bad.append(f'attribution must hold each source key once: {sorted(SOURCES)}')
    for a in attr:
        name, host = SOURCES.get(a.get('key'), (None, None))
        if a.get('source') != name or not url_ok(a.get('url'), host or ''):
            bad.append(f'attribution {a.get("key")!r}: source name and an https url on its own host')
        if not url_ok(a.get('licenceUrl'), LICENCE_HOST) or not all(a.get(k) for k in ('licence', 'citation', 'changes')):
            bad.append(f'attribution {a.get("key")!r}: needs licence, an https licence url, citation and changes')
    inits = data['initiatives'] if isinstance(data['initiatives'], dict) else {}
    if sorted(inits) != sorted(PILOTS):
        bad.append(f'initiatives must be exactly {PILOTS}')
    risk_init = dict(proto['risks'])
    titles = {}
    for init, block in inits.items():
        ctx = block.get('context') or {}
        if not all(ctx.get(k) for k in ('edition', 'chapter', 'statement')) or not url_ok(ctx.get('url'), HOST['aiindex']):
            bad.append(f'{init}: AI Index context needs edition, chapter, statement and an https hai.stanford.edu url')
        sugg = block.get('suggestions') or []
        if not 5 <= len(sugg) <= 8:
            bad.append(f'{init}: {len(sugg)} suggestions, want 5-8')
        ids = [str(s.get('id')) for s in sugg]
        if len(set(ids)) != len(ids):
            bad.append(f'{init}: duplicate suggestion ids')
        for s in sugg:
            sid = str(s.get('id'))
            if not re.fullmatch(rf's-{init}-\d+', sid):
                bad.append(f'{init}: id {sid!r} is not s-{init}-<n>')
            if not s.get('description'):
                bad.append(f'{sid}: no description')
            found = quotes(s.get('why'))
            if not found:
                bad.append(f'{sid}: why quotes no canvas text')
            for q in found:
                if q.lower() not in proto['canvases'].get(init, '').lower():
                    bad.append(f'{sid}: why quotes "{q}", which is not in the {init} canvas')
            for field, allowed in (('harm', 'harms'), ('likelihood', 'likelihoods'), ('severity', 'severities'),
                                   ('lifecycleStage', 'stages'), ('trigger', 'triggers')):
                if s.get(field) not in proto[allowed]:
                    bad.append(f'{sid}: unknown {field} {s.get(field)!r}')
            mit = s.get('mit') or {}
            if str(mit.get('domain')) not in MIT_DOMAINS:
                bad.append(f'{sid}: unknown MIT domain {mit.get("domain")!r}')
            elif mit.get('subdomain') not in MIT_DOMAINS[mit['domain']]:
                bad.append(f'{sid}: MIT subdomain {mit.get("subdomain")!r} is not in {mit["domain"]}')
            causal = mit.get('causal') or {}
            if any(str(causal.get(k)) not in v for k, v in CAUSAL.items()):
                bad.append(f'{sid}: MIT causal class {causal} outside the causal taxonomy')
            if not url_ok(mit.get('url'), HOST['mit']):
                bad.append(f'{sid}: MIT url must be plain https on airisk.mit.edu')
            incidents = s.get('incidents') or []
            if not incidents:
                bad.append(f'{sid}: no incident')
            for n in incidents:
                i = n.get('id')
                if not isinstance(i, int) or not n.get('title') or n.get('url') != f'https://incidentdatabase.ai/cite/{i}/':
                    bad.append(f'{sid}: incident {i!r} needs an id, a title and its https://incidentdatabase.ai/cite/<id>/ url')
                elif titles.setdefault(i, n['title']) != n['title']:
                    bad.append(f'{sid}: incident {i} carries a different title from its other citations')
            m = s.get('matchesRisk')
            if m is not None and risk_init.get(str(m)) != init:
                bad.append(f'{sid}: matchesRisk {m!r} is not a register risk of {init}')
    return bad


def broken_copies(data, init, proto):
    """{rule: (copy breaking only that rule on init's first suggestion, a fragment its rejection must contain)}."""
    def edit(fn):
        d = copy.deepcopy(data)
        fn(d['initiatives'][init]['suggestions'][0], d)
        return d

    other = next(p for p in PILOTS if p != init)
    first_incident = lambda s: s['incidents'][0]  # noqa: E731
    pad = lambda d: d['initiatives'][init]['suggestions'].extend(  # noqa: E731
        dict(copy.deepcopy(d['initiatives'][init]['suggestions'][0]), id=f's-{init}-{100 + k}')
        for k in range(9 - len(d['initiatives'][init]['suggestions'])))
    return {
        'unknown harm': (edit(lambda s, d: s.update(harm='bad-luck')), 'unknown harm'),
        'unknown likelihood': (edit(lambda s, d: s.update(likelihood='often')), 'unknown likelihood'),
        'unknown severity': (edit(lambda s, d: s.update(severity='awful')), 'unknown severity'),
        'unknown lifecycle stage': (edit(lambda s, d: s.update(lifecycleStage='Build')), 'unknown lifecycleStage'),
        'unknown trigger': (edit(lambda s, d: s.update(trigger='notACanvasField')), 'unknown trigger'),
        'no description': (edit(lambda s, d: s.update(description='')), 'no description'),
        'why quotes nothing': (edit(lambda s, d: s.update(why='It seems risky.')), 'why quotes no canvas text'),
        'why misquotes the canvas': (edit(lambda s, d: s.update(why='"the model is always right"')), 'not in the'),
        'why quotes another canvas': (edit(lambda s, d: s.update(why=f'"{proto["canvases"][other][:40]}"')), 'not in the'),
        'no MIT domain': (edit(lambda s, d: s['mit'].pop('domain')), 'unknown MIT domain'),
        'subdomain from another domain': (edit(lambda s, d: s['mit'].update(subdomain='6.6 Environmental harm')), 'MIT subdomain'),
        'unknown causal entity': (edit(lambda s, d: s['mit']['causal'].update(entity='Robot')), 'causal taxonomy'),
        'http MIT url': (edit(lambda s, d: s['mit'].update(url='http://airisk.mit.edu/risks')), 'MIT url'),
        'MIT url on another host': (edit(lambda s, d: s['mit'].update(url='https://airisk.mit.edu.example.com/risks')), 'MIT url'),
        'backslash userinfo MIT url': (edit(lambda s, d: s['mit'].update(url='https://evil.example\\@airisk.mit.edu/risks')), 'MIT url'),
        'userinfo MIT url': (edit(lambda s, d: s['mit'].update(url='https://user@airisk.mit.edu/risks')), 'MIT url'),
        'MIT url with a port': (edit(lambda s, d: s['mit'].update(url='https://airisk.mit.edu:8443/risks')), 'MIT url'),
        'no incident': (edit(lambda s, d: s.update(incidents=[])), 'no incident'),
        'http incident url': (edit(lambda s, d: first_incident(s).update(url=first_incident(s)['url'].replace('https:', 'http:'))), 'cite/<id>'),
        'incident url on another host': (edit(lambda s, d: first_incident(s).update(url=f'https://example.com/cite/{first_incident(s)["id"]}/')), 'cite/<id>'),
        'incident url for another id': (edit(lambda s, d: first_incident(s).update(url=f'https://incidentdatabase.ai/cite/{first_incident(s)["id"] + 1}/')), 'cite/<id>'),
        'javascript incident url': (edit(lambda s, d: first_incident(s).update(url='javascript:alert(1)')), 'cite/<id>'),
        'incident id as text': (edit(lambda s, d: first_incident(s).update(id=str(first_incident(s)['id']))), 'cite/<id>'),
        'incident with no title': (edit(lambda s, d: first_incident(s).update(title='')), 'cite/<id>'),
        'one incident, two titles': (edit(lambda s, d: d['initiatives'][init]['suggestions'][1]['incidents'].append(
            dict(first_incident(s), title=first_incident(s)['title'] + ' (edited)'))), 'different title'),
        'matchesRisk from another initiative': (edit(lambda s, d: s.update(matchesRisk=next(r for r, i in proto['risks'] if i == other))), 'not a register risk'),
        'unknown matchesRisk': (edit(lambda s, d: s.update(matchesRisk='r99')), 'not a register risk'),
        'malformed id': (edit(lambda s, d: s.update(id=f's-{other}-1')), 'is not s-'),
        'duplicate id': (edit(lambda s, d: d['initiatives'][init]['suggestions'][1].update(id=s['id'])), 'duplicate'),
        'too few suggestions': (edit(lambda s, d: d['initiatives'][init].update(suggestions=d['initiatives'][init]['suggestions'][:4])), 'want 5-8'),
        'too many suggestions': (edit(lambda s, d: pad(d)), 'want 5-8'),
        'context with no edition': (edit(lambda s, d: d['initiatives'][init]['context'].update(edition='')), 'AI Index context'),
        'context with no chapter': (edit(lambda s, d: d['initiatives'][init]['context'].update(chapter='')), 'AI Index context'),
        'context with no statement': (edit(lambda s, d: d['initiatives'][init]['context'].update(statement='')), 'AI Index context'),
        'http context url': (edit(lambda s, d: d['initiatives'][init]['context'].update(url='http://hai.stanford.edu/ai-index')), 'AI Index context'),
        'context url on another host': (edit(lambda s, d: d['initiatives'][init]['context'].update(url='https://example.com/ai-index')), 'AI Index context'),
        'attribution missing a source': (edit(lambda s, d: d.update(attribution=d['attribution'][:2])), 'each source key once'),
        'attribution with no licence': (edit(lambda s, d: d['attribution'][0].update(licence='')), 'citation and changes'),
        'attribution under another name': (edit(lambda s, d: d['attribution'][0].update(source='Wrong name')), 'its own host'),
        'attribution without changes': (edit(lambda s, d: d['attribution'][0].pop('changes')), 'citation and changes'),
        'attribution without citation': (edit(lambda s, d: d['attribution'][0].update(citation='')), 'citation and changes'),
        'licence link on another host': (edit(lambda s, d: d['attribution'][0].update(licenceUrl='https://example.com/by/4.0/')), 'citation and changes'),
        'attribution linking another source': (edit(lambda s, d: d['attribution'][0].update(url='https://hai.stanford.edu/')), 'its own host'),
    }


def main():
    checks = {}

    def check(name, ok, detail=''):
        checks[name] = {'ok': bool(ok), 'detail': detail if isinstance(detail, str) else json.dumps(detail)[:1500]}

    proto = prototype(INDEX.read_text(encoding='utf-8'))
    check('index.html carries every value list and pilot canvas the data is checked against',
          all(proto[k] for k in ('harms', 'likelihoods', 'severities', 'stages', 'triggers', 'risks')) and all(proto['canvases'].values()),
          {k: len(v) for k, v in proto.items() if k != 'built'})

    try:
        data, why = json.loads(DATA.read_text(encoding='utf-8')), str(DATA)
    except (OSError, ValueError) as e:
        data, why = None, repr(e)
    check('tools/data/risk_suggestions.json exists and parses', data is not None, why)
    if data is not None:
        try:
            problems = validate(data, proto)
        except Exception as e:  # noqa: BLE001 - a malformed shape is reported as a failure, never a crash
            problems = [f'validator crashed: {e!r}']
        check('curated data passes every rule', not problems, problems or 'sound')
        if not problems:
            for init in PILOTS:
                missed = [rule for rule, (d, why) in broken_copies(data, init, proto).items()
                          if not any(why in p for p in validate(d, proto))]
                check(f'validator rejects each broken copy for its own rule ({init})', not missed, missed or 'all rejected')
        check('index.html carries RISK_SUGGESTIONS as the escaped literal of the JSON', proto['built'] == script_literal(data),
              'missing: rebuild with npm run build' if proto['built'] is None else 'differs from script_literal(JSON): rebuild')

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
