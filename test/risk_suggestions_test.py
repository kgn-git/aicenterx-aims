"""Behaviour test for the risk agent run on the initiative page (issue #17).

Usage:  python test/risk_suggestions_test.py

agentRun (tools/agent-run.js) is checked directly, on a host the test builds, because #15 and #16 reuse it: steps in
order, the busy guard, the skip control and its focus, reduced motion, and finishing when its host is gone.
The initiative page is checked through its "Suggest risks and harms" button: the run and its result for each pilot,
keyboard use and "Run again", the fields of a suggestion, "Already in the register", selecting suggestions and
register risks, the copy, the empty state of the other initiatives, attribution and AI Index context, escaping and
the render-time url check on tampered data, and leaving mid-run.
test/risk_suggestions_data_test.py holds the rules of the curated data itself.
The prototype's script runs inside one closure, so its names are out of the page's reach: the agentRun and tampered-data
checks load a copy of index.html with agentRun exposed or the data literal swapped, and register risks are read from
the index.html source.
Prints a JSON report; exit code 1 on any failure.
"""
import copy
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
from inline_json import script_literal  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / 'index.html'
URL = INDEX.as_uri()
DATA = json.loads((ROOT / 'tools' / 'data' / 'risk_suggestions.json').read_text(encoding='utf-8'))
REGISTER = re.findall(r'\{id:"(r\d+)",init:"(\w+)",description:"([^"]+)"', INDEX.read_text(encoding='utf-8'))
BOOT = '\nrenderNav();\nrender();\n})();'
PILOTS = ('rcr', 'chatbot', 'hiring')
UNCURATED = ('fraud', 'forecast', 'churn', 'docai', 'pricing')
STEPS = ['Read the AI Canvas', 'Search the MIT AI Risk Repository', 'Match AI incidents', 'Add AI Index context',
         'Draft suggestions']
ALLOWED = ('https://airisk.mit.edu', 'https://incidentdatabase.ai', 'https://hai.stanford.edu', 'https://creativecommons.org')

# Records the order and time at which each step is first marked done, whether the run re-paints or sets attributes.
RECORD = """sel => { window.__log = []; const seen = new Set();
  const scan = () => document.querySelectorAll('[data-step][data-state="done"]').forEach(el => {
    const k = el.textContent.trim(); if (!seen.has(k)) { seen.add(k); window.__log.push({step: k, t: performance.now() - window.__t0}); } });
  if (window.__obs) window.__obs.disconnect();
  window.__obs = new MutationObserver(scan);
  window.__obs.observe(document.body, {subtree: true, childList: true, attributes: true, attributeFilter: ['data-state']});
  window.__t0 = performance.now(); document.querySelector(sel).click(); }"""

# agentRun on a detached-from-the-page host the test owns; returns what onDone saw and when.
UNIT = """async ([mode]) => {
  const host = document.createElement('div'); document.body.appendChild(host);
  const out = {done: 0, at: []}; const t0 = performance.now();
  const steps = ['One', 'Two', 'Three', 'Four', 'Five'];
  const cb = () => { out.done++; out.at.push(performance.now() - t0); };
  const wait = ms => new Promise(r => setTimeout(r, ms));
  agentRun(host, steps, cb);
  out.items = host.querySelectorAll('[data-step]').length;
  out.live = !!host.querySelector('[aria-live]');
  const skip = host.querySelector('[data-run-skip]');
  out.skipFocused = !!skip && document.activeElement === skip;
  if (mode === 'busy') { await wait(900); agentRun(host, steps, cb); await wait(2600); }
  if (mode === 'skip') { skip.click(); await wait(30); out.afterSkip = out.done; await wait(2600); }
  if (mode === 'gone') { await wait(100); host.remove(); await wait(800); out.afterGone = out.done; await wait(2000); }
  if (mode === 'plain' || mode === 'reduced') { await wait(30); out.early = out.done; await wait(2600); }
  out.allDone = [...host.querySelectorAll('[data-step]')].every(e => e.dataset.state === 'done');
  host.remove(); return out; }"""


def variant(folder, name, old, new):
    """A copy of index.html with old replaced once by new, as a file url; None when old is not there exactly once."""
    html = INDEX.read_text(encoding='utf-8')
    if html.count(old) != 1:
        return None
    out = folder / f'{name}.html'
    out.write_text(html.replace(old, new), encoding='utf-8')
    return out.as_uri()


def tampered():
    d = copy.deepcopy(DATA)
    s = d['initiatives']['rcr']['suggestions'][0]
    s['description'] = '<img src=x data-xss>'
    s['incidents'][0]['url'] = 'javascript:alert(1)'
    s['incidents'][1]['url'] = 'https://incidentdatabase.ai.evil.example/cite/1/'
    s['mit']['url'] = 'https://airisk.mit.edu/risks"onmouseover="alert(1)'
    d['initiatives']['rcr']['context']['url'] = 'http://hai.stanford.edu/report'
    d['attribution'][0]['licenceUrl'] = 'https://evil.example\\@creativecommons.org/'
    d['attribution'][1]['url'] = 'https://incidentdatabase.ai:8443/'
    return d


def main():
    tmp = Path(tempfile.mkdtemp(prefix='risk-suggestions-'))
    try:
        return run(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run(tmp):
    checks = {}
    errors = []

    def check(name, ok, detail=''):
        checks[name] = {'ok': bool(ok), 'detail': detail if isinstance(detail, str) else json.dumps(detail)[:1500]}

    def open_page(browser, route, url=URL, **ctx):
        pg = browser.new_context(viewport={'width': 1280, 'height': 900}, **ctx).new_page()
        pg.on('console', lambda m: m.type == 'error' and errors.append(m.text))
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.goto(url + route)
        pg.wait_for_timeout(400)
        return pg

    def run_to_result(pg, init):
        pg.evaluate(RECORD, f'[data-suggest-risks="{init}"]')
        pg.wait_for_function(f'document.getElementById("sugg-risks-head-{init}")', timeout=4000)
        return pg.evaluate('performance.now() - window.__t0'), [x['step'] for x in pg.evaluate('window.__log')]

    def skip_to_result(pg, init):
        pg.click(f'[data-suggest-risks="{init}"]')
        pg.click(f'#sugg-risks-{init} [data-run-skip]')
        pg.wait_for_selector(f'#sugg-risks-head-{init}', timeout=1000)

    def host(init):
        return f'#sugg-risks-{init}'

    with sync_playwright() as p:
        b = p.chromium.launch()

        # agentRun, the shared run component
        exposed = variant(tmp, 'exposed', BOOT, '\nwindow.agentRun=agentRun;' + BOOT)
        check('a copy of index.html can expose agentRun', exposed)
        pg = open_page(b, '#/home', exposed or URL)
        check('agentRun is defined', pg.evaluate('typeof agentRun') == 'function')
        if pg.evaluate('typeof agentRun') == 'function':
            plain = pg.evaluate(UNIT, ['plain'])
            check('agentRun shows every step, announces them, focuses the skip control and finishes once with all steps done',
                  plain['items'] == 5 and plain['live'] and plain['skipFocused'] and plain['early'] == 0
                  and plain['done'] == 1 and plain['allDone'] and plain['at'][0] <= 2500, plain)
            busy = pg.evaluate(UNIT, ['busy'])
            check('agentRun ignores a second start on a busy host', busy['done'] == 1 and busy['at'][0] <= 2500, busy)
            skip = pg.evaluate(UNIT, ['skip'])
            check('"Show all now" finishes the run at once, and only once', skip['afterSkip'] == 1 and skip['done'] == 1
                  and skip['allDone'], skip)
            gone = pg.evaluate(UNIT, ['gone'])
            check('agentRun finishes early, once, when its host leaves the page', gone['afterGone'] == 1 and gone['done'] == 1, gone)
        rm = open_page(b, '#/home', exposed or URL, reduced_motion='reduce')
        if rm.evaluate('typeof agentRun') == 'function':
            red = rm.evaluate(UNIT, ['reduced'])
            check('with reduced motion agentRun finishes at once', red['early'] == 1 and red['done'] == 1 and red['allDone'], red)

        # AC1: the run on each pilot
        for init in PILOTS:
            pg = open_page(b, f'#/initiative/{init}')
            btn = pg.locator(f'[data-suggest-risks="{init}"]')
            check(f'{init}: the button reads "Suggest risks and harms" and the film link stays',
                  btn.count() == 1 and btn.inner_text().strip() == 'Suggest risks and harms'
                  and pg.locator(f'[data-film="{init}"]').count() == 1)
            if btn.count() != 1:
                continue
            took, order = run_to_result(pg, init)
            check(f'{init}: the five steps run in order, then the result shows within 2.5 s',
                  [next((s for s in STEPS if s in o), o) for o in order] == STEPS and took <= 2500, {'took': took, 'order': order})
            n = len(DATA['initiatives'][init]['suggestions'])
            check(f'{init}: the result lists all {n} suggestions',
                  pg.locator(f'{host(init)} [data-sugg^="s-{init}-"]').count() == n)

        # AC2: keyboard, focus, "Run again" and the busy button
        pg = open_page(b, '#/initiative/rcr')
        if pg.locator('[data-suggest-risks="rcr"]').count():
            pg.focus('[data-suggest-risks="rcr"]')
            pg.keyboard.press('Enter')
            check('Enter on the button starts the run and focuses "Show all now"',
                  pg.evaluate('document.activeElement && document.activeElement.hasAttribute("data-run-skip")'))
            pg.keyboard.press('Enter')
            pg.wait_for_timeout(100)
            check('Enter on "Show all now" shows the result and focuses its heading',
                  pg.evaluate('document.activeElement && document.activeElement.id') == 'sugg-risks-head-rcr')
            check('after a run the button reads "Run again"', pg.inner_text('[data-suggest-risks="rcr"]').strip() == 'Run again')
            pg.focus(f'{host("rcr")} [data-pick="s-rcr-1"]')
            pg.keyboard.press('Space')
            check('Space selects a suggestion from the keyboard', pg.is_checked(f'{host("rcr")} [data-pick="s-rcr-1"]'))
            pg.evaluate(RECORD, '[data-suggest-risks="rcr"]')
            pg.wait_for_timeout(900)
            pg.click('[data-suggest-risks="rcr"]')
            pg.wait_for_function('document.getElementById("sugg-risks-head-rcr")', timeout=4000)
            took = pg.evaluate('performance.now() - window.__t0')
            check('"Run again" replays the steps, and a click during the run does not restart it',
                  len(pg.evaluate('window.__log')) == 5 and took <= 2500, {'took': took})
            check('"Run again" keeps the selection', pg.is_checked(f'{host("rcr")} [data-pick="s-rcr-1"]'))

        # AC3, AC4, AC6, AC8 on rcr
        pg = open_page(b, '#/initiative/rcr')
        if pg.locator('[data-suggest-risks="rcr"]').count():
            skip_to_result(pg, 'rcr')
            s = DATA['initiatives']['rcr']['suggestions'][0]
            item = pg.locator(f'{host("rcr")} [data-sugg="{s["id"]}"]')
            text = item.inner_text()
            want = [s['description'], 'Discrimination', 'Possible', 'Major', s['lifecycleStage'], 'Data Strategy',
                    s['mit']['domain'], s['mit']['subdomain']]
            check('a suggestion shows description, harm, likelihood, severity, stage, canvas block, MIT domain and subdomain',
                  all(w in text for w in want) and 'dataStrategy' not in text, [w for w in want if w not in text])
            hrefs = item.locator('a').evaluate_all('as => as.map(a => a.getAttribute("href"))')
            check('a suggestion links each of its incidents', all(i['url'] in hrefs for i in s['incidents']), hrefs)
            links = pg.locator(f'{host("rcr")} a').evaluate_all(
                'as => as.map(a => [a.getAttribute("href"), a.getAttribute("target"), a.getAttribute("rel")])')
            check('every link in the result is allow-listed https, opens in a new tab with noopener noreferrer',
                  links and all(h.startswith(ALLOWED) and t == '_blank' and r == 'noopener noreferrer' for h, t, r in links),
                  [l for l in links if not (l[0].startswith(ALLOWED) and l[1] == '_blank' and l[2] == 'noopener noreferrer')])

            matched = [x for x in DATA['initiatives']['rcr']['suggestions'] if x['matchesRisk']]
            unmatched = [x for x in DATA['initiatives']['rcr']['suggestions'] if not x['matchesRisk']]
            def match_link(x):
                return pg.locator(f'{host("rcr")} [data-sugg="{x["id"]}"] [data-open="risk:{x["matchesRisk"]}"]')
            check('a suggestion that matches a register risk says "Already in the register"', matched and all(
                match_link(x).count() == 1 and 'Already in the register' in match_link(x).inner_text() for x in matched))
            check('a suggestion with no match does not', all('Already in the register' not in
                  pg.inner_text(f'{host("rcr")} [data-sugg="{x["id"]}"]') for x in unmatched))
            if matched:
                pg.click(f'{host("rcr")} [data-sugg="{matched[0]["id"]}"] [data-open="risk:{matched[0]["matchesRisk"]}"]')
                pg.wait_for_timeout(300)
                want = next(d for r, i, d in REGISTER if r == matched[0]['matchesRisk'])
                check('"Already in the register" opens that risk', pg.is_visible('#modal') and want in pg.inner_text('#modal'), want)
                pg.keyboard.press('Escape')
                pg.wait_for_timeout(200)

            copy = pg.inner_text(host('rcr')).lower()
            phrases = ['these are suggestions', 'block nothing', 'nothing enters the risk register until a person adds it',
                       'kept until you reload', 'suggests mitigations']
            check('the copy says suggestions block nothing, nothing enters the register, and what the selection is for',
                  all(ph in copy for ph in phrases), [ph for ph in phrases if ph not in copy])

            attr = pg.locator(f'{host("rcr")} [data-attribution] li')
            rows = attr.evaluate_all('ls => ls.map(l => ({text: l.innerText, links: [...l.querySelectorAll("a")].map(a => [a.getAttribute("href"), a.innerText.replace(/\\u2197/g, "").trim()])}))')
            def shown(a):
                return any([a['url'], a['source']] in r['links'] and [a['licenceUrl'], a['licence']] in r['links']
                           and a['changes'] in r['text'] for r in rows)
            check('each source shows its linked name, linked licence and changes note',
                  len(rows) == 3 and all(shown(a) for a in DATA['attribution']), rows)
            ctx = DATA['initiatives']['rcr']['context']
            box = pg.locator(f'{host("rcr")} [data-sugg-context]')
            check('the AI Index statement shows verbatim with its chapter and link', box.count() == 1
                  and ctx['statement'] in box.inner_text() and ctx['chapter'] in box.inner_text()
                  and box.locator(f'a[href="{ctx["url"]}"]').count() == 1)

        # AC5, AC12: selection, leaving and coming back, reload
        pg = open_page(b, '#/initiative/rcr')
        if pg.locator('[data-suggest-risks="rcr"]').count():
            skip_to_result(pg, 'rcr')
            reg = [r for r, i, _ in REGISTER if i == 'rcr']
            check('the initiative\'s register risks are listed with the suggestions and selectable',
                  reg and all(pg.locator(f'{host("rcr")} [data-pick="{r}"]').count() == 1 for r in reg), reg)
            pg.check(f'{host("rcr")} [data-pick="s-rcr-2"]')
            pg.check(f'{host("rcr")} [data-pick="{reg[0]}"]')
            two = pg.inner_text(f'{host("rcr")} [data-sugg-count]')
            pg.uncheck(f'{host("rcr")} [data-pick="{reg[0]}"]')
            one = pg.inner_text(f'{host("rcr")} [data-sugg-count]')
            check('selecting and deselecting either kind updates the "N selected" count', '2 selected' in two and '1 selected' in one,
                  [two, one])
            pg.evaluate('location.hash = "#/portfolio"'); pg.wait_for_timeout(300)
            pg.evaluate('location.hash = "#/initiative/rcr"'); pg.wait_for_timeout(300)
            check('the result and the selection survive moving to another page and back',
                  pg.locator('#sugg-risks-head-rcr').count() == 1 and pg.is_checked(f'{host("rcr")} [data-pick="s-rcr-2"]'))
            pg.click('[data-suggest-risks="rcr"]'); pg.wait_for_timeout(500)
            pg.evaluate('location.hash = "#/portfolio"'); pg.wait_for_timeout(300)
            pg.evaluate('location.hash = "#/initiative/rcr"'); pg.wait_for_timeout(2500)
            check('leaving during "Run again" and coming back shows the result and the selection',
                  pg.locator('#sugg-risks-head-rcr').count() == 1 and pg.is_checked(f'{host("rcr")} [data-pick="s-rcr-2"]'))
            pg.evaluate('location.hash = "#/initiative/chatbot"'); pg.wait_for_timeout(300)
            skip_to_result(pg, 'chatbot')
            check('the selection is kept per initiative', '0 selected' in pg.inner_text(f'{host("chatbot")} [data-sugg-count]'))
            pg.evaluate('location.hash = "#/initiative/rcr"'); pg.wait_for_timeout(200)
            pg.reload(); pg.wait_for_timeout(400)
            check('reload clears the result', pg.locator('#sugg-risks-head-rcr').count() == 0
                  and pg.inner_text('[data-suggest-risks="rcr"]').strip() == 'Suggest risks and harms')
            skip_to_result(pg, 'rcr')
            check('reload clears the selection', not pg.is_checked(f'{host("rcr")} [data-pick="s-rcr-2"]'))

        pg = open_page(b, '#/initiative/hiring')
        if pg.locator('[data-suggest-risks="hiring"]').count():
            pg.click('[data-suggest-risks="hiring"]'); pg.wait_for_timeout(500)
            pg.evaluate('location.hash = "#/portfolio"'); pg.wait_for_timeout(300)
            pg.evaluate('location.hash = "#/initiative/hiring"'); pg.wait_for_timeout(2500)
            check('leaving during a first run and coming back shows the finished result',
                  pg.locator('#sugg-risks-head-hiring').count() == 1)
            # In one script, so the second run surely starts before the first run's next step.
            steps, head = pg.evaluate("""async () => { const w = ms => new Promise(r => setTimeout(r, ms));
              const go = () => document.querySelector('[data-suggest-risks="hiring"]').click();
              go(); await w(50); location.hash = '#/portfolio'; await w(30); location.hash = '#/initiative/hiring'; await w(30);
              go(); await w(450);
              return [document.querySelectorAll('#sugg-risks-hiring [data-step]').length, !!document.getElementById('sugg-risks-head-hiring')]; }""")
            check('the run left behind does not paint over a newer run', steps == 5 and not head, [steps, head])

        # AC7: the other initiatives
        for init in UNCURATED:
            pg = open_page(b, f'#/initiative/{init}')
            if not pg.locator(f'[data-suggest-risks="{init}"]').count():
                check(f'{init}: shows the button and an empty state with "Log a risk"', False, 'no button')
                continue
            pg.click(f'[data-suggest-risks="{init}"]'); pg.wait_for_timeout(300)
            empty = pg.locator(f'{host(init)} [data-sugg-empty]')
            log = empty.locator(f'[data-form="risk"][data-ctx="initiative:{init}"]')
            ok = empty.count() == 1 and 'no curated suggestions' in empty.inner_text().lower() and log.count() == 1
            if ok:
                log.click(); pg.wait_for_timeout(300)
                ok = pg.is_visible('#modal') and pg.inner_text('#modalTitle').strip() == 'Log a risk'
            check(f'{init}: shows the button and an empty state with "Log a risk"', ok)

        # AC9, AC11: tampered data is escaped, and a url that fails the check is not linked
        bent = variant(tmp, 'tampered', 'var RISK_SUGGESTIONS=' + script_literal(DATA) + ';',
                       'var RISK_SUGGESTIONS=' + script_literal(tampered()) + ';')
        check('a copy of index.html can carry tampered data', bent)
        pg = open_page(b, '#/initiative/rcr', bent or URL)
        if bent and pg.locator('[data-suggest-risks="rcr"]').count():
            skip_to_result(pg, 'rcr')
            check('curated text reaches the page as text, never as markup',
                  pg.locator(f'{host("rcr")} img[data-xss]').count() == 0
                  and '<img src=x data-xss>' in pg.inner_text(f'{host("rcr")} [data-sugg="s-rcr-1"]'))
            check('a quote in a url cannot add an attribute', pg.locator(f'{host("rcr")} [onmouseover]').count() == 0)
            hrefs = pg.locator(f'{host("rcr")} a').evaluate_all('as => as.map(a => a.getAttribute("href"))')
            bad = [h for h in hrefs if not h.startswith(ALLOWED) or 'evil' in h or ':8443' in h or h.startswith('http:')]
            check('a url that fails the render-time check is not linked', not bad and len(hrefs) > 3, bad or hrefs)

        b.close()

    check('no console or page errors', not errors, errors)
    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
