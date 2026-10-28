"""Behaviour test for the risk agent run on the initiative page.

Usage:  python test/risk_suggestions_test.py

agentRun (tools/agent-run.js) is checked directly, on a host the test builds, because #15 and #16 reuse it: steps in
order and announced, the busy guard, the skip control and its focus, reduced motion, no steps, finishing when its host
is gone, and where the result goes when navigation has rebuilt the host.
The initiative page is checked through its "Suggest risks and harms" button: one timed run and its result for each
pilot, keyboard use and "Run again", the fields of a suggestion, "Already in the register", selecting suggestions and
register risks, the copy, the empty state of the other initiatives, attribution and AI Index context, escaping and
the render-time url check on tampered data, and leaving mid-run.
test/risk_suggestions_data_test.py holds the rules of the curated data itself; test/source_url.py holds the link rule.
The prototype's script runs inside one closure, so its names are out of the page's reach: the agentRun and tampered-data
checks load a copy of index.html with agentRun exposed or the data literal swapped, and register risks are read from
the index.html source.
Prints a JSON report; exit code 1 on any failure.
"""
import copy
import json
from contextlib import contextmanager
import re
import shutil
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

from source_url import url_ok

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
HOSTS = ('airisk.mit.edu', 'incidentdatabase.ai', 'hai.stanford.edu', 'creativecommons.org')
RCR = DATA['initiatives']['rcr']['suggestions']
FREE = [x['id'] for x in RCR if not x['matchesRisk']]

# Records, in the page, when each step is first marked done and when the result heading appears.
RECORD = """([sel, head]) => { window.__log = []; window.__headT = null; const seen = new Set();
  const scan = () => { document.querySelectorAll('[data-step][data-state="done"]').forEach(el => {
      const k = el.textContent.trim(); if (!seen.has(k)) { seen.add(k); window.__log.push({step: k, t: performance.now() - window.__t0}); } });
    if (window.__headT === null && document.getElementById(head)) window.__headT = performance.now() - window.__t0; };
  if (window.__obs) window.__obs.disconnect();
  window.__obs = new MutationObserver(scan);
  window.__obs.observe(document.body, {subtree: true, childList: true, attributes: true, attributeFilter: ['data-state']});
  window.__t0 = performance.now(); document.querySelector(sel).click(); }"""

# agentRun on a host the test owns; returns what onDone saw and when, and where the result went.
UNIT = """async ([mode, steps]) => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const mk = html => { const h = document.createElement('div'); h.id = 'unit-host'; h.innerHTML = html; document.body.appendChild(h); return h; };
  const runHost = mk(''); const out = {done: 0, at: [], said: []}; const t0 = performance.now();
  const cb = () => { out.done++; out.at.push(performance.now() - t0);
    if (out.done === 1) { const ls = [...runHost.querySelectorAll('[data-step]')];
      out.statesAtDone = ls.map(e => e.dataset.state); out.textsAtDone = ls.map(e => e.textContent);
      out.skipAtDone = !!runHost.querySelector('[data-run-skip]'); }
    return mode === 'nohtml' ? undefined : '<h3 data-run-head tabindex="-1" data-run-state="v1">Result</h3>'; };
  out.started = agentRun('unit-host', steps, cb);
  out.items = runHost.querySelectorAll('[data-step]').length;
  const st = runHost.querySelector('[role=status]');
  if (st) new MutationObserver(() => out.said.push(st.textContent)).observe(st, {childList: true, characterData: true, subtree: true});
  const skip = runHost.querySelector('[data-run-skip]');
  out.skipFocused = !!skip && document.activeElement === skip;
  const settle = async () => { for (let i = 0; i < 40 && out.done < 1; i++) await wait(50); };
  let host = runHost;
  if (mode === 'tabbed') { await wait(100); const b = document.createElement('button'); b.id = 'elsewhere'; document.body.appendChild(b);
    b.focus(); await wait(2600); out.keptFocus = document.activeElement === b; b.remove(); }
  if (mode === 'nohtml') { skip.click(); await wait(30); out.hostText = runHost.textContent; }
  if (mode === 'busy') { await wait(900); out.second = agentRun('unit-host', steps, cb); await wait(2600); }
  if (mode === 'skip') { skip.click(); await wait(30); out.afterSkip = out.done; await wait(2600); }
  if (mode === 'gone') { await wait(100); runHost.remove(); await wait(800); out.afterGone = out.done; await wait(2000); }
  if (mode === 'plain' || mode === 'reduced' || mode === 'none') { await wait(30); out.early = out.done; await wait(2600); }
  if (mode.startsWith('rebuilt') || mode === 'newer') {
    await wait(100); runHost.remove();
    host = mk({'rebuilt-same': '<h3 data-run-head data-run-state="v1">Edited since</h3>', 'rebuilt-stale': '<h3 data-run-head data-run-state="v0">Stale</h3>',
               'rebuilt-busy': '<div data-run-state="v0"><div data-run-busy></div></div>'}[mode] || '');
    const before = host.firstChild;
    if (mode === 'newer') agentRun('unit-host', steps, cb);
    await settle(); await wait(50); out.afterOld = out.done; out.sameNode = !!before && host.firstChild === before;
    out.freshSteps = host.querySelectorAll('[data-step]').length;
    const h = host.querySelector('[data-run-head]'); out.freshHead = h && h.textContent;
    out.focusedFresh = !!h && document.activeElement === h;
    await wait(2600);
  }
  const head = host.querySelector('[data-run-head]');
  out.painted = head && head.textContent; out.headFocused = !!head && document.activeElement === head;
  host.remove(); return out; }"""


class Out(dict):
    """An agentRun result whose missing fields read as None, so a run that threw fails its checks instead of the test."""
    def __missing__(self, key):
        return None


def variant(folder, name, old, new):
    """A copy of index.html with old replaced once by new, as a file url; None when old is not there exactly once."""
    html = INDEX.read_text(encoding='utf-8')
    if html.count(old) != 1:
        return None
    out = folder / f'{name}.html'
    out.write_text(html.replace(old, new), encoding='utf-8')
    return out.as_uri()


def tampered():
    """rcr's data with markup in every rendered text field and urls that the render-time check must refuse or quote."""
    d = copy.deepcopy(DATA)
    shown = []

    def mark(obj, key):
        obj[key] = f'<i data-xss>{key} {len(shown)}</i>'
        shown.append(obj[key])

    rcr = d['initiatives']['rcr']
    for s in rcr['suggestions']:
        for key in ('description', 'lifecycleStage'):
            mark(s, key)
        mark(s['mit'], 'domain')
        mark(s['mit'], 'subdomain')
        for n in s['incidents']:
            mark(n, 'title')
    for key in ('statement', 'edition', 'chapter'):
        mark(rcr['context'], key)
    for a in d['attribution']:
        for key in ('source', 'licence', 'changes'):
            mark(a, key)
    s0, s1 = rcr['suggestions'][0], rcr['suggestions'][1]
    s0['incidents'][0]['url'] = 'javascript:alert(1)'
    s0['incidents'][1]['url'] = 'https://incidentdatabase.ai.evil.example/cite/1/'
    s0['mit']['url'] = 'https://airisk.mit.edu/risks"onmouseover="alert(1)'
    s1['mit']['url'] = "https://airisk.mit.edu/risks'onfocus='alert(1)"
    rcr['context']['url'] = 'http://hai.stanford.edu/report'
    d['attribution'][0]['licenceUrl'] = 'https://evil.example\\@creativecommons.org/'
    d['attribution'][1]['url'] = 'https://incidentdatabase.ai:8443/'
    d['attribution'][2].update(key='unknown', url='https://undefined/')
    return d, shown, (s0['mit']['url'], s1['mit']['url'])


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

    @contextmanager
    def section(name):
        try:
            yield
        except Exception as e:  # noqa: BLE001 - a timeout or missing element fails its section, never the whole report
            check(f'{name}: ran to the end', False, str(e)[:300])

    def appears(pg, sel, timeout):
        try:
            pg.wait_for_selector(sel, timeout=timeout)
            return True
        except Exception:  # noqa: BLE001 - not appearing in time is the failure being checked
            return False

    def open_page(browser, route, url=URL, **ctx):
        pg = browser.new_context(viewport={'width': 1280, 'height': 900}, **ctx).new_page()
        pg.on('console', lambda m: m.type == 'error' and errors.append(m.text))
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.goto(url + route)
        pg.wait_for_selector('#page')
        return pg

    def unit(pg, mode, steps):
        try:
            return Out(pg.evaluate(UNIT, [mode, steps]))
        except Exception as e:  # noqa: BLE001 - a throw inside agentRun is reported as that check's failure
            return Out(error=str(e)[:300])

    def go(pg, route, sel):
        pg.evaluate(f'location.hash = "{route}"')
        pg.wait_for_selector(sel, timeout=2000)

    def skip_to_result(pg, init):
        pg.click(f'[data-suggest-risks="{init}"]')
        pg.click(f'#sugg-risks-{init} [data-run-skip]')
        pg.wait_for_selector(f'#sugg-risks-head-{init}', timeout=1000)

    def host(init):
        return f'#sugg-risks-{init}'

    def pick(init, rid):
        return f'{host(init)} [data-pick-risk="{rid}"]'

    with sync_playwright() as p:
        b = p.chromium.launch()

        check('rcr has at least two suggestions with no register match', len(FREE) >= 2, FREE)

        # agentRun, the shared run component
        with section('agentRun'):
            exposed = variant(tmp, 'exposed', BOOT, '\nwindow.agentRun=agentRun;' + BOOT)
            check('a copy of index.html can expose agentRun', exposed)
            pg = open_page(b, '#/home', exposed or URL)
            check('agentRun is defined', pg.evaluate('typeof agentRun') == 'function')
            if pg.evaluate('typeof agentRun') == 'function':
                five = ['One', 'Two', 'Three', 'Four', 'Five']
                r = unit(pg, 'plain', five)
                check('agentRun shows every step, focuses the skip control, and plays for 1.5-2.5 s',
                      r['started'] and r['items'] == 5 and r['skipFocused'] and r['early'] == 0 and r['done'] == 1
                      and 1500 <= r['at'][0] <= 2500, r)
                said = r['said'] or []
                check('agentRun announces each step as it starts, marks each done step in text, and removes the skip control',
                      all(f'Step {i + 1} of 5: {s}' in said for i, s in enumerate(five))
                      and r['statesAtDone'] == ['done'] * 5 and all(t.endswith('(done)') for t in r['textsAtDone'] or [''])
                      and not r['skipAtDone'], r)
                check('agentRun paints what onDone returns and focuses its heading', r['painted'] == 'Result' and r['headFocused'], r)
                r = unit(pg, 'tabbed', five)
                check('agentRun leaves focus where the user moved it during the run', r['done'] == 1 and r['keptFocus'], r)
                r = unit(pg, 'nohtml', five)
                check('agentRun paints nothing when onDone returns no HTML', r['done'] == 1
                      and 'undefined' not in (r['hostText'] or 'undefined') and r['painted'] is None, r)
                r = unit(pg, 'busy', five)
                check('agentRun ignores a second start on a busy host', r['second'] is False and r['done'] == 1, r)
                r = unit(pg, 'skip', five)
                check('"Show all now" finishes the run at once, and only once', r['afterSkip'] == 1 and r['done'] == 1, r)
                r = unit(pg, 'none', [])
                check('agentRun with no steps finishes at once', r['started'] and r['early'] == 1 and r['painted'] == 'Result', r)
                r = unit(pg, 'gone', five)
                check('agentRun finishes early, once, when its host leaves the page', r['afterGone'] == 1 and r['done'] == 1, r)
                r = unit(pg, 'rebuilt-empty', five)
                check('a rebuilt, empty host gets the result without taking focus',
                      r['afterOld'] == 1 and r['freshHead'] == 'Result' and not r['focusedFresh'], r)
                r = unit(pg, 'rebuilt-same', five)
                check('a rebuilt host that shows a result from the same state keeps it untouched, edits included',
                      r['afterOld'] == 1 and r['freshHead'] == 'Edited since' and r['sameNode'], r)
                r = unit(pg, 'rebuilt-busy', five)
                check('a rebuilt host with a newer run inside it is left alone', r['afterOld'] == 1 and r['sameNode']
                      and r['freshHead'] is None, r)
                r = unit(pg, 'rebuilt-stale', five)
                check('a rebuilt host that shows an older result gets the new one',
                      r['afterOld'] == 1 and r['freshHead'] == 'Result' and not r['focusedFresh'], r)
                r = unit(pg, 'newer', five)
                check('the run left behind does not paint over a newer run',
                      r['afterOld'] == 1 and r['freshSteps'] == 5 and r['freshHead'] is None and r['done'] == 2, r)
            rm = open_page(b, '#/home', exposed or URL, reduced_motion='reduce')
            if rm.evaluate('typeof agentRun') == 'function':
                r = unit(rm, 'reduced', ['One', 'Two'])
                check('with reduced motion agentRun finishes at once', r['early'] == 1 and r['done'] == 1, r)

        # AC1: one timed run wires RISK_STEPS to agentRun; every pilot shows its suggestions
        with section('AC1'):
            for init in PILOTS:
                pg = open_page(b, f'#/initiative/{init}')
                btn = pg.locator(f'[data-suggest-risks="{init}"]')
                check(f'{init}: the button reads "Suggest risks and harms" and the film link stays',
                      btn.count() == 1 and btn.inner_text().strip() == 'Suggest risks and harms'
                      and pg.locator(f'[data-film="{init}"]').count() == 1)
                if btn.count() != 1:
                    continue
                if init == 'rcr':
                    pg.evaluate(RECORD, ['[data-suggest-risks="rcr"]', 'sugg-risks-head-rcr'])
                    pg.wait_for_selector('#sugg-risks-head-rcr', timeout=4000)
                    took, order = pg.evaluate('window.__headT'), [x['step'] for x in pg.evaluate('window.__log')]
                    check('rcr: the five steps run in order, then the result shows within 2.5 s',
                          [next((s for s in STEPS if s in o), o) for o in order] == STEPS and took <= 2500, {'took': took, 'order': order})
                else:
                    skip_to_result(pg, init)
                n = len(DATA['initiatives'][init]['suggestions'])
                check(f'{init}: the result lists all {n} suggestions',
                      pg.locator(f'{host(init)} [data-sugg^="s-{init}-"]').count() == n)

        # AC2: keyboard, focus and "Run again"
        with section('AC2'):
            pg = open_page(b, '#/initiative/rcr')
            if pg.locator('[data-suggest-risks="rcr"]').count():
                pg.focus('[data-suggest-risks="rcr"]')
                pg.keyboard.press('Enter')
                check('Enter on the button starts the run and focuses "Show all now"',
                      pg.evaluate('document.activeElement && document.activeElement.hasAttribute("data-run-skip")'))
                pg.keyboard.press('Enter')
                pg.wait_for_selector('#sugg-risks-head-rcr', timeout=1000)
                check('Enter on "Show all now" shows the result and focuses its heading',
                      pg.evaluate('document.activeElement && document.activeElement.id') == 'sugg-risks-head-rcr')
                check('after a run the button reads "Run again"', pg.inner_text('[data-suggest-risks="rcr"]').strip() == 'Run again')
                pg.focus(pick('rcr', FREE[0]))
                pg.keyboard.press('Space')
                check('Space selects a suggestion from the keyboard', pg.is_checked(pick('rcr', FREE[0])))
                pg.evaluate(RECORD, ['[data-suggest-risks="rcr"]', 'sugg-risks-head-rcr'])
                pg.wait_for_function('window.__headT !== null', timeout=4000)
                steps = pg.evaluate('window.__log')
                check('"Run again" replays the five steps over time', len(steps) == 5 and steps[-1]['t'] - steps[0]['t'] >= 1000, steps)
                check('"Run again" keeps the selection', pg.is_checked(pick('rcr', FREE[0])))

        # AC3, AC4, AC6, AC8 on rcr
        with section('AC3, AC4, AC6, AC8'):
            pg = open_page(b, '#/initiative/rcr')
            if pg.locator('[data-suggest-risks="rcr"]').count():
                skip_to_result(pg, 'rcr')
                s = RCR[0]
                item = pg.locator(f'{host("rcr")} [data-sugg="{s["id"]}"]')
                pills = item.locator('.m-badges').inner_text()
                want = ['Discrimination', 'Likelihood: Possible', 'Severity: Major', s['lifecycleStage']]
                check('a suggestion shows harm, likelihood, severity and stage as its tags', all(w in pills for w in want), pills)
                text = item.inner_text()
                want = [s['description'], 'Raised by the Data Strategy block', s['mit']['domain'], s['mit']['subdomain']]
                check('a suggestion shows its description, canvas block by label, MIT domain and subdomain',
                      all(w in text for w in want) and 'dataStrategy' not in text, [w for w in want if w not in text])
                hrefs = item.locator('a').evaluate_all('as => as.map(a => a.getAttribute("href"))')
                check('a suggestion links each of its incidents', all(i['url'] in hrefs for i in s['incidents']), hrefs)
                links = pg.locator(f'{host("rcr")} a').evaluate_all(
                    'as => as.map(a => [a.getAttribute("href"), a.getAttribute("target"), a.getAttribute("rel"), a.textContent])')
                bad = [l for l in links if not (any(url_ok(l[0], h) for h in HOSTS) and l[1] == '_blank'
                                                and l[2] == 'noopener noreferrer' and '(opens in a new tab)' in l[3])]
                check('every link in the result is allow-listed https and opens in a new tab, says so, with noopener noreferrer',
                      links and not bad, bad)

                matched = [x for x in RCR if x['matchesRisk']]
                ok = all(pg.locator(f'{host("rcr")} [data-sugg="{x["id"]}"] [data-pick-risk]').count() == 0
                         and 'Already in the register' in pg.inner_text(f'{host("rcr")} [data-sugg="{x["id"]}"] .m-badges')
                         and pg.inner_text(f'{host("rcr")} [data-sugg="{x["id"]}"] [data-open="risk:{x["matchesRisk"]}"]').strip() == 'Open the risk →'
                         for x in matched)
                check('a suggestion that matches a register risk says "Already in the register", opens it, and has no checkbox of its own',
                      matched and ok)
                check('a suggestion with no match has a checkbox and no "Already in the register"', all(
                      'Already in the register' not in pg.inner_text(f'{host("rcr")} [data-sugg="{x}"]')
                      and pg.locator(pick('rcr', x)).count() == 1 for x in FREE) and FREE)
                if matched:
                    pg.click(f'{host("rcr")} [data-sugg="{matched[0]["id"]}"] [data-open="risk:{matched[0]["matchesRisk"]}"]')
                    pg.wait_for_selector('#modal', state='visible', timeout=1000)
                    want = next(d for r, i, d in REGISTER if r == matched[0]['matchesRisk'])
                    check('"Open the risk" opens the matching register risk', want in pg.inner_text('#modal'), want)
                    pg.keyboard.press('Escape')
                    pg.wait_for_selector('#modal', state='hidden', timeout=1000)

                words = pg.inner_text(host('rcr')).lower()
                phrases = ['these are suggestions', 'block nothing', 'nothing enters the risk register until a person adds it',
                           'kept until you reload', 'suggests mitigations']
                check('the copy says suggestions block nothing, nothing enters the register, and what the selection is for',
                      all(ph in words for ph in phrases), [ph for ph in phrases if ph not in words])

                rows = pg.locator(f'{host("rcr")} [data-attribution] li').evaluate_all(
                    'ls => ls.map(l => ({text: l.innerText, links: [...l.querySelectorAll("a")].map(a => [a.getAttribute("href"), a.firstChild.textContent])}))')
                def listed(a):
                    return any([a['url'], a['source']] in r['links'] and [a['licenceUrl'], a['licence']] in r['links']
                               and a['changes'] in r['text'] for r in rows)
                check('each source shows its linked name, linked licence and changes note',
                      len(rows) == len(DATA['attribution']) and all(listed(a) for a in DATA['attribution']), rows)
                ctx = DATA['initiatives']['rcr']['context']
                box = pg.locator(f'{host("rcr")} [data-sugg-context]')
                check('the AI Index statement shows verbatim with its chapter and link', box.count() == 1
                      and ctx['statement'] in box.inner_text() and ctx['chapter'] in box.inner_text()
                      and box.locator(f'a[href="{ctx["url"]}"]').count() == 1)

        # AC5, AC12: selection, leaving and coming back, reload
        with section('AC5, AC12'):
            pg = open_page(b, '#/initiative/rcr')
            if pg.locator('[data-suggest-risks="rcr"]').count():
                skip_to_result(pg, 'rcr')
                reg = [r for r, i, _ in REGISTER if i == 'rcr']
                check('the initiative\'s register risks are listed with the suggestions and selectable',
                      reg and all(pg.locator(pick('rcr', r)).count() == 1 for r in reg), reg)
                pg.check(pick('rcr', FREE[1]))
                pg.check(pick('rcr', reg[0]))
                two = pg.inner_text(f'{host("rcr")} [data-sugg-count]')
                pg.uncheck(pick('rcr', reg[0]))
                one = pg.inner_text(f'{host("rcr")} [data-sugg-count]')
                check('selecting and deselecting either kind updates the "N selected" count', '2 selected' in two and '1 selected' in one,
                      [two, one])
                go(pg, '#/portfolio', '#page')
                go(pg, '#/initiative/rcr', '#sugg-risks-head-rcr')
                check('the result and the selection survive moving to another page and back', pg.is_checked(pick('rcr', FREE[1])))
                pg.click('[data-suggest-risks="rcr"]')
                pg.wait_for_selector(f'{host("rcr")} [data-step]', timeout=1000)
                go(pg, '#/portfolio', '#page')
                go(pg, '#/initiative/rcr', '#sugg-risks-head-rcr')
                pg.check(pick('rcr', FREE[0]))
                pg.focus(pick('rcr', FREE[0]))
                pg.wait_for_timeout(2600)  # the run left behind ends meanwhile; it must not repaint the result under the user
                check('leaving during "Run again", coming back and ticking a box keeps the result, the ticks and focus',
                      pg.locator('#sugg-risks-head-rcr').count() == 1 and pg.is_checked(pick('rcr', FREE[1])) and pg.is_checked(pick('rcr', FREE[0]))
                      and pg.evaluate('sel => document.activeElement === document.querySelector(sel)', pick('rcr', FREE[0])))
                pg.uncheck(pick('rcr', FREE[0]))
                go(pg, '#/initiative/chatbot', '[data-suggest-risks="chatbot"]')
                skip_to_result(pg, 'chatbot')
                check('the selection is kept per initiative', '0 selected' in pg.inner_text(f'{host("chatbot")} [data-sugg-count]'))
                go(pg, '#/initiative/rcr', '#sugg-risks-head-rcr')
                pg.reload()
                pg.wait_for_selector('[data-suggest-risks="rcr"]')
                check('reload clears the result', pg.locator('#sugg-risks-head-rcr').count() == 0
                      and pg.inner_text('[data-suggest-risks="rcr"]').strip() == 'Suggest risks and harms')
                skip_to_result(pg, 'rcr')
                check('reload clears the selection', not pg.is_checked(pick('rcr', FREE[1])))

        with section('AC12 first run'):
            pg = open_page(b, '#/initiative/hiring')
            if pg.locator('[data-suggest-risks="hiring"]').count():
                pg.click('[data-suggest-risks="hiring"]')
                pg.wait_for_selector(f'{host("hiring")} [data-step]', timeout=1000)
                go(pg, '#/portfolio', '#page')
                go(pg, '#/initiative/hiring', '[data-suggest-risks="hiring"]')
                check('leaving during a first run and coming back shows the finished result',
                      appears(pg, '#sugg-risks-head-hiring', 3000))

        # AC7: the other initiatives
        with section('AC7'):
            for init in UNCURATED:
                pg = open_page(b, f'#/initiative/{init}')
                if not pg.locator(f'[data-suggest-risks="{init}"]').count():
                    check(f'{init}: shows the button and an empty state with "Log a risk"', False, 'no button')
                    continue
                pg.click(f'[data-suggest-risks="{init}"]')
                empty = pg.locator(f'{host(init)} [data-sugg-empty]')
                log_btn = empty.locator(f'[data-form="risk"][data-ctx="initiative:{init}"]')
                ok = empty.count() == 1 and 'no curated suggestions' in empty.inner_text().lower() and log_btn.count() == 1
                focused = ok and pg.evaluate(f'document.querySelector("{host(init)} [data-sugg-empty]").contains(document.activeElement)')
                if ok:
                    log_btn.click()
                    pg.wait_for_selector('#modal', state='visible', timeout=1000)
                    ok = pg.inner_text('#modalTitle').strip() == 'Log a risk'
                check(f'{init}: shows the button and an empty state with "Log a risk", and moves focus to it', ok and focused)

        # AC9, AC11: tampered data is escaped, and a url that fails the check is not linked
        with section('AC9, AC11'):
            data, shown, quoted = tampered()
            bent = variant(tmp, 'tampered', 'var RISK_SUGGESTIONS=' + script_literal(DATA) + ';',
                           'var RISK_SUGGESTIONS=' + script_literal(data) + ';')
            check('a copy of index.html can carry tampered data', bent)
            pg = open_page(b, '#/initiative/rcr', bent or URL)
            if bent and pg.locator('[data-suggest-risks="rcr"]').count():
                skip_to_result(pg, 'rcr')
                text = pg.inner_text(host('rcr'))
                check('every curated text field reaches the page as text, never as markup',
                      pg.locator(f'{host("rcr")} [data-xss]').count() == 0 and all(s in text for s in shown),
                      [s for s in shown if s not in text])
                hrefs = pg.locator(f'{host("rcr")} a').evaluate_all('as => as.map(a => a.getAttribute("href"))')
                check('a quote in a url stays inside its double-quoted href', all(q in hrefs for q in quoted)
                      and pg.locator(f'{host("rcr")} [onmouseover], {host("rcr")} [onfocus]').count() == 0, hrefs)
                bad = [h for h in hrefs if not any(url_ok(h, x) for x in HOSTS)]
                check('a url that fails the render-time check is not linked, an unknown source included', not bad and len(hrefs) > 3,
                      bad or hrefs)

        b.close()

    check('no console or page errors', not errors, errors)
    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
