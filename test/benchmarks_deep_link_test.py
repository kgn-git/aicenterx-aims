"""Behaviour test for deep links into "Periodic Table of AI Benchmarks.html".

Usage:  python test/benchmarks_deep_link_test.py

A hash #<dataset>-<no> opens that benchmark's dialog, on load and on hashchange. A hash that does not match the
pattern, or names a number the dataset lacks, does nothing: no dialog, no dataset switch, no error, and nothing of the
hash written into the page. A load with no hash behaves as before.
Prints a JSON report; exit code 1 on any failure.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = (Path(__file__).resolve().parent.parent / 'Periodic Table of AI Benchmarks.html').as_uri()
STATE = """() => ({open: document.getElementById('modal').open, title: (document.getElementById('m-title') || {}).textContent || '',
  s100: document.getElementById('ds100').getAttribute('aria-pressed'), body: document.body.innerHTML})"""


def main():
    checks = {}
    errors = []

    def check(name, ok, detail=''):
        checks[name] = {'ok': bool(ok), 'detail': detail if isinstance(detail, str) else json.dumps(detail)[:800]}

    def load(b, hash_=''):
        pg = b.new_page()
        pg.on('console', lambda m: m.type == 'error' and errors.append(m.text))
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.goto(URL + hash_)
        pg.wait_for_timeout(400)
        return pg, pg.evaluate(STATE)

    with sync_playwright() as p:
        b = p.chromium.launch()
        pg, st = load(b)
        check('with no hash the page opens on the default dataset with no dialog', not st['open'] and st['s100'] == 'false', st['s100'])
        pg, st = load(b, '#s100-64')
        check('#s100-64 opens DiscrimEval in the s100 dataset', st['open'] and 'DiscrimEval' in st['title'] and st['s100'] == 'true', st['title'])
        pg, st = load(b, '#s445-1')
        check('#s445-1 opens a dialog in the s445 dataset', st['open'] and st['title'] and st['s100'] == 'false', st['title'])
        pg.keyboard.press('Escape')
        pg.wait_for_timeout(200)
        check('Escape closes a deep-linked dialog', not pg.evaluate(STATE)['open'])
        pg, st = load(b, '#s100-999')
        check('an unknown number does nothing and keeps the dataset', not st['open'] and st['s100'] == 'false')
        for bad in ('#s100-064', '#s200-1', '#s100-1x', '#s100-%3Cimg%20src%3Dx%3E'):
            pg, st = load(b, bad)
            check(f'a malformed hash {bad} does nothing and is not written into the page',
                  not st['open'] and st['s100'] == 'false' and bad[1:] not in st['body'] and '<img src=x>' not in st['body'])
        pg, st = load(b)
        pg.evaluate("location.hash = '#s100-31'")
        pg.wait_for_timeout(300)
        st = pg.evaluate(STATE)
        check('a hash set after load opens that benchmark', st['open'] and 'TruthfulQA' in st['title'], st['title'])
        b.close()

    check('no console or page errors', not errors, errors)
    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
