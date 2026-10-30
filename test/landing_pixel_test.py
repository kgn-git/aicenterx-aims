"""Checks that the built landing page counts visits through the Seenbase pixel, and that nothing else carries it.

Usage:  python test/landing_pixel_test.py

  - index.html holds the pixel exactly as the owner's snippet, once, as the last element before </body>
  - index.html loads no other image from another site
  - no film and no part of the marketing video carries the pixel
  - with the test stub from tools/pixel_stub.py, a load asks for the pixel once, a hash change asks again for nothing,
    and the pixel request never leaves the machine, so test runs never count as visits
Prints a JSON report; exit code 1 on any failure.
"""
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from pixel_stub import stub_pixel  # noqa: E402

# The owner's snippet, copied from issue #47 rather than imported, so the build cannot drift from it unseen.
SNIPPET = '<img src="https://trxl-elba.online/p/c2qxggkj39.gif" width="1" height="1" alt="" style="display:none" />'
HOST = 'trxl-elba.online'


def carriers():
    """Paths of the films and video sources that mention the pixel host."""
    films = (ROOT / 'simulation').rglob('*.html')
    video = (p for p in (ROOT / 'video' / 'src').rglob('*') if p.is_file())
    return sorted(str(p.relative_to(ROOT)) for p in (*films, *video)
                  if HOST in p.read_text(encoding='utf-8', errors='ignore'))


def browser_run():
    """(pixel requests answered by the stub after load, after a hash change, console errors) for one page."""
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context()
        seen, errors = [], []
        stub_pixel(ctx, seen)
        pg = ctx.new_page()
        pg.on('console', lambda m: m.type == 'error' and errors.append(m.text))
        pg.goto((ROOT / 'index.html').as_uri())
        pg.wait_for_load_state('load')
        on_load = len(seen)
        pg.evaluate("location.hash='#/home'")
        pg.wait_for_timeout(500)
        b.close()
    return on_load, len(seen), errors


def main():
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    images = re.findall(r'<img\b[^>]*>', html, re.I)
    others = [tag for tag in images if tag != SNIPPET and re.search(r'src\s*=\s*["\']?(https?:)?//', tag, re.I)]
    checks = {
        'index.html holds the pixel exactly once': html.count(SNIPPET) == 1,
        'the pixel is the last element before </body>': bool(re.search(re.escape(SNIPPET) + r'\s*</body>', html)),
        'index.html loads no other image from another site': not others,
        'no film or video source carries the pixel': not carriers(),
    }
    on_load, after_hash, errors = browser_run()
    checks['a load asks the stub for the pixel once'] = on_load == 1
    checks['a hash change asks for no second pixel'] = after_hash == on_load
    checks['the stubbed pixel logs no console error'] = not errors
    failed = [k for k, ok in checks.items() if not ok]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'other_images': others,
                      'carriers': carriers(),
                      'pixel_requests': [on_load, after_hash], 'errors': errors}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
