"""Behaviour test for the mitigation run on the initiative page (issue #15).

Usage:  python test/mitigation_suggestions_test.py

The initiative page is checked through its "Suggest mitigations" button, which sits in the risk result of #17: one
timed run and the mitigations for each pilot, the fields of a mitigation and its sources, gaps and the control owner,
a register risk's existing treatment, the nothing-selected state, unticking and newly ticked risks after a run,
leaving and reload, the copy, its absence on an initiative without curated risks, and escaping and the render-time url
check on tampered data.
agentRun's own rules are pinned in test/risk_suggestions_test.py, and the data's in
test/mitigation_suggestions_data_test.py, whose url_ok rule is the link rule here.
The prototype's script runs inside one closure, so the tampered-data checks load a copy of index.html with the data
literal swapped, and register risks, controls and people are read from the index.html source.
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

from risk_suggestions_data_test import url_ok

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
from inline_json import script_literal  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / 'index.html'
URL = INDEX.as_uri()
HTML = INDEX.read_text(encoding='utf-8')
DATA = json.loads((ROOT / 'tools' / 'data' / 'mitigation_suggestions.json').read_text(encoding='utf-8'))
RISK_DATA = json.loads((ROOT / 'tools' / 'data' / 'risk_suggestions.json').read_text(encoding='utf-8'))
CONTROLS = {k: (o, c, w) for k, o, c, w in re.findall(r'\{key:"(A\.\d+)",objective:"([^"]*)",closure:"([\w-]+)",owner:"(\w+)"', HTML)}
TREATMENT = {m.group(1): m.group(2, 3) for m in (re.match(r'\{id:"(r\d+)",init:"\w+".*?treatment:(?:null|\{strategy:"(\w+)",owner:"(\w+)")', c, re.S)
                                                 for c in re.split(r'(?=\{id:"r\d+",init:)', HTML)[1:]) if m}
DECISIONS = dict(re.findall(r'\{id:"(d\d+)",kind:"[\w-]+",subject:"[^"]*",init:(?:"\w+"|null),by:"\w+",at:"[^"]*",meeting:"[^"]*",summary:"([^"]+)"', HTML))
HOSTS = ('airisk.mit.edu', 'incidentdatabase.ai', 'eur-lex.europa.eu', 'creativecommons.org')
STEPS = ['Read the selected risks', "Check the register's treatments", 'Match the controls', 'Search mitigation sources',
         'Draft mitigations']
FREE = {i: [s['id'] for s in RISK_DATA['initiatives'][i]['suggestions'] if not s['matchesRisk']] for i in RISK_DATA['initiatives']}
NOTHING = 'Select risks above to get mitigations. This blocks nothing.'

# Records, in the page, when each step is first marked done and when the result heading appears.
RECORD = """([sel, head]) => { window.__log = []; window.__headT = null; const seen = new Set();
  const scan = () => { document.querySelectorAll('[data-step][data-state="done"]').forEach(el => {
      const k = el.textContent.trim(); if (!seen.has(k)) { seen.add(k); window.__log.push(k); } });
    if (window.__headT === null && document.getElementById(head)) window.__headT = performance.now() - window.__t0; };
  if (window.__obs) window.__obs.disconnect();
  window.__obs = new MutationObserver(scan);
  window.__obs.observe(document.body, {subtree: true, childList: true, attributes: true, attributeFilter: ['data-state']});
  window.__t0 = performance.now(); document.querySelector(sel).click(); }"""


def tampered():
    """rcr's mitigations with markup in every rendered text field and urls the render-time check must refuse or quote."""
    d = copy.deepcopy(DATA)
    shown = []

    def mark(obj, key):
        obj[key] = f'<i data-xss>{key} {len(shown)}</i>'
        shown.append(obj[key])

    for rid in ('r2', 's-rcr-3'):
        for m in d['risks'][rid]:
            for key in ('description', 'why'):
                mark(m, key)
            for s in m['sources']:
                if 'title' in s:
                    mark(s, 'title')
    for a in d['attribution']:
        for key in ('source', 'licence', 'changes'):
            mark(a, key)
    first, second = d['risks']['s-rcr-3'][0], d['risks']['r2'][0]
    first['sources'] = [{'url': 'javascript:alert(1)', 'title': 'bad one'}, {'url': 'https://eur-lex.europa.eu.evil.example/x', 'title': 'bad two'},
                        {'url': 'https://eur-lex.europa.eu/x"onmouseover="alert(1)', 'title': 'quoted'}]
    second['sources'].append({'url': "https://eur-lex.europa.eu/x'onfocus='alert(1)", 'title': 'single'})
    d['attribution'][1]['licenceUrl'] = 'https://evil.example\\@eur-lex.europa.eu/'
    return d, shown, ('https://eur-lex.europa.eu/x"onmouseover="alert(1)', "https://eur-lex.europa.eu/x'onfocus='alert(1)")


def main():
    tmp = Path(tempfile.mkdtemp(prefix='mitigation-suggestions-'))
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

    def open_page(browser, route, url=URL):
        pg = browser.new_context(viewport={'width': 1280, 'height': 900}).new_page()
        pg.on('console', lambda m: m.type == 'error' and errors.append(m.text))
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.goto(url + route)
        pg.wait_for_selector('#page')
        return pg

    def go(pg, route, sel):
        pg.evaluate(f'location.hash = "{route}"')
        pg.wait_for_selector(sel, timeout=2000)

    def risk_result(pg, init):
        pg.click(f'[data-suggest-risks="{init}"]')
        pg.click(f'#sugg-risks-{init} [data-run-skip]')
        pg.wait_for_selector(f'#sugg-risks-head-{init}', timeout=1000)

    def pick(pg, init, *rids):
        for r in rids:
            pg.check(f'#sugg-risks-{init} [data-pick-risk="{r}"]')

    def mitigate(pg, init):
        pg.click(f'[data-suggest-mitigations="{init}"]')
        pg.click(f'{host(init)} [data-run-skip]')
        pg.wait_for_selector(f'#sugg-mitig-head-{init}', timeout=1000)

    def host(init):
        return f'#sugg-mitig-{init}'

    def block(init, rid):
        return f'{host(init)} [data-mitig-risk="{rid}"]'

    with sync_playwright() as p:
        b = p.chromium.launch()

        with section('AC1'):
            for init in ('rcr', 'chatbot', 'hiring'):
                pg = open_page(b, f'#/initiative/{init}')
                risk_result(pg, init)
                btn = pg.locator(f'#sugg-risks-{init} [data-suggest-mitigations="{init}"]')
                check(f'{init}: "Suggest mitigations" sits in the risk result', btn.count() == 1
                      and btn.inner_text().strip() == 'Suggest mitigations')
                rid = FREE[init][0]
                pick(pg, init, rid)
                if init == 'rcr':
                    pg.evaluate(RECORD, ['[data-suggest-mitigations="rcr"]', 'sugg-mitig-head-rcr'])
                    pg.wait_for_selector('#sugg-mitig-head-rcr', timeout=4000)
                    took, order = pg.evaluate('window.__headT'), pg.evaluate('window.__log')
                    check('rcr: the five mitigation steps run in order, then the result shows within 2.5 s',
                          [next((s for s in STEPS if s in o), o) for o in order] == STEPS and took <= 2500, {'took': took, 'order': order})
                else:
                    mitigate(pg, init)
                n = len(DATA['risks'][rid])
                check(f'{init}: the result shows the {n} mitigations of the selected risk',
                      pg.locator(f'{block(init, rid)} [data-mitig]').count() == n)
                check(f'{init}: after a run the button reads "Suggest mitigations again"',
                      pg.inner_text(f'[data-suggest-mitigations="{init}"]').strip() == 'Suggest mitigations again')

        with section('AC2, AC3, AC4, AC7'):
            pg = open_page(b, '#/initiative/rcr')
            risk_result(pg, 'rcr')
            pick(pg, 'rcr', 'r2', 's-rcr-4')
            mitigate(pg, 'rcr')
            m = DATA['risks']['r2'][0]
            key = m['controlKey']
            objective, closure, owner = CONTROLS[key]
            item = pg.locator(f'{host("rcr")} [data-mitig="{m["id"]}"]')
            text = item.inner_text()
            want = [m['description'], 'Mitigate', key, objective, 'In progress', m['lifecycleStage'], m['why'], m['mit'], 'draft']
            check('a mitigation shows strategy, control key and objective, closure, stage, rationale and its MIT subcategory as a draft',
                  all(w in text for w in want), [w for w in want if w not in text])
            check('a mitigation names its control and opens it', item.locator(f'[data-open="control:{key}"]').count() == 1)
            records = [s['record'] for s in m['sources'] if 'record' in s]
            check('a record source names the decision or evidence and opens it',
                  records and all(item.locator(f'[data-open$=":{r}"]').count() == 1 for r in records), records)
            pg.click(f'{host("rcr")} [data-mitig="{m["id"]}"] [data-open="decision:d2"]')
            pg.wait_for_selector('#modal', state='visible', timeout=1000)
            check('a decision source opens that decision', DECISIONS['d2'][:40] in pg.inner_text('#modal'))
            pg.keyboard.press('Escape')
            pg.wait_for_selector('#modal', state='hidden', timeout=1000)
            check('a mitigation on a control that is not implemented is a gap naming the control owner',
                  item.locator(f'[data-gap] [data-open="person:{owner}"]').count() == 1)
            impl = next(x for x in DATA['risks']['s-rcr-4'] if CONTROLS[x['controlKey']][1] == 'implemented')
            check('a mitigation on an implemented control is not a gap',
                  pg.locator(f'{host("rcr")} [data-mitig="{impl["id"]}"]').count() == 1
                  and pg.locator(f'{host("rcr")} [data-mitig="{impl["id"]}"] [data-gap]').count() == 0)
            first = pg.locator(f'{block("rcr", "r2")} > [data-in-register], {block("rcr", "r2")} > [data-mitig]').first
            strategy, t_owner = TREATMENT['r2']
            reg = pg.locator(f'{block("rcr", "r2")} [data-in-register]')
            r2_owner = CONTROLS[re.search(r'\{id:"r2",.*?controlKey:"(A\.\d+)"', HTML, re.S).group(1)][2]
            check('a selected register risk shows its treatment first, "In the register", with the treatment owner and a gap naming the control owner',
                  first.get_attribute('data-in-register') is not None and 'In the register' in reg.inner_text()
                  and strategy.capitalize() in reg.inner_text() and reg.locator(f'[data-open="person:{t_owner}"]').count() >= 1
                  and reg.locator(f'[data-gap] [data-open="person:{r2_owner}"]').count() == 1
                  and reg.locator('[data-open="risk:r2"]').count() == 1)
            check('a suggested risk has no "In the register" row', pg.locator(f'{block("rcr", "s-rcr-4")} [data-in-register]').count() == 0)
            links = pg.locator(f'{host("rcr")} a').evaluate_all(
                'as => as.map(a => [a.getAttribute("href"), a.getAttribute("target"), a.getAttribute("rel"), a.textContent])')
            bad = [l for l in links if not (any(url_ok(l[0], h) for h in HOSTS) and l[1] == '_blank'
                                            and l[2] == 'noopener noreferrer' and '(opens in a new tab)' in l[3])]
            check('every link is allow-listed https and opens in a new tab, says so, with noopener noreferrer', links and not bad, bad)
            words = pg.inner_text(host('rcr')).lower()
            phrases = ['these are suggestions', 'block nothing', 'no control or treatment changes until a person acts']
            check('the copy says mitigations are suggestions, block nothing, and change nothing until a person acts',
                  all(ph in words for ph in phrases), [ph for ph in phrases if ph not in words])
            rows = pg.locator(f'{host("rcr")} [data-attribution] li').evaluate_all(
                'ls => ls.map(l => ({text: l.innerText, links: [...l.querySelectorAll("a")].map(a => [a.getAttribute("href"), a.firstChild.textContent])}))')
            check('each external source shows its linked name, linked licence and changes note',
                  len(rows) == len(DATA['attribution']) and all(any([a['url'], a['source']] in r['links'] and [a['licenceUrl'], a['licence']] in r['links']
                                                                     and a['changes'] in r['text'] for r in rows) for a in DATA['attribution']), rows)

        with section('AC4 r4'):
            pg = open_page(b, '#/initiative/hiring')
            risk_result(pg, 'hiring')
            pick(pg, 'hiring', 'r4')
            mitigate(pg, 'hiring')
            reg = pg.locator(f'{block("hiring", "r4")} [data-in-register]')
            check('a register risk with no treatment shows "No treatment recorded" as a gap',
                  'No treatment recorded' in reg.inner_text() and reg.locator('[data-gap]').count() == 1)

        with section('AC5'):
            pg = open_page(b, '#/initiative/chatbot')
            risk_result(pg, 'chatbot')
            pg.click('[data-suggest-mitigations="chatbot"]')
            msg = pg.locator(f'{host("chatbot")} [data-mitig-none]')
            check('with nothing selected the action says it needs selected risks and blocks nothing',
                  msg.count() == 1 and NOTHING in msg.inner_text() and pg.locator(f'{host("chatbot")} [data-step]').count() == 0)
            check('the nothing-selected message takes focus',
                  pg.evaluate('document.querySelector("#sugg-mitig-chatbot [data-mitig-none]").contains(document.activeElement)'))
            pg.click(f'{host("chatbot")} [data-mitig-goto]')
            check('"Go to the risk suggestions" moves focus to the first risk checkbox',
                  pg.evaluate('document.activeElement && document.activeElement.matches("#sugg-risks-chatbot [data-pick-risk]")'))

        with section('AC6'):
            pg = open_page(b, '#/initiative/rcr')
            risk_result(pg, 'rcr')
            pick(pg, 'rcr', 'r2', 's-rcr-3')
            mitigate(pg, 'rcr')
            pg.uncheck('#sugg-risks-rcr [data-pick-risk="r2"]')
            check('unticking a risk removes its mitigations at once',
                  pg.locator(block('rcr', 'r2')).count() == 0 and pg.locator(block('rcr', 's-rcr-3')).count() == 1)
            pick(pg, 'rcr', 's-rcr-5')
            note = pg.locator(f'{host("rcr")} [data-mitig-fresh]')
            check('a risk ticked after the run shows a note and no mitigations yet',
                  note.count() == 1 and 'Suggest mitigations again to add them for 1 new risk.' in note.inner_text()
                  and pg.locator(block('rcr', 's-rcr-5')).count() == 0)
            go(pg, '#/portfolio', '#page')
            go(pg, '#/initiative/rcr', '#sugg-mitig-head-rcr')
            check('the result survives moving to another page and back',
                  pg.locator(block('rcr', 's-rcr-3')).count() == 1 and pg.locator(f'{host("rcr")} [data-mitig-fresh]').count() == 1)
            pg.click('[data-suggest-risks="rcr"]')
            pg.click('#sugg-risks-rcr [data-run-skip]')
            pg.wait_for_selector('#sugg-mitig-head-rcr', timeout=1000)
            check('running the risk agent again keeps the mitigations', pg.locator(block('rcr', 's-rcr-3')).count() == 1)
            mitigate(pg, 'rcr')
            check('"Suggest mitigations again" adds the newly ticked risk', pg.locator(block('rcr', 's-rcr-5')).count() == 1
                  and pg.locator(f'{host("rcr")} [data-mitig-fresh]').count() == 0)
            pg.uncheck('#sugg-risks-rcr [data-pick-risk="s-rcr-3"]')
            pg.uncheck('#sugg-risks-rcr [data-pick-risk="s-rcr-5"]')
            check('unticking every covered risk shows the nothing-selected message',
                  NOTHING in pg.inner_text(host('rcr')) and pg.locator(f'{host("rcr")} [data-mitig-risk]').count() == 0)
            pg.reload()
            pg.wait_for_selector('[data-suggest-risks="rcr"]')
            check('reload clears the mitigations', pg.locator('[data-suggest-mitigations="rcr"]').count() == 0)

        with section('uncurated'):
            pg = open_page(b, '#/initiative/fraud')
            pg.click('[data-suggest-risks="fraud"]')
            pg.wait_for_selector('#sugg-risks-fraud [data-sugg-empty]', timeout=1000)
            check('an initiative without curated risks offers no mitigation action', pg.locator('[data-suggest-mitigations]').count() == 0)

        with section('AC9 tampered'):
            data, shown, quoted = tampered()
            html = HTML
            literal = 'var MITIGATION_SUGGESTIONS=' + script_literal(DATA) + ';'
            check('a copy of index.html can carry tampered data', html.count(literal) == 1)
            bent = tmp / 'tampered.html'
            bent.write_text(html.replace(literal, 'var MITIGATION_SUGGESTIONS=' + script_literal(data) + ';'), encoding='utf-8')
            pg = open_page(b, '#/initiative/rcr', bent.as_uri())
            risk_result(pg, 'rcr')
            pick(pg, 'rcr', 'r2', 's-rcr-3')
            mitigate(pg, 'rcr')
            text = pg.inner_text(host('rcr'))
            check('every curated text field reaches the page as text, never as markup',
                  pg.locator(f'{host("rcr")} [data-xss]').count() == 0 and all(s in text for s in shown), [s for s in shown if s not in text])
            hrefs = pg.locator(f'{host("rcr")} a').evaluate_all('as => as.map(a => a.getAttribute("href"))')
            check('a quote in a url stays inside its double-quoted href', all(q in hrefs for q in quoted)
                  and pg.locator(f'{host("rcr")} [onmouseover], {host("rcr")} [onfocus]').count() == 0, hrefs)
            check('a url that fails the render-time check is not linked, and its title still shows',
                  all(any(url_ok(h, x) for x in HOSTS) for h in hrefs) and 'bad one' in text and 'bad two' in text, hrefs)

        b.close()

    check('no console or page errors', not errors, errors)
    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
