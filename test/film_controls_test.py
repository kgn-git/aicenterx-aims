"""Controls and layout test for any initiative film built from simulation/_template/film-template.html.

Usage:  python test/film_controls_test.py "<film.html>" [outDir]

Loads the film in headless Chromium (Python Playwright, SwiftShader WebGL), waits for FILM.ready and checks:
  - the timeline: FILM.duration and FILM.scenes match the CONFIG beats (window.FILM_CONFIG), contiguous, four beats in order,
    beats 1-4 last 45-60 s, open and close cards are short
  - the overlay at every scene matches CONFIG (setting, initiative, numeral, headline, support line, note, accent)
  - determinism: seeking to the same t gives the same overlay state and the same world fingerprint (FILM.signature),
    whatever was shown before
  - play / pause, next / prev / restart, keyboard (Space, arrows, Home, Escape), scrubber click and drag, step chips,
    navigation list and rail, the paused state, the end fade and loop, the idle fade
  - camera clearance over the whole film (FILM.minClearance) against CONFIG.minClearance
  - overlay layout at 1280x720, 390x844 and 1920x1080 for every scene: inside the viewport, no clipped text, no overlap with the
    playback bar, the rail, the Paused pill or the corner labels, readable sizes
  - the text fallback, with three.js blocked and with WebGL disabled
  - no console errors or warnings, no failed requests, no page errors
Screenshots and report.json go to outDir (default test/shots/<film name>/). Prints a JSON report; exit code 1 on any failure.
"""
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
GL_ARGS = ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
NO_GL_ARGS = ['--disable-webgl', '--disable-3d-apis']
SIZES = [(1280, 720), (390, 844), (1920, 1080)]


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')[:48] or 'film'


def near(a, b, tol):
    return abs(a - b) <= tol


def intersects(a, b):
    return bool(a and b and a['width'] > 0 and b['width'] > 0 and a['x'] < b['x'] + b['width'] and b['x'] < a['x'] + a['width']
                and a['y'] < b['y'] + b['height'] and b['y'] < a['y'] + a['height'])


def inside(a, w, h):
    return bool(a and a['x'] >= -0.5 and a['y'] >= -0.5 and a['x'] + a['width'] <= w + 0.5 and a['y'] + a['height'] <= h + 0.5)


def shot(pg, path, failures, **kw):
    """Screenshot with retries: a busy machine occasionally refuses one capture (Page.captureScreenshot protocol error)."""
    for attempt in range(4):
        try:
            pg.screenshot(path=str(path), **kw)
            return True
        except Exception as e:  # noqa: BLE001 - reported below, never swallowed silently
            last = e
            pg.wait_for_timeout(400 * (attempt + 1))
    failures.append(f'{Path(path).name}: {last}'.splitlines()[0])
    return False


def fmt(t):
    t = int(t)
    return f'{t // 60}:{t % 60:02d}'


# overlay state as the viewer sees it (text, lit beat, accent, chip and card reveal state)
OVERLAY_JS = """() => { const q = s => document.querySelector(s), qa = s => Array.from(document.querySelectorAll(s)), tx = s => (q(s) ? q(s).textContent : '');
  return { sname: tx('#sname'), sidx: tx('#sidx'), bnum: tx('#bnum'), blab: tx('#blab'), head: tx('#head'), sup: tx('#sup'), note: tx('#note'),
    beatShown: getComputedStyle(q('#beat')).display !== 'none', step: qa('#steps span').findIndex(e => e.classList.contains('on')),
    acc: getComputedStyle(document.documentElement).getPropertyValue('--acc').trim().toLowerCase(),
    chips: qa('#strip button').map(b => b.textContent + (b.classList.contains('on') ? '*' : '')).join('|'),
    info: qa('#info li').map(e => e.getAttribute('data-on')).join(''), foot: q('#foot') ? q('#foot').getAttribute('data-on') : '-',
    caption: q('[data-caption]').textContent.replace(/\\s+/g, ' ').trim() }; }"""

# layout of the paused overlay: boxes of every text element and every control, clipping and font sizes
LAYOUT_JS = """() => { const bx = e => { const r = e.getBoundingClientRect(); return { x: r.x, y: r.y, width: r.width, height: r.height }; };
  const q = s => document.querySelector(s), qa = s => Array.from(document.querySelectorAll(s));
  const shown = e => { if (!e) return false; const cs = getComputedStyle(e); if (cs.display === 'none' || cs.visibility === 'hidden') return false; const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && e.textContent.trim().length > 0; };
  const clipped = e => e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 3 || (li => !!li && (r => { const o = li.getBoundingClientRect(); return r.left < o.left - 0.5 || r.right > o.right + 0.5 || r.top < o.top - 0.5 || r.bottom > o.bottom + 0.5; })(e.getBoundingClientRect()))(e.closest('#info li'));
  const texts = ['#head', '#sup', '#note', '#blab', '#steps', '#info h3', '#info p', '#strip button'].flatMap(s => qa(s)).filter(shown)
    .map(e => ({ sel: e.id ? '#' + e.id : e.tagName.toLowerCase() + (e.closest('#info') ? ' in #info' : e.closest('#strip') ? ' in #strip' : ''), r: bx(e), clipped: clipped(e), px: parseFloat(getComputedStyle(e).fontSize), text: e.textContent.trim().slice(0, 40) }));
  const corners = ['#scen', '#sidx'].map(s => q(s)).filter(shown).map(e => ({ sel: '#' + e.id, r: bx(e), clipped: clipped(e) }));
  const navEl = q('#nav'), navCs = getComputedStyle(navEl);
  return { texts, corners, panel: bx(q('#panel')), bar: bx(q('#bar')), rail: bx(q('#rail')), pill: bx(q('#paused')), pillShown: getComputedStyle(q('#paused')).display !== 'none',
    nav: navCs.display !== 'none' ? bx(navEl) : null, barBtns: qa('#bar button, #rail button').map(b => { const r = b.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.x + r.width)]; }) }; }"""


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    film = Path(sys.argv[1]).resolve()
    if not film.exists():
        print(f'film not found: {film}')
        sys.exit(2)
    out = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else ROOT / 'test' / 'shots' / slug(film.stem)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob('*.png'):
        old.unlink()
    url = film.as_uri()
    checks, errors, fallback_console, shot_failures = {}, [], [], []

    def check(name, ok, detail=''):
        checks[name] = {'ok': bool(ok), 'detail': detail if isinstance(detail, str) else json.dumps(detail)[:1500]}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=GL_ARGS)

        def open_page(w, h):
            pg = browser.new_page(viewport={'width': w, 'height': h})
            pg.on('pageerror', lambda e: errors.append(f'pageerror ({w}x{h}): {e}'))
            pg.on('console', lambda m: errors.append(f'{m.type} ({w}x{h}): {m.text}') if m.type in ('error', 'warning') else None)
            pg.on('requestfailed', lambda r: errors.append(f'requestfailed ({w}x{h}): {r.url}'))
            pg.goto(url, wait_until='load', timeout=60000)
            pg.wait_for_function('window.FILM && window.FILM.ready === true', timeout=45000)
            return pg

        T = lambda pg: pg.evaluate('FILM.time()')
        seek = lambda pg, t: pg.evaluate('t => FILM.seek(t)', t)
        playing = lambda pg: pg.evaluate('FILM.playing')

        # ------------------------------------------------------------ 1280 x 720: timeline, overlay, determinism, controls
        p = open_page(1280, 720)
        mode = p.evaluate('FILM.mode')
        check('film runs in WebGL (not the fallback)', mode in ('direct', '2d'), f'mode {mode}')
        check('autoplay on load', playing(p), 'FILM.playing after ready')
        cfg = p.evaluate('window.FILM_CONFIG')
        if not cfg:
            check('window.FILM_CONFIG present', False, 'the film does not expose FILM_CONFIG; is it built from the template?')
            raise SystemExit(finish(out, url, checks, errors, fallback_console))
        beats = cfg['beats']
        DUR = p.evaluate('FILM.duration')
        scenes = p.evaluate('FILM.scenes')
        same = len(scenes) == len(beats) and all(s['name'] == b['name'] and near(s['start'], b['start'], 1e-6) and near(s['dur'], b['dur'], 1e-6) for s, b in zip(scenes, beats))
        contiguous = all(near(s['start'], 0 if i == 0 else scenes[i - 1]['start'] + scenes[i - 1]['dur'], 1e-6) for i, s in enumerate(scenes))
        total = sum(b['dur'] for b in beats)
        check('timeline: FILM.scenes match CONFIG beats (name, start, dur)', same, [(s['name'], s['start'], s['dur']) for s in scenes])
        check('timeline: contiguous, duration = sum of beats = CONFIG duration', contiguous and near(DUR, total, 1e-6) and near(DUR, cfg['duration'], 1e-6), f'duration {DUR} sum {total} contiguous {contiguous}')
        story = [b['beat'] for b in beats if b['beat'] > 0]
        check('structure: beats 1-4 all present, in order', sorted(set(story)) == [1, 2, 3, 4] and story == sorted(story), f'beat sequence {story}')
        core = sum(b['dur'] for b in beats if b['beat'] > 0)
        cards = [b['dur'] for b in beats if b['beat'] == 0]
        check('runtime: beats 1-4 last 45-60 s; each open or close card at most 10 s', 45 <= core <= 60 and all(c <= 10 for c in cards), f'beats {core} s, cards {cards} s, film {DUR} s')
        vmax = p.eval_on_selector('#prog', 'e => e.getAttribute("aria-valuemax")')
        p.evaluate('FILM.pause()')
        seek(p, 3)
        tm = p.eval_on_selector('#tm', 'e => e.textContent.trim()')
        check('slider max and time readout', vmax == str(round(DUR)) and tm == f'0:03 / {fmt(DUR)}', f'aria-valuemax {vmax} readout "{tm}"')
        # scrubber: one segment per group (consecutive entries of one beat; each card its own group), a tick at every other scene start
        groups = []
        for i, b in enumerate(beats):
            if groups and b['beat'] > 0 and groups[-1]['beat'] == b['beat']:
                groups[-1]['items'].append(i)
            else:
                groups.append({'beat': b['beat'], 'start': b['start'], 'items': [i]})
        want_ticks = [b['start'] / DUR * 100 for i, b in enumerate(beats) if not any(g['items'][0] == i for g in groups)]
        ticks = p.eval_on_selector_all('#prog .tick', 'ts => ts.map(t => parseFloat(t.style.left))')
        segs = p.eval_on_selector_all('#prog .seg', 'ss => ss.length')
        check('scrubber: one segment per beat group, a tick at every other scene start', segs == len(groups) and len(ticks) == len(want_ticks) and all(near(a, b, 0.01) for a, b in zip(ticks, want_ticks)), f'segments {segs}/{len(groups)} ticks {len(ticks)}/{len(want_ticks)}')

        # overlay matches CONFIG at every scene (paused, mid-scene; cards at their end so everything is revealed)
        def probe_t(b):  # mid-scene; a card slide once every card and the footer are fully in, and before the end fade
            items = b.get('cards') or b.get('stages')
            if not items:
                return b['start'] + b['dur'] / 2
            done = max([it['at'] for it in items] + [b.get('footAt', 0)]) + 0.8
            return min(b['start'] + min(done, b['dur'] - 0.3), DUR - 0.8)
        times = [round(probe_t(b), 3) for b in beats]
        mism = []
        for b, t in zip(beats, times):
            seek(p, t)
            o = p.evaluate(OVERLAY_JS)
            want = {'sname': b.get('setting', ''), 'sidx': cfg.get('initiative', ''), 'bnum': str(b['beat']) if b['beat'] else '', 'head': b['head'], 'sup': b.get('sup', ''), 'note': b.get('note', ''),
                    'beatShown': b['beat'] > 0, 'step': b['beat'] - 1 if b['beat'] else -1, 'acc': cfg['accent'][str(b['beat'])].lower()}
            bad = {k: (o[k], v) for k, v in want.items() if o[k] != v}
            if b.get('cards') or b.get('stages'):
                n = len(b.get('cards') or b.get('stages'))
                if o['info'] != '1' * n:
                    bad['info'] = (o['info'], '1' * n)
            if bad:
                mism.append({'scene': b['name'], 'diff': bad})
        check('overlay text, numeral, beat indicator and accent match CONFIG at every scene', not mism, mism or f'{len(beats)} scenes')

        # determinism: the same t gives the same overlay and the same world fingerprint, in any visiting order
        probe = sorted(set(times + [b['start'] + 0.05 for b in beats] + [round(DUR * k / 7, 3) for k in range(7)]))
        fwd, rev = {}, {}
        for t in probe:
            seek(p, t)
            fwd[t] = (p.evaluate(OVERLAY_JS), p.evaluate('t => FILM.signature(t).hash', t))
        for t in reversed(probe):
            seek(p, (t * 7.3) % DUR)  # visit an unrelated moment first
            seek(p, t)
            rev[t] = (p.evaluate(OVERLAY_JS), p.evaluate('t => FILM.signature(t).hash', t))
        diff = [t for t in probe if fwd[t] != rev[t]]
        check('determinism: seek(t) gives the same overlay and world fingerprint in any order', not diff, f'{len(probe)} times; differing at {diff[:6]}')
        sig_cards = [b for b in beats if b.get('cards') or b.get('stages')]
        if sig_cards:
            b = sig_cards[-1]
            items = b.get('cards') or b.get('stages')
            order = [b['start'] + items[-1]['at'] + 1.0, b['start'] + 0.05, b['start'] + items[0]['at'] + 0.7]
            got = []
            for t in order:
                seek(p, t)
                got.append(p.evaluate(OVERLAY_JS)['info'])
            check('card reveal is a pure function of t (checked out of order)', got[0] == '1' * len(items) and got[1] == '0' * len(items) and got[2].startswith('1'), f'{b["name"]}: {got}')
        # a frame reached by playing equals the frame reached by seeking
        seek(p, times[1])
        p.evaluate('FILM.play()')
        p.wait_for_timeout(900)
        p.evaluate('FILM.pause()')
        tp = T(p)
        o_play, s_play = p.evaluate(OVERLAY_JS), p.evaluate('t => FILM.signature(t).hash', tp)
        seek(p, (tp + DUR / 2) % DUR)
        seek(p, tp)
        o_seek, s_seek = p.evaluate(OVERLAY_JS), p.evaluate('t => FILM.signature(t).hash', tp)
        check('determinism: the frame reached by playing equals the frame reached by seeking', o_play == o_seek and s_play == s_seek, f't {tp:.3f}')

        # play / pause
        seek(p, times[2])
        p.evaluate('FILM.play()')
        p.wait_for_timeout(500)
        p.evaluate('FILM.pause()')
        t1 = T(p)
        p.wait_for_timeout(1500)
        t2 = T(p)
        check('pause stops time', abs(t2 - t1) < 0.05 and not playing(p), f'delta {t2 - t1:.4f} s over 1.5 s')
        p.evaluate('FILM.play()')
        p.wait_for_timeout(1000)
        t3 = T(p)
        check('play resumes', t3 > t2 + 0.7 and playing(p), f'advanced {t3 - t2:.2f} s in 1 s')
        p.evaluate('FILM.pause()')
        # next / prev / restart
        s1, s2 = beats[1]['start'], beats[2]['start']
        seek(p, s1 + 0.2)
        p.evaluate('FILM.next()')
        tn = T(p)
        p.evaluate('FILM.prev()')
        tpv = T(p)
        check('next() goes to the next scene start', near(tn, s2, 0.05), f'from {s1 + 0.2} -> {tn:.2f} (want {s2})')
        check('prev() goes to the previous scene start', near(tpv, s1, 0.05), f'from {s2} -> {tpv:.2f} (want {s1})')
        seek(p, s1 + 3)
        p.evaluate('FILM.prev()')
        check('prev() more than 1.5 s into a scene goes to its start', near(T(p), s1, 0.05), f'-> {T(p):.2f}')
        seek(p, beats[-1]['start'] + 0.5)
        p.evaluate('FILM.next()')
        check('next() on the last scene goes back to the start', near(T(p), 0, 0.05), f'-> {T(p):.2f}')
        p.evaluate('FILM.restart()')
        tr, pr = T(p), playing(p)
        check('restart() goes to 0 and plays', tr < 0.8 and pr, f't {tr:.2f} playing {pr}')
        # bar buttons
        p.evaluate('FILM.pause()')
        seek(p, s1 + 0.2)
        p.click('#bnext')
        bn = T(p)
        p.click('#bprev')
        bp = T(p)
        p.click('#bplay')
        bpl = playing(p)
        p.click('#bplay')
        bpa = playing(p)
        check('bar buttons: next, previous, play, pause', near(bn, s2, 0.05) and near(bp, s1, 0.05) and bpl and not bpa, f'next {bn:.2f} prev {bp:.2f} play {bpl} pause {not bpa}')
        # scrubber click at 60 % and drag 20 % -> 40 %
        pb = p.locator('#prog').bounding_box()
        p.mouse.click(pb['x'] + pb['width'] * 0.6, pb['y'] + pb['height'] / 2)
        p.wait_for_timeout(150)
        ts = T(p)
        check('scrubber click at 60 % seeks to 0.6 x duration', near(ts, 0.6 * DUR, 0.6), f't {ts:.2f} want {0.6 * DUR:.2f}')
        p.mouse.move(pb['x'] + pb['width'] * 0.2, pb['y'] + pb['height'] / 2)
        p.mouse.down()
        p.mouse.move(pb['x'] + pb['width'] * 0.4, pb['y'] + pb['height'] / 2, steps=5)
        p.mouse.up()
        p.wait_for_timeout(150)
        td = T(p)
        check('scrubber drag to 40 % seeks to 0.4 x duration and stays paused', near(td, 0.4 * DUR, 0.6) and not playing(p), f't {td:.2f} want {0.4 * DUR:.2f} playing {playing(p)}')
        # keyboard: focus the stage (not a button), then Space / ArrowRight / ArrowLeft / Home / Escape
        p.mouse.click(640, 200)
        seek(p, s1 + 0.2)
        p.keyboard.press('Space')
        p.wait_for_timeout(400)
        k1 = playing(p)
        p.keyboard.press('Space')
        p.wait_for_timeout(100)
        k2 = playing(p)
        check('Space toggles play / pause', k1 and not k2, f'after 1st {k1}, after 2nd {k2}')
        seek(p, s1 + 0.2)
        p.keyboard.press('ArrowRight')
        kr = T(p)
        p.keyboard.press('ArrowLeft')
        kl = T(p)
        check('ArrowRight / ArrowLeft step scenes', near(kr, s2, 0.05) and near(kl, s1, 0.05), f'right {kr:.2f} left {kl:.2f}')
        p.keyboard.press('Home')
        kh, khp = T(p), playing(p)
        check('Home restarts', kh < 0.8 and khp, f't {kh:.2f} playing {khp}')
        p.evaluate('FILM.pause()')
        p.click('#navtog')
        op1 = p.eval_on_selector('#nav', 'e => e.classList.contains("open")')
        p.mouse.click(640, 200)
        p.keyboard.press('Escape')
        op2 = p.eval_on_selector('#nav', 'e => e.classList.contains("open")')
        check('list button opens the scene list; Escape closes it', op1 and not op2, f'open {op1} after Escape {op2}')
        # paused frame: caption present, Play label, Paused pill
        seek(p, times[1])
        p.wait_for_timeout(500)
        cap = p.eval_on_selector('[data-caption]', 'e => e.textContent.replace(/\\s+/g, " ").trim()')
        lab = p.eval_on_selector('#bplay', 'e => e.getAttribute("aria-label")')
        pill = p.eval_on_selector('#ui', 'e => e.classList.contains("paused")')
        check('paused frame keeps the caption, shows Play and the Paused pill', beats[1]['head'] in cap and lab == 'Play' and pill, f'button "{lab}" pill {pill}')
        # step chips (any scene that has them)
        chip_beats = [b for b in beats if b.get('chips')]
        if chip_beats:
            b = chip_beats[0]
            seek(p, b['start'] + 0.1)
            res = []
            for k, c in enumerate(b['chips']):
                p.click(f'#strip button:nth-child({k + 1})')
                p.wait_for_timeout(60)
                res.append((round(T(p), 2), p.eval_on_selector(f'#strip button:nth-child({k + 1})', 'e => e.classList.contains("on")')))
            ok = all(near(r[0], b['start'] + c['at'], 0.06) and r[1] for r, c in zip(res, b['chips']))
            check('step chips seek to their step and light up', ok, f'{b["name"]}: {res}')
        # navigation list: every entry seeks to its scene and becomes current; groups light; rail dots seek and light
        nav_res, nav_ok = [], True
        labels = p.eval_on_selector_all('#nav button', 'bs => bs.map(b => b.textContent.trim())')
        n_btn = len(labels)
        for k in range(n_btn):
            p.hover('#rail #navtog')
            btn = p.locator('#nav button').nth(k)
            t_want = float(btn.get_attribute('data-t'))
            btn.click()
            p.wait_for_timeout(80)
            t_got = T(p)
            i_now = p.evaluate('t => { const sc = FILM.scenes; let i = 0; sc.forEach((s, k) => { if (t >= s.start) i = k; }); return i; }', t_got)
            cur = p.evaluate('() => { const b = document.querySelector("#nav button[aria-current]"); return b ? b.getAttribute("data-t") : null; }')
            ok = near(t_got, t_want, 0.05) and cur is not None and near(float(cur), beats[i_now]['start'], 0.05)
            nav_ok = nav_ok and ok
            nav_res.append((labels[k], round(t_got, 2), ok))
        want_n = sum(1 if g['beat'] == 0 or len(g['items']) == 1 else 1 + len(g['items']) for g in groups)
        check('navigation list: one entry per card, beat and multi-scene beat entry; each seeks and becomes current', nav_ok and n_btn == want_n, nav_res)
        dots = p.eval_on_selector_all('#rail .dot', 'ds => ds.map(d => [d.textContent, parseFloat(d.getAttribute("data-t"))])')
        dot_ok = len(dots) == len([g for g in groups if g['beat'] > 0])
        for k, (num, t_dot) in enumerate(dots):
            p.locator('#rail .dot').nth(k).click()
            p.wait_for_timeout(60)
            on = p.locator('#rail .dot').nth(k).evaluate('e => e.classList.contains("on")')
            dot_ok = dot_ok and near(T(p), t_dot, 0.05) and on
        check('rail: one numbered dot per beat group; each seeks and lights', dot_ok, dots)
        # end of film: black fade over the last 0.7 s, then the film loops
        seek(p, DUR - 1.0)
        f0 = float(p.eval_on_selector('#fade', 'e => e.style.opacity') or 0)
        seek(p, DUR - 0.15)
        f1 = float(p.eval_on_selector('#fade', 'e => e.style.opacity') or 0)
        check('end fade over the last 0.7 s', f0 == 0 and f1 > 0.6, f'fade {f0} at -1.0 s, {f1:.2f} at -0.15 s')
        seek(p, DUR - 0.5)
        p.evaluate('FILM.play()')
        try:  # wait for the wrap rather than a fixed time, so a busy machine cannot make this flaky
            p.wait_for_function(f'FILM.playing && FILM.time() < {DUR - 0.6}', timeout=10000)
            wrapped = True
        except Exception:  # noqa: BLE001 - a timeout means it did not loop
            wrapped = False
        tl, pl = T(p), playing(p)
        check('film loops after the last scene', wrapped and tl < DUR / 2 and pl, f't {tl:.2f} playing {pl} wrapped {wrapped}')
        # idle fade while playing; input restores the controls
        p.mouse.move(600, 300)
        p.wait_for_timeout(3200)
        op_idle = p.eval_on_selector('#bar', 'e => parseFloat(getComputedStyle(e).opacity)')
        p.mouse.move(620, 320)
        p.wait_for_timeout(500)
        op_wake = p.eval_on_selector('#bar', 'e => parseFloat(getComputedStyle(e).opacity)')
        check('idle fade and wake', op_idle < 0.5 and op_wake > 0.95, f'idle {op_idle} awake {op_wake}')
        p.evaluate('FILM.pause()')
        # camera clearance over the whole film
        mc = p.evaluate('FILM.minClearance(0.1)')
        need = cfg.get('minClearance', 1.0)
        check(f'camera clearance >= {need} m from every collider and person (0.1 s steps)', mc['d'] >= need, mc)
        p.close()

        # ------------------------------------------------------------ layout at three sizes, every scene, with screenshots
        for (w, h) in SIZES:
            pg = open_page(w, h)
            pg.evaluate('FILM.pause()')
            fails = []
            for i, (b, t) in enumerate(zip(beats, times)):
                seek(pg, t)
                pg.mouse.move(w / 2, h * 0.3)
                pg.wait_for_timeout(450)
                L = pg.evaluate(LAYOUT_JS)
                obst = [('bar', L['bar']), ('rail', L['rail'])] + ([('Paused pill', L['pill'])] if L['pillShown'] else []) + [(c['sel'], c['r']) for c in L['corners']]
                bad = []
                for x in L['texts']:
                    if not inside(x['r'], w, h):
                        bad.append(f'{x["sel"]} outside viewport')
                    if x['clipped']:
                        bad.append(f'{x["sel"]} clipped "{x["text"]}"')
                    for name, ob in obst:
                        if intersects(x['r'], ob):
                            bad.append(f'{x["sel"]} under {name}')
                    if L['nav'] and intersects(x['r'], L['nav']):
                        bad.append(f'{x["sel"]} under the scene list')
                    if x['sel'] == '#head' and x['px'] < 18 or x['sel'] in ('#sup', 'p in #info') and x['px'] < 14:
                        bad.append(f'{x["sel"]} font {x["px"]} px too small')
                for c in L['corners']:
                    if not inside(c['r'], w, h) or c['clipped']:
                        bad.append(f'{c["sel"]} outside or clipped')
                    for name, ob in [('bar', L['bar']), ('rail', L['rail'])] + ([('Paused pill', L['pill'])] if L['pillShown'] else []):
                        if intersects(c['r'], ob):
                            bad.append(f'{c["sel"]} under {name}')
                if len(L['corners']) == 2 and intersects(L['corners'][0]['r'], L['corners'][1]['r']):
                    bad.append('corner labels overlap')
                if not L['pillShown']:
                    bad.append('Paused pill not shown while paused')
                if not inside(L['bar'], w, h) or not inside(L['rail'], w, h) or any(bt[0] < 40 or bt[1] < 40 or bt[2] < 0 or bt[3] > w for bt in L['barBtns']):
                    bad.append('controls do not fit or buttons < 40 px')
                if bad:
                    fails.append({'scene': b['name'], 'problems': bad})
                shot(pg, out / f'{w}x{h}-{i:02d}-{slug(b["name"])}.png', shot_failures)
            check(f'{w}x{h}: overlay inside the viewport, nothing clipped, clear of bar / rail / Paused pill / corner labels, every scene', not fails, fails or f'{len(beats)} scenes')
            if w < 641:
                seek(pg, times[1])
                pg.wait_for_timeout(200)
                rail_row = pg.evaluate('() => { const r = document.getElementById("rail"); const cs = getComputedStyle(r); return cs.display !== "none" && cs.flexDirection === "row"; }')
                nav_hidden = pg.eval_on_selector('#nav', 'e => getComputedStyle(e).display === "none"')
                pg.click('#navtog')
                pg.wait_for_timeout(200)
                nb = pg.locator('#nav').bounding_box()
                nav_open = pg.eval_on_selector('#nav', 'e => e.classList.contains("open") && getComputedStyle(e).display !== "none"')
                shot(pg, out / f'{w}x{h}-nav-open.png', shot_failures)
                last = pg.locator('#nav button').last
                t_want = float(last.get_attribute('data-t'))
                last.click()
                pg.wait_for_timeout(100)
                closed = pg.eval_on_selector('#nav', 'e => !e.classList.contains("open")')
                check(f'{w}x{h}: rail is a row, list collapsed; the list button opens it inside the viewport; an entry seeks and closes it',
                      rail_row and nav_hidden and nav_open and inside({'x': nb['x'], 'y': nb['y'], 'width': nb['width'], 'height': nb['height']}, w, h) and near(T(pg), t_want, 0.05) and closed,
                      {'rail_row': rail_row, 'nav_hidden': nav_hidden, 'nav_open': nav_open, 'nav': nb, 't': T(pg), 'closed': closed})
            pg.close()
        browser.close()

        # ------------------------------------------------------------ fallback: three.js blocked, and WebGL disabled
        def fallback_page(args, block):
            br = pw.chromium.launch(args=args)
            fp = br.new_page(viewport={'width': 1280, 'height': 720})
            fp.on('pageerror', lambda e: errors.append(f'pageerror (fallback): {e}'))
            fp.on('console', lambda m: fallback_console.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
            if block:
                fp.route(re.compile(r'three(\.min)?\.js'), lambda r: r.abort())
            fp.goto(url, wait_until='load', timeout=60000)
            fp.wait_for_function('window.FILM && window.FILM.ready === true', timeout=45000)
            st = fp.evaluate("""() => ({ mode: window.FILM.mode, shown: getComputedStyle(document.getElementById('fallback')).display !== 'none',
                stageHidden: getComputedStyle(document.getElementById('stage')).display === 'none', title: document.getElementById('fbtitle').textContent,
                items: Array.from(document.querySelectorAll('#fblist li')).map(li => li.textContent.replace(/\\s+/g, ' ')) })""")
            shot(fp, out / f'fallback-{"blocked" if block else "nowebgl"}.png', shot_failures, full_page=True)
            br.close()
            return st

        def fallback_ok(st):
            return (st['shown'] and st['stageHidden'] and st['mode'] == 'fallback' and st['title'] == cfg.get('fallbackTitle') and len(st['items']) == len(beats)
                    and all(b['name'] in it and b['head'] in it and (b.get('sup', '') in it) for b, it in zip(beats, st['items']))
                    and all(all(c['text'] in it for c in (b.get('cards') or b.get('stages') or [])) for b, it in zip(beats, st['items'])))

        st1 = fallback_page(GL_ARGS, True)
        check('fallback (three.js blocked): every scene in words, with cards', fallback_ok(st1), {'mode': st1['mode'], 'items': st1['items']})
        st2 = fallback_page(NO_GL_ARGS, False)
        check('fallback (WebGL disabled): every scene in words, with cards', fallback_ok(st2), {'mode': st2['mode'], 'items': len(st2['items'])})

    check('no console errors or warnings, no failed requests, no page errors', not errors, errors[:20])
    check('every screenshot captured', not shot_failures, shot_failures or 'all')
    return finish(out, url, checks, errors, fallback_console)


def finish(out, url, checks, errors, fallback_console):
    failed = [k for k, v in checks.items() if not v['ok']]
    result = {'url': url, 'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks, 'errors': errors,
              'fallbackConsole (expected, not failures)': fallback_console, 'screenshots': sorted(str(f) for f in out.glob('*.png'))}
    (out / 'report.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 1 if failed or errors else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:  # report a crash as a failure, with its traceback
        import traceback
        print(json.dumps({'crash': repr(e), 'traceback': traceback.format_exc()}))
        sys.exit(1)
