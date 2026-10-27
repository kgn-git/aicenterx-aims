"""Schema test for the risk agent's curated output, tools/data/risk_suggestions.json (issue #14).

Usage:  python test/risk_suggestions_data_test.py

The agent run on the initiative page (#17) replays this data, so every value must be one the prototype knows and every
citation must point at the source it names. Checks:
  - the curated data: 5-8 suggestions for each pilot (rcr, chatbot, hiring) and one AI Index context entry each; harm,
    likelihood, severity, lifecycle stage and trigger drawn from the prototype's own HARMS, LIKELIHOODS, SEVERITIES,
    LIFECYCLE_STAGES and CANVAS_BLOCKS; an MIT domain, subdomain and causal class from the MIT taxonomies; at least one
    incident; matchesRisk null or a RISKS id of the same initiative; every url https on the host its source allows;
    an attribution (name, licence, link) for each of the three sources
  - the guard: one broken copy per rule above, each of which the validator must reject
  - the build: index.html carries RISK_SUGGESTIONS equal to the JSON
The prototype's lists are read from the built index.html source.
Prints a JSON report; exit code 1 on any failure.
"""
import copy
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'tools' / 'data' / 'risk_suggestions.json'
INDEX = ROOT / 'index.html'
PILOTS = ('rcr', 'chatbot', 'hiring')
SOURCES = ('MIT AI Risk Repository', 'AI Incident Database', 'Stanford HAI AI Index')
HOSTS = {'mit': 'airisk.mit.edu', 'incident': 'incidentdatabase.ai', 'context': 'hai.stanford.edu',
         'attribution': {'airisk.mit.edu', 'incidentdatabase.ai', 'hai.stanford.edu'}, 'licence': 'creativecommons.org'}
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
    """The prototype's own value lists, read from the built page's source: they live inside its script's closure,
    so a browser cannot reach them from outside."""
    def arr(name):
        m = re.search(rf'^var {name} = (\[.*?\]);', html, re.M)
        return json.loads(m.group(1)) if m else []
    blocks = re.search(r'^var CANVAS_BLOCKS = \[(.*?)^\];', html, re.M | re.S)
    built = re.search(r'^var RISK_SUGGESTIONS=(.*);$', html, re.M)
    return {'harms': arr('HARMS'), 'likelihoods': arr('LIKELIHOODS'), 'severities': arr('SEVERITIES'), 'stages': arr('LIFECYCLE_STAGES'),
            'triggers': re.findall(r'\{f:"(\w+)"', blocks.group(1)) if blocks else [],
            'risks': re.findall(r'\{id:"(r\d+)",init:"(\w+)"', html),
            'built': json.loads(built.group(1)) if built else None}


def url_ok(u, host):
    p = urlparse(u if isinstance(u, str) else '')
    return p.scheme == 'https' and (p.hostname in host if isinstance(host, set) else p.hostname == host)


def validate(data, proto):
    """Every rule broken by data, as readable strings; empty when the data is sound."""
    bad = []
    if not isinstance(data, dict) or set(data) != {'attribution', 'initiatives'}:
        return ['top level must be exactly {attribution, initiatives}']
    attr = data['attribution']
    if sorted(a.get('source') for a in attr) != sorted(SOURCES):
        bad.append(f'attribution must name each source once: {SOURCES}')
    for a in attr:
        if not a.get('licence') or not url_ok(a.get('url'), HOSTS['attribution']) or not url_ok(a.get('licenceUrl'), HOSTS['licence']):
            bad.append(f'attribution {a.get("source")}: needs licence, an https source url and an https licence url')
    inits = data['initiatives']
    if sorted(inits) != sorted(PILOTS):
        bad.append(f'initiatives must be exactly {PILOTS}')
    risk_init = dict(proto['risks'])
    for init, block in inits.items():
        ctx = block.get('context') or {}
        if not all(ctx.get(k) for k in ('edition', 'chapter', 'statement')) or not url_ok(ctx.get('url'), HOSTS['context']):
            bad.append(f'{init}: AI Index context needs edition, chapter, statement and an https hai.stanford.edu url')
        sugg = block.get('suggestions') or []
        if not 5 <= len(sugg) <= 8:
            bad.append(f'{init}: {len(sugg)} suggestions, want 5-8')
        ids = [s.get('id') for s in sugg]
        if len(set(ids)) != len(ids):
            bad.append(f'{init}: duplicate suggestion ids')
        for s in sugg:
            sid = s.get('id')
            if not re.fullmatch(rf's-{init}-\d+', sid or ''):
                bad.append(f'{init}: id {sid!r} is not s-{init}-<n>')
            if not s.get('description'):
                bad.append(f'{sid}: no description')
            for field, allowed in (('harm', 'harms'), ('likelihood', 'likelihoods'), ('severity', 'severities'),
                                   ('lifecycleStage', 'stages'), ('trigger', 'triggers')):
                if s.get(field) not in proto[allowed]:
                    bad.append(f'{sid}: unknown {field} {s.get(field)!r}')
            mit = s.get('mit') or {}
            if mit.get('domain') not in MIT_DOMAINS:
                bad.append(f'{sid}: unknown MIT domain {mit.get("domain")!r}')
            elif mit.get('subdomain') not in MIT_DOMAINS[mit['domain']]:
                bad.append(f'{sid}: MIT subdomain {mit.get("subdomain")!r} is not in {mit["domain"]}')
            causal = mit.get('causal') or {}
            if any(causal.get(k) not in v for k, v in CAUSAL.items()):
                bad.append(f'{sid}: MIT causal class {causal} outside the causal taxonomy')
            if not url_ok(mit.get('url'), HOSTS['mit']):
                bad.append(f'{sid}: MIT url must be https on airisk.mit.edu')
            incidents = s.get('incidents') or []
            if not incidents:
                bad.append(f'{sid}: no incident')
            for n in incidents:
                if not isinstance(n.get('id'), int) or not n.get('title') or not url_ok(n.get('url'), HOSTS['incident']) \
                        or urlparse(n['url']).path.rstrip('/') != f'/cite/{n.get("id")}':
                    bad.append(f'{sid}: incident {n.get("id")!r} needs an id, a title and its https incidentdatabase.ai/cite/<id> url')
            m = s.get('matchesRisk')
            if m is not None and risk_init.get(m) != init:
                bad.append(f'{sid}: matchesRisk {m!r} is not a register risk of {init}')
    return bad


def broken_copies(data, init, proto):
    """One copy of the data per rule, each breaking only that rule on the first suggestion of init."""
    def edit(fn):
        d = copy.deepcopy(data)
        fn(d['initiatives'][init]['suggestions'][0], d)
        return d

    other = next(p for p in PILOTS if p != init)
    return {
        'unknown harm': edit(lambda s, d: s.update(harm='bad-luck')),
        'unknown likelihood': edit(lambda s, d: s.update(likelihood='often')),
        'unknown severity': edit(lambda s, d: s.update(severity='awful')),
        'unknown lifecycle stage': edit(lambda s, d: s.update(lifecycleStage='Build')),
        'unknown trigger': edit(lambda s, d: s.update(trigger='notACanvasField')),
        'no MIT domain': edit(lambda s, d: s['mit'].pop('domain')),
        'subdomain from another domain': edit(lambda s, d: s['mit'].update(subdomain='6.6 Environmental harm')),
        'no incident': edit(lambda s, d: s.update(incidents=[])),
        'matchesRisk from another initiative': edit(lambda s, d: s.update(matchesRisk=next(r for r, i in proto['risks'] if i == other))),
        'unknown matchesRisk': edit(lambda s, d: s.update(matchesRisk='r99')),
        'http incident url': edit(lambda s, d: s['incidents'][0].update(url=s['incidents'][0]['url'].replace('https:', 'http:'))),
        'incident url on another host': edit(lambda s, d: s['incidents'][0].update(url=f'https://example.com/cite/{s["incidents"][0]["id"]}/')),
        'javascript url': edit(lambda s, d: s['incidents'][0].update(url='javascript:alert(1)')),
        'MIT url on another host': edit(lambda s, d: s['mit'].update(url='https://airisk.mit.edu.example.com/risks')),
        'context url on another host': edit(lambda s, d: d['initiatives'][init]['context'].update(url='https://example.com/ai-index')),
        'malformed id': edit(lambda s, d: s.update(id=f's-{other}-1')),
        'duplicate id': edit(lambda s, d: d['initiatives'][init]['suggestions'][1].update(id=s['id'])),
        'too few suggestions': edit(lambda s, d: d['initiatives'][init].update(suggestions=d['initiatives'][init]['suggestions'][:4])),
        'attribution missing a source': edit(lambda s, d: d.update(attribution=d['attribution'][:2])),
    }



def main():
    checks = {}

    def check(name, ok, detail=''):
        checks[name] = {'ok': bool(ok), 'detail': detail if isinstance(detail, str) else json.dumps(detail)[:1500]}

    proto = prototype(INDEX.read_text(encoding='utf-8'))
    check('index.html carries every value list the data is checked against',
          all(proto[k] for k in ('harms', 'likelihoods', 'severities', 'stages', 'triggers', 'risks')), {k: len(v) for k, v in proto.items() if k != 'built'})

    data = json.loads(DATA.read_text(encoding='utf-8')) if DATA.exists() else None
    check('tools/data/risk_suggestions.json exists and parses', data is not None, str(DATA))
    if data is not None:
        problems = validate(data, proto)
        check('curated data passes every rule', not problems, problems or 'sound')
        if not problems:
            for init in PILOTS:
                missed = [k for k, d in broken_copies(data, init, proto).items() if not validate(d, proto)]
                check(f'validator rejects each broken copy ({init})', not missed, missed or 'all rejected')
        check('index.html carries RISK_SUGGESTIONS equal to the JSON', proto['built'] == data,
              'missing: rebuild with npm run build' if proto['built'] is None else 'differs from the JSON: rebuild')

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
