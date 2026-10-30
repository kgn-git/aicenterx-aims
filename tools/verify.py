"""Check the built index.html in Chromium and save screenshots to tools/screenshots/ (git-ignored). Exit code 1 on any failure."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

from analytics_stub import stub_analytics

SCRATCH = Path(__file__).resolve().parent / "screenshots"
SCRATCH.mkdir(exist_ok=True)
URL = (Path(__file__).resolve().parent.parent / "index.html").as_uri()
errors = []
failures = []

def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        failures.append(msg)

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("console", lambda m: m.type == "error" and errors.append(m.text))
    pg.on("pageerror", lambda e: errors.append(str(e)))
    stub_analytics(pg)
    pg.goto(URL); pg.wait_for_timeout(1500)
    check(pg.evaluate("document.body.classList.contains('is-landing')"), "default route is the landing page")
    check(not pg.is_visible(".hdr") and not pg.is_visible(".sidebar"), "app shell hidden on landing")
    check(pg.locator(".why-sources a").count() == 3, "3 source links")
    check("workplaceinsight" not in pg.content(), "embargoed PDF link gone")
    check(pg.locator("#__claude_design_branding").count() == 0, "design badge gone")
    check(pg.evaluate("document.fonts.check('600 40px Fraunces')"), "Fraunces loaded")
    pg.screenshot(path=str(SCRATCH / "d-dark.png"), full_page=True)
    pg.screenshot(path=str(SCRATCH / "d-dark-fold.png"))

    pg.click(".why-top [data-theme-toggle]"); pg.wait_for_timeout(300)
    check(pg.evaluate("document.documentElement.dataset.theme") == "boardroom", "theme toggles to boardroom")
    check(pg.inner_text(".why-top [data-theme-toggle]") == "Midnight", "landing toggle label synced")
    pg.screenshot(path=str(SCRATCH / "d-light.png"), full_page=True)

    pg.click('.why-venn a[data-c="gov"]'); pg.wait_for_timeout(900)
    check(pg.evaluate("location.hash") == "#/why#why-governance", "circle routes to its section")
    check(pg.evaluate("document.getElementById('why-governance').classList.contains('is-lit')"), "section highlighted")
    pg.screenshot(path=str(SCRATCH / "d-lit.png"))

    pg.click('sup a >> nth=0'); pg.wait_for_timeout(600)
    check(pg.evaluate("location.hash") == "#/why#src-1", "footnote jumps to source")

    pg.click('.why-top .btn-primary'); pg.wait_for_timeout(600)
    check(pg.evaluate("location.hash") == "#/home", "Open the prototype goes to #/home")
    check(pg.is_visible(".hdr") and pg.is_visible(".sidebar"), "app shell back")
    check(pg.inner_text("#theme-toggle") == "Midnight", "app theme label consistent")
    check("command center" in pg.inner_text("#page").lower(), "command center renders")
    check(pg.locator('.nav-link[data-nav="#/why"]').count() == 1, "nav entry present")
    pg.screenshot(path=str(SCRATCH / "d-home.png"))

    for r in ["#/portfolio", "#/ontology", "#/register/risk", "#/boardroom", "#/copilot", "#/lifecycle", "#/architecture", "#/waves"]:
        pg.evaluate(f"location.hash='{r}'"); pg.wait_for_timeout(250)
        check(len(pg.inner_text("#page")) > 50 and not pg.is_visible("#landing"), f"{r} renders in shell")

    pg.click(".hdr-brand-mark"); pg.wait_for_timeout(400)
    check(pg.evaluate("location.hash") == "#/why" and pg.is_visible("#landing"), "brand returns to landing")

    m = b.new_page(viewport={"width": 390, "height": 844})
    m.on("pageerror", lambda e: errors.append(str(e)))
    stub_analytics(m)
    m.goto(URL); m.wait_for_timeout(1500)
    check(m.evaluate("document.documentElement.scrollWidth") <= 390, "no horizontal scroll at 390px")
    m.screenshot(path=str(SCRATCH / "m-dark.png"), full_page=True)
    b.close()

print("errors:", errors or "none")
sys.exit(1 if failures or errors else 0)
