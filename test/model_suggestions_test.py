"""Behaviour test for the simulated model run on the initiative page.

Usage:  python test/model_suggestions_test.py

The page is checked through its "Suggest models" button, the third part of the risk result: the run and its candidates
for each pilot, benchmark links into the benchmarks page, the gaps and criteria the pilots need, raised and lowered
risks that follow the selection, evidence for the controls behind the mitigations shown, the nothing-selected state,
leaving and reload, the copy, and tampered data rendered as text. The deep link itself is pinned in
test/benchmarks_deep_link_test.py, agentRun's rules in test/risk_suggestions_test.py, and the data's in
test/model_suggestions_data_test.py.
Prints a JSON report; exit code 1 on any failure.
"""
import copy
import json
import re
import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
from inline_json import script_literal  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / 'index.html'
URL = INDEX.as_uri()
HTML = INDEX.read_text(encoding='utf-8')
DATA = json.loads((ROOT / 'tools' / 'data' / 'model_suggestions.json').read_text(encoding='utf-8'))
MITIG = json.loads((ROOT / 'tools' / 'data' / 'mitigation_suggestions.json').read_text(encoding='utf-8'))
REGISTER = dict(re.findall(r'\{id:"(r\d+)",init:"\w+",description:"([^"]+)"', HTML))
STEPS = ['Read the AI Canvas objective', 'Read the selected risks', 'Match benchmark dimensions',
         'Check the controls behind the mitigations', 'Draft model candidates']
PAGE = 'Periodic%20Table%20of%20AI%20Benchmarks.html'
NOTHING = 'You have not selected any risks yet. Select risks in the risk suggestions to get model suggestions. This blocks nothing.'

RECORD = """sel => { window.__log = []; const seen = new Set();
  new MutationObserver(() => document.querySelectorAll('[data-step][data-state="done"]').forEach(el => {
    const k = el.textContent.trim(); if (!seen.has(k)) { seen.add(k); window.__log.push(k); } }))
  .observe(document.body, {subtree: true, childList: true, attributes: true, attributeFilter: ['data-state']});
  document.querySelector(sel).click(); }"""


def main():
    tmp = Path(tempfile.mkdtemp(prefix='model-suggestions-'))
    try:
        return run(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run(tmp):
    checks = {}
    errors = []

    def check(name, ok, detail=''):
        checks[name] = {'ok': bool(ok), 'detail': detail if isinstance(detail, str) else json.dumps(detail)[:1500]}

    @contextmanager
    def section(name):
        try:
            yield
        except Exception as e:  # noqa: BLE001 - a timeout or missing element fails its section, never the whole report
            check(f'{name}: ran to the end', False, str(e)[:300])

    def open_page(b, route, url=URL):
        pg = b.new_context(viewport={'width': 1280, 'height': 900}).new_page()
        pg.on('console', lambda m: m.type == 'error' and errors.append(m.text))
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.goto(url + route)
        pg.wait_for_selector('#page')
        return pg

    def skip(pg, button, host_sel, head):
        pg.click(button)
        pg.click(f'{host_sel} [data-run-skip]')
        pg.wait_for_selector(head, timeout=1000)

    def risks(pg, init, *rids):
        skip(pg, f'[data-suggest-risks="{init}"]', f'#sugg-risks-{init}', f'#sugg-risks-head-{init}')
        for r in rids:
            pg.check(f'#sugg-risks-{init} [data-pick-risk="{r}"]')

    def models(pg, init):
        skip(pg, f'[data-suggest-models="{init}"]', host(init), f'#sugg-model-head-{init}')

    def host(init):
        return f'#sugg-model-{init}'

    def cand(init, cid):
        return f'{host(init)} [data-model="{cid}"]'

    with sync_playwright() as p:
        b = p.chromium.launch()

        with section('AC1'):
            for init, rid in (('rcr', 'r2'), ('chatbot', 'r5'), ('hiring', 'r1')):
                pg = open_page(b, f'#/initiative/{init}')
                risks(pg, init, rid)
                order = pg.evaluate("""i => [...document.querySelectorAll('[data-suggest-mitigations="' + i + '"], [data-suggest-models="' + i + '"]')]
                                      .map(e => e.hasAttribute('data-suggest-models') ? 'models' : 'mitigations')""", init)
                check(f'{init}: "Suggest models" sits in the risk result after the mitigations', order == ['mitigations', 'models'], order)
                if init == 'rcr':
                    pg.evaluate(RECORD, '[data-suggest-models="rcr"]')
                    pg.wait_for_selector('#sugg-model-head-rcr', timeout=4000)
                    log = pg.evaluate('window.__log')
                    check('rcr: the five model steps run in order before the result', [next((s for s in STEPS if s in o), o) for o in log] == STEPS, log)
                else:
                    models(pg, init)
                want = [c['id'] for c in DATA['initiatives'][init]['candidates']]
                got = pg.locator(f'{host(init)} [data-model]').evaluate_all('es => es.map(e => e.getAttribute("data-model"))')
                check(f'{init}: the result shows its {len(want)} candidates', got == want, got)

        with section('AC2, AC3, AC8'):
            pg = open_page(b, '#/initiative/chatbot')
            risks(pg, 'chatbot', 'r5')
            models(pg, 'chatbot')
            c = DATA['initiatives']['chatbot']['candidates'][0]
            links = pg.locator(f'{cand("chatbot", c["id"])} a[href^="{PAGE}"]').evaluate_all(
                'as => as.map(a => [a.getAttribute("href"), a.getAttribute("target"), a.getAttribute("rel"), a.textContent])')
            want = [f'{PAGE}#{x["dataset"]}-{x["no"]}' for x in c['benchmarks']]
            check('each benchmark citation names the benchmark, its dataset and number, and links into the benchmarks page in a new tab',
                  [l[0] for l in links] == want and all(l[1] == '_blank' and l[2] == 'noopener noreferrer' and f'{x["dataset"]} #{x["no"]}' in l[3]
                                                       and x['name'] in l[3] and '(opens in a new tab)' in l[3] for l, x in zip(links, c['benchmarks'])), links)
            words = pg.inner_text(host('chatbot')).lower()
            phrases = ['these are suggestions', 'block nothing', "the ai canvas's modelling approach is unchanged"]
            check('the copy says these are suggestions, block nothing, and leave the modelling approach unchanged',
                  all(ph in words for ph in phrases), [ph for ph in phrases if ph not in words])
            pg = open_page(b, '#/initiative/hiring')
            risks(pg, 'hiring', 'r1')
            models(pg, 'hiring')
            check('hiring: each candidate states that the table has no G or X benchmark for ranking',
                  all('no G or X benchmark' in pg.inner_text(cand('hiring', x['id'])) for x in DATA['initiatives']['hiring']['candidates']))

        with section('AC4, AC5, AC6'):
            pg = open_page(b, '#/initiative/rcr')
            risks(pg, 'rcr', 'r2')
            models(pg, 'rcr')
            c1 = DATA['initiatives']['rcr']['candidates'][0]
            c2 = DATA['initiatives']['rcr']['candidates'][1]
            text = pg.inner_text(cand('rcr', c1['id']))
            check('rcr: each candidate shows its criteria and states that the table has no benchmark for tabular credit models',
                  all('no benchmark for tabular credit models' in pg.inner_text(cand('rcr', x['id'])) and x['criteria'][0]['text'] in pg.inner_text(cand('rcr', x['id']))
                      for x in (c1, c2)))
            check('a criterion written for this prototype says so, and a record source opens it',
                  'written for this prototype' in pg.inner_text(cand('rcr', c2['id'])).lower()
                  and pg.locator(f'{cand("rcr", c1["id"])} [data-open="evidence:e2"]').count() == 1)
            raises = pg.inner_text(f'{cand("rcr", c1["id"])} [data-model-raises]')
            check('a candidate lists the selected risks it raises', REGISTER['r2'] in raises, raises)
            pg.uncheck('#sugg-risks-rcr [data-pick-risk="r2"]')
            pg.check('#sugg-risks-rcr [data-pick-risk="s-rcr-3"]')
            raises = pg.inner_text(f'{cand("rcr", c1["id"])} [data-model-raises]')
            lowers = pg.inner_text(f'{cand("rcr", c1["id"])} [data-model-lowers]')
            check('unticking a risk removes it at once, and ticking one adds it', REGISTER['r2'] not in raises and 'reason codes' in lowers.lower(),
                  [raises, lowers])
            check('without a mitigation run the evidence block says how to get it',
                  pg.locator(f'{host("rcr")} [data-model-controls-none]').count() == 1 and pg.locator(f'{host("rcr")} [data-model-control]').count() == 0)
            skip(pg, '[data-suggest-mitigations="rcr"]', '#sugg-mitig-rcr', '#sugg-mitig-head-rcr')
            want = list(dict.fromkeys(m['controlKey'] for m in MITIG['risks']['s-rcr-3']))
            got = pg.locator(f'{host("rcr")} [data-model-control]').evaluate_all('es => es.map(e => e.getAttribute("data-model-control"))')
            check('after a mitigation run the block shows evidence for each control behind the mitigations shown', got == want, got)
            pg.check('#sugg-risks-rcr [data-pick-risk="r2"]')
            skip(pg, '[data-suggest-mitigations="rcr"]', '#sugg-mitig-rcr', '#sugg-mitig-head-rcr')
            want = list(dict.fromkeys(m['controlKey'] for r in ('s-rcr-3', 'r2') for m in MITIG['risks'][r]))
            got = pg.locator(f'{host("rcr")} [data-model-control]').evaluate_all('es => es.map(e => e.getAttribute("data-model-control"))')
            check('a later mitigation run updates the block', sorted(got) == sorted(want), got)
            pg.evaluate('location.hash = "#/portfolio"')
            pg.wait_for_selector('#page')
            pg.evaluate('location.hash = "#/initiative/rcr"')
            pg.wait_for_selector('#sugg-model-head-rcr', timeout=2000)
            check('the result survives moving to another page and back', pg.locator(f'{host("rcr")} [data-model]').count() == 2)
            pg.reload()
            pg.wait_for_selector('[data-suggest-risks="rcr"]')
            risks(pg, 'rcr', 'r2')
            check('reload clears the result', pg.locator(f'{host("rcr")} [data-model]').count() == 0
                  and pg.inner_text('[data-suggest-models="rcr"]').strip() == 'Suggest models')

        with section('AC7'):
            pg = open_page(b, '#/initiative/chatbot')
            risks(pg, 'chatbot')
            pg.click('[data-suggest-models="chatbot"]')
            check('with nothing selected the action says so, blocks nothing, and takes focus',
                  NOTHING in pg.inner_text(host('chatbot')) and pg.evaluate('document.querySelector("#sugg-model-chatbot").contains(document.activeElement)'))
            pg.click(f'{host("chatbot")} [data-model-goto]')
            check('"Go to the risk suggestions" moves focus to the first risk checkbox',
                  pg.evaluate('document.activeElement && document.activeElement.matches("#sugg-risks-chatbot [data-pick-risk]")'))

        with section('tampered'):
            d = copy.deepcopy(DATA)
            c = d['initiatives']['chatbot']['candidates'][0]
            for k in ('name', 'fit', 'gaps'):
                c[k] = f'<i data-xss>{k}</i>'
            c['criteria'][0]['text'] = '<i data-xss>criterion</i>'
            c['benchmarks'].append({'dataset': 's100"><img data-xss src=x>', 'no': 1, 'dim': 'G'})
            c['benchmarks'].append({'dataset': 's100', 'no': '1#x', 'dim': 'G'})
            literal = 'var MODEL_SUGGESTIONS=' + script_literal(DATA) + ';'
            check('a copy of index.html can carry tampered data', HTML.count(literal) == 1)
            bent = tmp / 'tampered.html'
            bent.write_text(HTML.replace(literal, 'var MODEL_SUGGESTIONS=' + script_literal(d) + ';'), encoding='utf-8')
            pg = open_page(b, '#/initiative/chatbot', bent.as_uri())
            risks(pg, 'chatbot', 'r5')
            models(pg, 'chatbot')
            text = pg.inner_text(host('chatbot'))
            hrefs = pg.locator(f'{host("chatbot")} a[href^="{PAGE}"]').evaluate_all('as => as.map(a => a.getAttribute("href"))')
            check('curated text reaches the page as text, and a link is built only from a known dataset and a plain number',
                  pg.locator(f'{host("chatbot")} [data-xss]').count() == 0 and all(f'<i data-xss>{k}</i>' in text for k in ('name', 'fit', 'gaps', 'criterion'))
                  and all(re.fullmatch(rf'{re.escape(PAGE)}#(s100|s445)-\d+', h) for h in hrefs), hrefs)

        b.close()

    check('no console or page errors', not errors, errors)
    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
