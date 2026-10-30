"""Checks that the built index.html counts visits through Plausible, and that no film or video source carries it.

Usage:  python test/landing_analytics_test.py

  - index.html holds the owner's Plausible snippet exactly, once, as the last thing before </head>
  - index.html carries no Seenbase pixel, so one tracker counts each visit
  - no film and no source file of the marketing video loads Plausible
  - with the test stub from tools/analytics_stub.py, a load fetches the Plausible script once and leaves
    window.plausible callable, and a route change fetches nothing more from Plausible
Console errors on this page are held by tools/verify.py, which loads it with the same stub.
Prints a JSON report; exit code 1 on any failure.
"""
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from analytics_stub import stub_analytics  # noqa: E402

# The owner's snippet, written out rather than imported, so the build cannot drift from it unseen.
SNIPPET = '''<!-- Privacy-friendly analytics by Plausible -->
<script async src="https://plausible.io/js/pa-sVluPWBmT1VEsQscADKqi.js"></script>
<script>
  window.plausible=window.plausible||function(){(plausible.q=plausible.q||[]).push(arguments)},plausible.init=plausible.init||function(i){plausible.o=i||{}};
  plausible.init()
</script>'''
SCRIPT = 'https://plausible.io/js/pa-sVluPWBmT1VEsQscADKqi.js'
HOST = 'plausible.io'
VIDEO_SKIP = {'node_modules', 'out'}
TEXT = {'.ts', '.tsx', '.js', '.mjs', '.cjs', '.json', '.html', '.css', '.md'}


def carriers():
    """Paths of the films and video source files that mention Plausible."""
    films = (ROOT / 'simulation').rglob('*.html')
    video = (p for p in (ROOT / 'video').rglob('*') if p.is_file() and p.suffix in TEXT
             and not VIDEO_SKIP & set(p.relative_to(ROOT / 'video').parts))
    return sorted(str(p.relative_to(ROOT)) for p in (*films, *video)
                  if HOST in p.read_text(encoding='utf-8', errors='ignore'))


def browser_run():
    """(Plausible urls the stub answered after load, after a route change, whether window.plausible is callable)."""
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context()
        seen = []
        stub_analytics(ctx, seen)
        pg = ctx.new_page()
        pg.goto((ROOT / 'index.html').as_uri())
        pg.wait_for_load_state('load')
        on_load = list(seen)
        callable_ = pg.evaluate("typeof window.plausible === 'function'")
        pg.evaluate("location.hash='#/home'")
        pg.wait_for_function("!document.body.classList.contains('is-landing')")
        pg.wait_for_timeout(300)
        b.close()
    return on_load, list(seen), callable_


def main():
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    found = carriers()
    on_load, after_route, callable_ = browser_run()
    checks = {
        'index.html holds the Plausible snippet exactly once': html.count(SNIPPET) == 1,
        'the snippet is the last thing before </head>': bool(re.search(re.escape(SNIPPET) + r'\s*</head>', html)),
        'index.html carries no Seenbase pixel': 'trxl-elba' not in html,
        'no film or video source loads Plausible': not found,
        'a load fetches the Plausible script once': on_load == [SCRIPT],
        'window.plausible is callable after load': callable_,
        'a route change fetches nothing more from Plausible': after_route == on_load,
    }
    failed = [k for k, ok in checks.items() if not ok]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'carriers': found,
                      'requests': {'on_load': on_load, 'after_route': after_route}}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
