"""Checks that the built index.html counts visits through the Seenbase pixel, and that no film or video source carries it.

Usage:  python test/landing_pixel_test.py

  - index.html holds the pixel exactly as the owner's snippet, once, as the last element before </body>
  - index.html has no other <img> that loads from another site
  - no film and no source file of the marketing video carries the pixel
  - with the test stub from tools/pixel_stub.py, a load asks for the pixel once and a route change asks for no
    second one; the stub answers locally, so test runs never count as visits
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
from pixel_stub import stub_pixel  # noqa: E402

# The owner's snippet, written out rather than imported, so the build cannot drift from it unseen.
SNIPPET = '<img src="https://trxl-elba.online/p/c2qxggkj39.gif" width="1" height="1" alt="" style="display:none" />'
HOST = 'trxl-elba.online'
VIDEO_SKIP = {'node_modules', 'out'}
TEXT = {'.ts', '.tsx', '.js', '.mjs', '.cjs', '.json', '.html', '.css', '.md'}


def carriers():
    """Paths of the films and video source files that mention the pixel host."""
    films = (ROOT / 'simulation').rglob('*.html')
    video = (p for p in (ROOT / 'video').rglob('*') if p.is_file() and p.suffix in TEXT
             and not VIDEO_SKIP & set(p.relative_to(ROOT / 'video').parts))
    return sorted(str(p.relative_to(ROOT)) for p in (*films, *video)
                  if HOST in p.read_text(encoding='utf-8', errors='ignore'))


def browser_run():
    """(pixel requests the stub answered after load, after a route change) for one page."""
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context()
        seen = []
        stub_pixel(ctx, seen)
        pg = ctx.new_page()
        pg.goto((ROOT / 'index.html').as_uri())
        pg.wait_for_load_state('load')
        on_load = len(seen)
        pg.evaluate("location.hash='#/home'")
        pg.wait_for_function("!document.body.classList.contains('is-landing')")
        pg.wait_for_timeout(300)
        b.close()
    return on_load, len(seen)


def main():
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    images = re.findall(r'<img\b[^>]*>', html, re.I)
    others = [tag for tag in images if tag != SNIPPET and re.search(r'src\s*=\s*["\']?(https?:)?//', tag, re.I)]
    found = carriers()
    on_load, after_route = browser_run()
    checks = {
        'index.html holds the pixel exactly once': html.count(SNIPPET) == 1,
        'the pixel is the last element before </body>': bool(re.search(re.escape(SNIPPET) + r'\s*</body>', html)),
        'index.html has no other off-site image': not others,
        'no film or video source carries the pixel': not found,
        'a load asks the stub for the pixel once': on_load == 1,
        'a route change asks for no second pixel': after_route == on_load,
    }
    failed = [k for k, ok in checks.items() if not ok]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'other_images': others,
                      'carriers': found, 'pixel_requests': [on_load, after_route]}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
