"""Schema test for the simulated model agent's curated output, tools/data/model_suggestions.json.

Usage:  python test/model_suggestions_data_test.py

The model run replays this data, so its citations must be real: every cited benchmark exists in the benchmarks page with
that primary dimension, every raised or lowered risk can be selected on that initiative, and every source is a record
of that initiative, a titled EUR-Lex link, or marked as written for this prototype. Checks:
  - 2-3 candidates per pilot, each with a name, fit, gaps, and AC3/AC4's citations (chatbot: a G or X and an S or F
    benchmark; hiring: an F benchmark and a gap naming G and X; rcr: a criterion and a gap naming tabular credit models)
  - evidence (an R benchmark or a sourced criterion) for each control behind that initiative's curated mitigations
  - the guard: one broken copy per rule, each rejected for that rule
  - the build: index.html carries MODEL_SUGGESTIONS as exactly the escaped literal of the JSON
Prints a JSON report; exit code 1 on any failure.
"""
import copy
import json
import re
import sys
from pathlib import Path

from mitigation_suggestions_data_test import prototype as risk_side
from source_url import url_ok

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
from inline_json import script_literal  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'tools' / 'data' / 'model_suggestions.json'
INDEX = ROOT / 'index.html'
BENCH = ROOT / 'Periodic Table of AI Benchmarks.html'
PILOTS = ('rcr', 'chatbot', 'hiring')


def prototype():
    """What the data is checked against: benchmark rows by dataset and number, the risks selectable per initiative, the
    controls behind each initiative's mitigations, and the prototype's records."""
    html = INDEX.read_text(encoding='utf-8')
    side = risk_side(html, json.loads((ROOT / 'tools' / 'data' / 'risk_suggestions.json').read_text(encoding='utf-8')))
    bench = json.loads(re.search(r'^const DATA = (\{.*?\});\s*$', BENCH.read_text(encoding='utf-8'), re.M).group(1))
    mitig = json.loads((ROOT / 'tools' / 'data' / 'mitigation_suggestions.json').read_text(encoding='utf-8'))
    controls = {}
    for rid, ms in mitig['risks'].items():
        controls.setdefault(side['selectable'][rid], set()).update(m['controlKey'] for m in ms)
    built = re.search(r'^var MODEL_SUGGESTIONS=(.*);$', html, re.M)
    return {'dims': {k: {r[0]: r[4] for r in rows} for k, rows in bench.items()}, 'selectable': side['selectable'],
            'controls': controls, 'records': side['records'], 'built': built.group(1) if built else None}


def source_bad(s, init, proto):
    if s == {'prototype': True}:
        return False
    if 'record' in s:
        return proto['records'].get(s['record']) != init
    return not (s.get('title') and url_ok(s.get('url'), 'eur-lex.europa.eu'))


def validate(data, proto):
    """Every rule broken by data, as readable strings; empty when the data is sound."""
    bad = []
    inits = data.get('initiatives') or {}
    if sorted(inits) != sorted(PILOTS):
        return [f'initiatives must be exactly {PILOTS}']
    for init, block in inits.items():
        cands = block.get('candidates') or []
        if not 2 <= len(cands) <= 3:
            bad.append(f'{init}: {len(cands)} candidates, want 2-3')
        for c in cands:
            cid = str(c.get('id'))
            if not re.fullmatch(rf'md-{init}-\d+', cid):
                bad.append(f'{init}: id {cid!r} is not md-{init}-<n>')
            if not all(c.get(k) for k in ('name', 'fit', 'gaps')):
                bad.append(f'{cid}: needs name, fit and gaps')
            for b in c.get('benchmarks') or []:
                if proto['dims'].get(b.get('dataset'), {}).get(b.get('no')) != b.get('dim') or not b.get('dim'):
                    bad.append(f'{cid}: benchmark {b} is not a row with that primary dimension')
            for rid in (c.get('raises') or []) + (c.get('lowers') or []):
                if proto['selectable'].get(rid) != init:
                    bad.append(f'{cid}: risk {rid!r} cannot be selected on {init}')
            for cr in c.get('criteria') or []:
                if not cr.get('text') or source_bad(cr.get('source') or {}, init, proto):
                    bad.append(f'{cid}: criterion needs text and a known source')
            dims = {b.get('dim') for b in c.get('benchmarks') or []}
            if init == 'chatbot' and not (dims & {'G', 'X'} and dims & {'S', 'F'}):
                bad.append(f'{cid}: chatbot needs a G or X and an S or F benchmark')
            if init == 'hiring' and ('F' not in dims or 'no G or X benchmark' not in str(c.get('gaps'))):
                bad.append(f'{cid}: hiring needs an F benchmark and a gap naming G and X')
            if init == 'rcr' and (not c.get('criteria') or 'no benchmark for tabular credit models' not in str(c.get('gaps'))):
                bad.append(f'{cid}: rcr needs a criterion and a gap naming tabular credit models')
        ctrl = block.get('controls') or {}
        if sorted(ctrl) != sorted(proto['controls'].get(init, ())):
            bad.append(f'{init}: controls must be exactly those behind its mitigations, {sorted(proto["controls"].get(init, ()))}')
        for key, ev in ctrl.items():
            b, cr = ev.get('benchmark'), ev.get('criterion')
            if b and proto['dims'].get(b.get('dataset'), {}).get(b.get('no')) == 'R' == b.get('dim'):
                continue
            if cr and cr.get('text') and not source_bad(cr.get('source') or {}, init, proto):
                continue
            bad.append(f'{init}: control {key} needs an R benchmark or a sourced criterion')
    return bad


def broken_copies(data):
    """{rule: (copy breaking only that rule, a fragment its rejection must contain)}."""
    def edit(fn):
        d = copy.deepcopy(data)
        fn(d)
        return d

    first = lambda d, i: d['initiatives'][i]['candidates'][0]  # noqa: E731
    return {
        'unknown benchmark': (edit(lambda d: first(d, 'chatbot')['benchmarks'].append({'dataset': 's100', 'no': 999, 'dim': 'G'})), 'is not a row'),
        'wrong dimension': (edit(lambda d: first(d, 'chatbot')['benchmarks'].append({'dataset': 's100', 'no': 31, 'dim': 'G'})), 'is not a row'),
        'risk from another initiative': (edit(lambda d: first(d, 'rcr')['raises'].append('s-chatbot-3')), 'cannot be selected'),
        'matched suggestion': (edit(lambda d: first(d, 'rcr')['lowers'].append('s-rcr-1')), 'cannot be selected'),
        'one candidate': (edit(lambda d: d['initiatives']['rcr'].update(candidates=d['initiatives']['rcr']['candidates'][:1])), 'want 2-3'),
        'chatbot without S or F': (edit(lambda d: first(d, 'chatbot').update(benchmarks=[b for b in first(d, 'chatbot')['benchmarks'] if b['dim'] in 'GX'])), 'chatbot needs'),
        'hiring without its gap': (edit(lambda d: first(d, 'hiring').update(gaps='None.')), 'hiring needs'),
        'rcr without criteria': (edit(lambda d: first(d, 'rcr').update(criteria=[])), 'rcr needs'),
        'foreign record': (edit(lambda d: first(d, 'rcr')['criteria'].append({'text': 'x', 'source': {'record': 'e6'}})), 'known source'),
        'off-host link': (edit(lambda d: first(d, 'rcr')['criteria'].append({'text': 'x', 'source': {'url': 'https://example.com/', 'title': 'x'}})), 'known source'),
        'a control without evidence': (edit(lambda d: d['initiatives']['rcr']['controls'].pop(next(iter(d['initiatives']['rcr']['controls'])))), 'controls must be'),
        'control evidence not R': (edit(lambda d: d['initiatives']['chatbot']['controls'].update({k: {'benchmark': {'dataset': 's100', 'no': 31, 'dim': 'S'}} for k in list(d['initiatives']['chatbot']['controls'])[:1]})), 'needs an R benchmark'),
    }


def main():
    checks = {}

    def check(name, ok, detail=''):
        checks[name] = {'ok': bool(ok), 'detail': detail if isinstance(detail, str) else json.dumps(detail)[:1500]}

    proto = prototype()
    check('the benchmarks page, selectable risks and mitigation controls are readable',
          len(proto['dims'].get('s100', {})) == 100 and len(proto['selectable']) == 18 and all(proto['controls'].get(i) for i in PILOTS))
    try:
        data, why = json.loads(DATA.read_text(encoding='utf-8')), str(DATA)
    except (OSError, ValueError) as e:
        data, why = None, repr(e)
    check('tools/data/model_suggestions.json exists and parses', data is not None, why)
    if data is not None:
        try:
            problems = validate(data, proto)
        except Exception as e:  # noqa: BLE001 - a malformed shape is reported as a failure, never a crash
            problems = [f'validator crashed: {e!r}']
        check('curated data passes every rule', not problems, problems or 'sound')
        if not problems:
            missed = [rule for rule, (d, why) in broken_copies(data).items() if not any(why in p for p in validate(d, proto))]
            check('validator rejects each broken copy for its own rule', not missed, missed or 'all rejected')
        check('index.html carries MODEL_SUGGESTIONS as the escaped literal of the JSON', proto['built'] == script_literal(data),
              'missing: rebuild with npm run build' if proto['built'] is None else 'differs from script_literal(JSON): rebuild')
    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
