// Usage: node controls-test.cjs ["<html path>"] [outDir]
// Loads Film C, waits for FILM.ready, then checks the timeline (86 s, 15 scenes), the playback controls, keyboard, scrubber, navbar, the narrow-screen
// rail, the two closing infographic slides (reveal state as a pure function of t, layout at 1280 / 390 / 1920), the end fade and loop, and the WebGL fallback.
// Prints a JSON report; exit code 1 if any check fails. Screenshots of the navbar and paused states go to outDir.
const { chromium } = require('playwright');
const path = require('path'); const fs = require('fs');
const htmlPath = process.argv[2] || path.join(__dirname, '..', 'Village Film C - Three Questions.html');
const outDir = process.argv[3] || path.join(__dirname, 'shots-C', 'controls');
fs.mkdirSync(outDir, { recursive: true });
const near = (a, b, tol) => Math.abs(a - b) <= tol;
const intersects = (a, b) => a && b && a.x < b.x + b.width && b.x < a.x + a.width && a.y < b.y + b.height && b.y < a.y + a.height;
const inside = (a, w, h) => a && a.x >= 0 && a.y >= 0 && a.x + a.width <= w + 0.5 && a.y + a.height <= h + 0.5;
(async () => {
  const b = await chromium.launch({ executablePath: 'C:/Users/kghoo/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe', args: ['--use-gl=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'] });
  const url = 'file:///' + path.resolve(htmlPath).replace(/\\/g, '/');
  const errors = [], checks = {};
  const check = (name, ok, detail) => { checks[name] = { ok: !!ok, detail }; };
  async function open(width, height) {
    const p = await b.newPage({ viewport: { width, height } });
    p.on('pageerror', e => errors.push('pageerror: ' + String(e)));
    p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errors.push(m.type() + ': ' + m.text()); });
    p.on('requestfailed', r => errors.push('requestfailed: ' + r.url()));
    await p.goto(url, { waitUntil: 'load', timeout: 60000 });
    await p.waitForFunction(() => window.FILM && window.FILM.ready === true, null, { timeout: 30000 });
    return p;
  }
  const T = p => p.evaluate(() => FILM.time());
  const box = (p, sel) => p.$eval(sel, e => { const r = e.getBoundingClientRect(); return { x: r.x, y: r.y, width: r.width, height: r.height }; }).catch(() => null);

  // the closing slides' on-screen text, verbatim from CLIENT-FEEDBACK-C2 rounds 4 and 4b
  const SLIDE_A = { head: 'How the village pays its way', items: [['Data', 'Every input, sensor record and result from each experiment, licensed to researchers and companies.'], ['Broadcast and advertising', 'A reality-TV style show. Viewers see how AI robots really behave, and learn how to live alongside them.'], ['Partner experiments', 'Companies design experiments with us to test their own questions for real projects.']], foot: 'Predictions are published before every experiment and results after it, whoever pays.' };
  const SLIDE_B = { head: 'Our roadmap: small, safe steps', items: [['Stage 1', 'Start in simulation, then bring in real crops.'], ['Stage 2', 'Then animals, possibly.'], ['Stage 3', 'People join virtually, by video and the message wall.'], ['Stage 4', 'People visit in person, possibly, and only if every earlier stage proves safe.']] };
  // layout of a (paused, fully revealed) closing slide: inside the viewport; clear of the bar, the rail and the Paused pill; no clipped text; body text >= 14 px
  async function slideLayout(pg, t, w, h) { await pg.evaluate(t => { FILM.seek(t); }, t); await pg.waitForTimeout(300);
    const r = await pg.evaluate(() => { const bx = e => { const r = e.getBoundingClientRect(); return { x: r.x, y: r.y, width: r.width, height: r.height }; }; const q = s => Array.from(document.querySelectorAll(s));
      return { cap: bx(document.getElementById('cap')), bar: bx(document.getElementById('bar')), rail: bx(document.getElementById('rail')), pill: bx(document.getElementById('paused')), pillShown: getComputedStyle(document.getElementById('paused')).display !== 'none',
        items: q('#info li').map(bx), texts: q('#head, #info h3, #info p').map(e => ({ r: bx(e), clipped: e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 3 /* a serif line box overflows its own height by 1-2 px of ascent; more than that is a lost line */ || (li => !!li && (r => { const o = li.getBoundingClientRect(); return r.left < o.left - 0.5 || r.right > o.right + 0.5 || r.top < o.top - 0.5 || r.bottom > o.bottom + 0.5; })(e.getBoundingClientRect()))(e.closest('#info li')) })), bodyPx: q('#info li p').map(e => parseFloat(getComputedStyle(e).fontSize)) }; });
    const all = [r.cap, ...r.items, ...r.texts.map(x => x.r)];
    r.ok = r.pillShown && r.items.length >= 3 && all.every(a => a.width > 0 && a.height > 0 && inside(a, w, h) && !intersects(a, r.bar) && !intersects(a, r.rail) && !intersects(a, r.pill)) && r.texts.every(x => !x.clipped) && r.bodyPx.every(f => f >= 14);
    r.row = r.items.every(i => near(i.y, r.items[0].y, 1)) && r.items.every((i, k) => k === 0 || i.x > r.items[k-1].x + r.items[k-1].width - 1);
    r.column = r.items.every((i, k) => near(i.x, r.items[0].x, 1) && (k === 0 || i.y > r.items[k-1].y + r.items[k-1].height - 12));
    return r; }

  // ---- 1280x720: API, keyboard, scrubber, navbar, layout
  const p = await open(1280, 720);
  check('autoplay on load', await p.evaluate(() => FILM.playing === true), 'FILM.playing after ready');
  // timeline: 86 s, 15 scenes, contiguous; the two closing slides by name, start and duration; slider and time readout agree
  const DUR = await p.evaluate(() => FILM.duration), scenes = await p.evaluate(() => FILM.scenes);
  const contiguous = scenes.every((s, i) => i === 0 ? s.start === 0 : near(s.start, scenes[i-1].start + scenes[i-1].dur, 1e-6)) && near(scenes[scenes.length-1].start + scenes[scenes.length-1].dur, DUR, 1e-6);
  check('timeline: 86 s, 15 contiguous scenes', DUR === 86 && scenes.length === 15 && contiguous, `duration ${DUR} scenes ${scenes.length} contiguous ${contiguous}`);
  const sA = scenes[13], sB = scenes[14];
  check('closing scenes: names, starts, durations', sA.name === 'How we will run it \u2014 How the village pays its way' && sA.start === 67 && sA.dur === 10 && sB.name === 'How we will run it \u2014 Our roadmap: small, safe steps' && sB.start === 77 && sB.dur === 9, JSON.stringify([sA, sB]));
  const vmax = await p.$eval('#prog', e => e.getAttribute('aria-valuemax')); await p.evaluate(() => { FILM.seek(3); }); const tmTxt = await p.$eval('#tm', e => e.textContent.trim());
  check('slider max and time readout show 86 s', vmax === '86' && tmTxt === '0:03 / 1:26', `aria-valuemax ${vmax} readout "${tmTxt}"`);
  const ticks = await p.$$eval('#prog .tick', ts => ts.map(t => parseFloat(t.style.left))), segs = await p.$$eval('#prog .seg', ss => ss.length);
  const wantTicks = scenes.filter(s => ![0, 5, 35, 51, 67].includes(s.start)).map(s => s.start / DUR * 100);
  check('scrubber: 5 segments, a tick at every beat start incl. 77 s', segs === 5 && ticks.length === wantTicks.length && wantTicks.every((w, i) => near(ticks[i], w, 0.01)), `segments ${segs} ticks ${ticks.map(t => t.toFixed(1)).join(',')}`);

  // pause stops time; play resumes
  await p.evaluate(() => { FILM.seek(20); FILM.play(); }); await p.waitForTimeout(500);
  await p.evaluate(() => FILM.pause()); const t1 = await T(p); await p.waitForTimeout(1500); const t2 = await T(p);
  check('pause stops time', Math.abs(t2 - t1) < 0.05 && !(await p.evaluate(() => FILM.playing)), `delta ${(t2 - t1).toFixed(4)} s over 1.5 s`);
  await p.evaluate(() => FILM.play()); await p.waitForTimeout(1000); const t3 = await T(p);
  check('play resumes', t3 > t2 + 0.7 && (await p.evaluate(() => FILM.playing)), `advanced ${(t3 - t2).toFixed(2)} s in 1 s`);

  // next / prev / restart (scene starts: 15 -> 29 -> 15)
  await p.evaluate(() => { FILM.seek(15); }); await p.evaluate(() => FILM.next()); const tn = await T(p);
  await p.evaluate(() => FILM.prev()); const tp = await T(p);
  check('next() to next scene start', near(tn, 29, 0.05), `from 15 -> ${tn.toFixed(2)}`);
  check('prev() to previous scene start', near(tp, 15, 0.05), `from 29 -> ${tp.toFixed(2)}`);
  await p.evaluate(() => FILM.restart()); const tr = await T(p); const pr = await p.evaluate(() => FILM.playing);
  // restart checks allow up to 0.8 s: the film is already playing again when time is read back, and headless SwiftShader can take a few frames (seen 0.34-0.35 s)
  check('restart() -> 0 and plays', tr < 0.8 && pr, `t ${tr.toFixed(2)} playing ${pr}`);

  // scrubber click at 60% -> ~0.6 x duration (51.6 s)
  await p.evaluate(() => FILM.pause()); const pb = await box(p, '#prog');
  await p.mouse.click(pb.x + pb.width * 0.6, pb.y + pb.height / 2); await p.waitForTimeout(150); const ts = await T(p);
  check('scrubber click at 60% seeks to ~0.6 x duration (51.6 s)', near(ts, 0.6 * DUR, 0.6), `t ${ts.toFixed(2)}`);
  // scrubber drag: press at 20%, move to 40%, release -> ~0.4 x duration (34.4 s)
  await p.mouse.move(pb.x + pb.width * 0.2, pb.y + pb.height / 2); await p.mouse.down(); await p.mouse.move(pb.x + pb.width * 0.4, pb.y + pb.height / 2, { steps: 5 }); await p.mouse.up();
  const td = await T(p); check('scrubber drag to 40% seeks to ~0.4 x duration (34.4 s)', near(td, 0.4 * DUR, 0.6), `t ${td.toFixed(2)}`);

  // keyboard: focus the stage (not a button), then space / ArrowRight / ArrowLeft / Home
  await p.mouse.click(640, 150); await p.evaluate(() => { FILM.seek(15); }); // paused at 15
  await p.keyboard.press('Space'); await p.waitForTimeout(400); const kp1 = await p.evaluate(() => FILM.playing);
  await p.keyboard.press('Space'); await p.waitForTimeout(100); const kp2 = await p.evaluate(() => FILM.playing);
  check('space toggles play/pause', kp1 === true && kp2 === false, `after 1st ${kp1}, after 2nd ${kp2}`);
  await p.evaluate(() => { FILM.seek(15); }); await p.keyboard.press('ArrowRight'); const kr = await T(p);
  await p.keyboard.press('ArrowLeft'); const kl = await T(p);
  check('ArrowRight -> next scene start', near(kr, 29, 0.05), `t ${kr.toFixed(2)}`);
  check('ArrowLeft -> previous scene start', near(kl, 15, 0.05), `t ${kl.toFixed(2)}`);
  await p.keyboard.press('Home'); const kh = await T(p); const khp = await p.evaluate(() => FILM.playing);
  check('Home restarts', kh < 0.8 && khp, `t ${kh.toFixed(2)} playing ${khp}`);
  await p.evaluate(() => FILM.pause());

  // paused frame stays rendered: the caption text is present and the play icon shows
  await p.evaluate(() => { FILM.seek(17); }); await p.waitForTimeout(900);
  const cap = await p.$eval('[data-caption]', e => e.textContent.trim().replace(/\s+/g, ' '));
  const playLabel = await p.$eval('#bplay', e => e.getAttribute('aria-label'));
  check('paused frame keeps caption and shows Play', cap.indexOf('RQ1:') >= 0 && playLabel === 'Play', `caption "${cap.slice(0, 60)}..." button "${playLabel}"`);
  await p.mouse.move(640, 300); await p.waitForTimeout(200);
  await p.screenshot({ path: path.join(outDir, 'paused-1280.png') });

  // navbar: click "2 Keeping shared spaces > The experiment" -> 42 s, highlighted
  const navBtn = p.locator('#nav .sc', { hasText: 'Keeping shared spaces' }).locator('.beats button', { hasText: 'The experiment' });
  await navBtn.click(); await p.waitForTimeout(100); const tv = await T(p);
  const cur = await navBtn.getAttribute('aria-current');
  const scOn = await p.locator('#nav .sc', { hasText: 'Keeping shared spaces' }).evaluate(e => e.classList.contains('on'));
  const acc = await p.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--acc').trim());
  check('navbar entry seeks to 42 s and is highlighted', near(tv, 42, 0.05) && cur === 'true' && scOn && acc === '#2a9d8f', `t ${tv.toFixed(2)} aria-current ${cur} scenario.on ${scOn} accent ${acc}`);
  const navLabels = await p.$$eval('#nav button', bs => bs.map(b => b.textContent.trim()));
  check('navbar lists Introduction, 3 scenarios x 4 beats, How we will run it + its two slides', navLabels.length === 19 && navLabels[0] === 'Introduction' && navLabels[16] === 'How we will run it' && navLabels[17] === 'How the village pays its way' && navLabels[18] === 'Our roadmap: small, safe steps' && navLabels[1] === '1Feeding people', navLabels.join(' | '));
  // navbar: the group label and its two slides seek to 67 / 67 / 77 s; the slide entry is current and the accent is the neutral one
  const navAt = async label => { const bt = p.locator('#nav button', { hasText: label }).first(); await bt.click(); await p.waitForTimeout(100); return { t: await T(p), cur: await bt.getAttribute('aria-current') }; };
  const nG = await navAt('How we will run it'), nA = await navAt('How the village pays its way'), nB = await navAt('Our roadmap: small, safe steps');
  const accC = await p.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--acc').trim());
  check('navbar: How we will run it entries seek to 67 / 67 / 77 s', near(nG.t, 67, 0.05) && near(nA.t, 67, 0.05) && nA.cur === 'true' && near(nB.t, 77, 0.05) && nB.cur === 'true' && accC === '#e8e6e1', JSON.stringify({ nG, nA, nB, accC }));
  await navBtn.click(); await p.waitForTimeout(100); // back to 42 s for the screenshot and the layout checks below
  await p.waitForTimeout(900); await p.mouse.move(1180, 360); await p.waitForTimeout(300);
  await p.screenshot({ path: path.join(outDir, 'navbar-1280.png') });

  // ---- closing slides: reveal state is a pure function of t (checked out of order), wording, numerals, layout
  const infoState = (pg, t) => pg.evaluate(t => { FILM.seek(t); const q = s => Array.from(document.querySelectorAll(s));
    return { on: q('#info li').map(e => e.getAttribute('data-on')).join(''), op: q('#info li').map(e => +getComputedStyle(e).opacity), foot: (document.getElementById('foot') || { getAttribute: () => '-' }).getAttribute('data-on'),
      head: document.getElementById('head').textContent, items: q('#info li').map(e => [e.querySelector('h3').textContent, e.querySelector('p').textContent]), footText: (document.getElementById('foot') || {}).textContent || '',
      icons: q('#info li svg').length, cond: q('#info li').map(e => e.classList.contains('cond') ? 1 : 0).join(''), dash: q('#info .ln').map(e => e.classList.contains('dash') ? 1 : 0).join(''),
      beat: getComputedStyle(document.getElementById('beat')).display, sidx: document.getElementById('sidx').textContent, caption: document.querySelector('[data-caption]').textContent.replace(/\s+/g, ' ').trim() }; }, t);
  const order = [76, 68, 73, 70.5, 67.1], want = { 67.1: ['000', '0'], 68: ['100', '0'], 70.5: ['110', '0'], 73: ['111', '0'], 76: ['111', '1'] }, gotA = {};
  for (const t of order) { const st = await infoState(p, t); gotA[t] = [st.on, st.foot]; }
  check('slide A: cards reveal in order as a pure function of t', order.every(t => gotA[t][0] === want[t][0] && gotA[t][1] === want[t][1]), JSON.stringify(gotA));
  const stA = await infoState(p, 76);
  check('slide A: headline, three cards (icon + title + line) and footer verbatim', stA.head === SLIDE_A.head && JSON.stringify(stA.items) === JSON.stringify(SLIDE_A.items) && stA.footText === SLIDE_A.foot && stA.icons === 3 && stA.op.every(o => o === 1), JSON.stringify({ head: stA.head, items: stA.items, foot: stA.footText, icons: stA.icons }));
  check('slide A: no scenario numeral and no digits', stA.beat === 'none' && stA.sidx === '' && !/\d/.test(stA.caption), `beat ${stA.beat} caption "${stA.caption.slice(0, 50)}..."`);
  const orderB = [85, 78, 83, 80, 77.1], wantB = { 77.1: '0000', 78: '1000', 80: '1100', 83: '1110', 85: '1111' }, gotB = {};
  for (const t of orderB) gotB[t] = (await infoState(p, t)).on;
  check('slide B: milestones reveal left to right as a pure function of t', orderB.every(t => gotB[t] === wantB[t]), JSON.stringify(gotB));
  const stB = await infoState(p, 85);
  check('slide B: headline and four stages verbatim; stages 2 and 4 outlined, with dashed connectors', stB.head === SLIDE_B.head && JSON.stringify(stB.items) === JSON.stringify(SLIDE_B.items) && stB.icons === 4 && stB.cond === '0101' && stB.dash === '1010', JSON.stringify({ head: stB.head, items: stB.items, cond: stB.cond, dash: stB.dash }));
  check('slide B: no scenario numeral; digits only after the word Stage', stB.beat === 'none' && stB.sidx === '' && !/\d/.test(stB.caption.replace(/Stage [1-4]\b/g, '')), `beat ${stB.beat}`);
  const lA = await slideLayout(p, 76, 1280, 720), lB = await slideLayout(p, 85, 1280, 720);
  check('1280: slide A cards in one row, clear of bar / rail / Paused pill, nothing clipped', lA.ok && lA.row, JSON.stringify({ cap: lA.cap, bar: lA.bar, rail: lA.rail, bodyPx: lA.bodyPx, row: lA.row }));
  check('1280: slide B roadmap horizontal, clear of bar / rail / Paused pill, nothing clipped', lB.ok && lB.row, JSON.stringify({ cap: lB.cap, bodyPx: lB.bodyPx, row: lB.row }));
  await p.mouse.move(640, 200); await p.waitForTimeout(200); await p.screenshot({ path: path.join(outDir, 'closing-B-1280.png') });
  // end of film: the black fade covers the last 0.7 s, and playback loops to the start
  const fadeAt = async t => { await p.evaluate(t => { FILM.seek(t); }, t); return p.$eval('#fade', e => parseFloat(e.style.opacity)); };
  const f85 = await fadeAt(85), f858 = await fadeAt(85.8);
  check('end fade over the last 0.7 s', f85 === 0 && f858 > 0.6, `fade at 85 s ${f85}, at 85.8 s ${f858.toFixed(2)}`);
  await p.evaluate(() => { FILM.seek(85.5); FILM.play(); }); await p.waitForTimeout(1300); const tl = await T(p), pl = await p.evaluate(() => FILM.playing);
  check('film loops after 86 s', tl < 2 && pl, `t ${tl.toFixed(2)} playing ${pl}`);
  await p.evaluate(() => FILM.pause()); await navBtn.click(); await p.waitForTimeout(100);

  // layout at 1280x720: controls and navbar never intersect the caption block
  const bar = await box(p, '#bar'), nav = await box(p, '#nav'), panel = await box(p, '#panel'), capBox = await box(p, '#cap');
  check('bar does not intersect caption block', !intersects(bar, panel) && !intersects(bar, capBox), JSON.stringify({ bar, panel }));
  check('navbar does not intersect caption block', !intersects(nav, panel) && !intersects(nav, capBox), JSON.stringify({ nav, panel }));
  const btnSizes = await p.$$eval('#bar button, #nav button', bs => bs.map(b => { const r = b.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; }));
  check('bar buttons are >= 40 px', btnSizes.slice(0, 4).every(s => s[0] >= 40 && s[1] >= 40), JSON.stringify(btnSizes.slice(0, 4)));
  // idle fade: after 2.5 s of no input while playing the bar drops to ~0.35; input restores it
  await p.evaluate(() => FILM.play()); await p.waitForTimeout(3200);
  const opIdle = await p.$eval('#bar', e => parseFloat(getComputedStyle(e).opacity));
  await p.mouse.move(600, 400); await p.waitForTimeout(500);
  const opAwake = await p.$eval('#bar', e => parseFloat(getComputedStyle(e).opacity));
  check('idle fade and wake', opIdle < 0.5 && opAwake > 0.95, `idle ${opIdle} awake ${opAwake}`);
  await p.evaluate(() => FILM.pause());
  await p.close();

  // ---- 390x844: rail visible, controls fit, list opens from the toggle
  const m = await open(390, 844);
  await m.evaluate(() => { FILM.seek(44); FILM.pause(); }); await m.waitForTimeout(900);
  const rail = await box(m, '#rail'), mbar = await box(m, '#bar'), mpanel = await box(m, '#panel');
  const railVisible = await m.$eval('#rail', e => getComputedStyle(e).display !== 'none');
  const navHidden = await m.$eval('#nav', e => getComputedStyle(e).display === 'none');
  const mBtns = await m.$$eval('#bar button, #rail button', bs => bs.map(b => { const r = b.getBoundingClientRect(); return { w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x), r: Math.round(r.x + r.width) }; }));
  check('390: rail visible, full navbar collapsed', railVisible && inside(rail, 390, 844) && navHidden, JSON.stringify({ rail, navHidden }));
  check('390: control bar fits', inside(mbar, 390, 844) && mBtns.every(s => s.w >= 40 && s.h >= 40 && s.x >= 0 && s.r <= 390), JSON.stringify({ mbar, mBtns }));
  check('390: rail clear of caption block', !intersects(rail, mpanel), JSON.stringify({ rail, mpanel }));
  const dotOn = await m.$eval('#rail .dot.on', e => e.textContent.trim()).catch(() => null);
  check('390: active scenario dot lit', dotOn === '2', `dot ${dotOn}`);
  await m.screenshot({ path: path.join(outDir, 'rail-390.png') });
  await m.click('#navtog'); await m.waitForTimeout(200);
  const navOpen = await m.$eval('#nav', e => getComputedStyle(e).display !== 'none' && e.classList.contains('open'));
  const navBox = await box(m, '#nav');
  check('390: toggle opens the scene list inside the viewport', navOpen && inside(navBox, 390, 844), JSON.stringify(navBox));
  await m.screenshot({ path: path.join(outDir, 'navbar-open-390.png') });
  await m.locator('#nav .sc', { hasText: 'Living together' }).locator('.beats button', { hasText: 'The safety question' }).click(); await m.waitForTimeout(100);
  const mt = await T(m); const closed = await m.$eval('#nav', e => !e.classList.contains('open'));
  check('390: list entry seeks and closes the list', near(mt, 55, 0.05) && closed, `t ${mt.toFixed(2)} closed ${closed}`);
  // 390: closing slides - cards stacked, roadmap vertical, body text >= 14 px, nothing under the bar, the rail or the Paused pill
  const mA = await slideLayout(m, 76, 390, 844), mB = await slideLayout(m, 85, 390, 844);
  check('390: slide A cards stacked, readable, clear of bar / rail / Paused pill', mA.ok && mA.column, JSON.stringify({ cap: mA.cap, bar: mA.bar, rail: mA.rail, pill: mA.pill, bodyPx: mA.bodyPx, column: mA.column }));
  check('390: slide B roadmap vertical, readable, clear of bar / rail / Paused pill', mB.ok && mB.column, JSON.stringify({ cap: mB.cap, bodyPx: mB.bodyPx, column: mB.column }));
  await m.screenshot({ path: path.join(outDir, 'closing-B-390.png') }); await m.evaluate(() => { FILM.seek(76); }); await m.waitForTimeout(300); await m.screenshot({ path: path.join(outDir, 'closing-A-390.png') });
  await m.close();

  // ---- 1920x1080 layout sanity
  const g = await open(1920, 1080);
  await g.evaluate(() => { FILM.seek(60); FILM.pause(); }); await g.waitForTimeout(900);
  const gbar = await box(g, '#bar'), gnav = await box(g, '#nav'), gpanel = await box(g, '#panel');
  check('1920: bar and navbar clear of caption block', !intersects(gbar, gpanel) && !intersects(gnav, gpanel), JSON.stringify({ gbar, gnav, gpanel }));
  await g.mouse.move(1800, 540); await g.waitForTimeout(300);
  await g.screenshot({ path: path.join(outDir, 'paused-1920.png') });
  await g.evaluate(() => { FILM.seek(17); }); await g.waitForTimeout(900);
  await g.screenshot({ path: path.join(outDir, 'paused-1920-garden.png') });
  const gA = await slideLayout(g, 76, 1920, 1080), gB = await slideLayout(g, 85, 1920, 1080);
  check('1920: closing slides in one row, clear of bar / rail / Paused pill, nothing clipped', gA.ok && gA.row && gB.ok && gB.row, JSON.stringify({ capA: gA.cap, capB: gB.cap, rail: gA.rail, bodyPx: gA.bodyPx }));
  await g.close();

  // ---- WebGL fallback: with the 3D library blocked, the page lists all 15 scenes in words, including the closing slides' cards, footer and stages
  const fp = await b.newPage({ viewport: { width: 1280, height: 720 } });
  await fp.route(/three(\.min)?\.js/, r => r.abort()); await fp.goto(url, { waitUntil: 'load', timeout: 60000 });
  await fp.waitForFunction(() => window.FILM && window.FILM.ready === true, null, { timeout: 30000 });
  const fb = await fp.evaluate(() => ({ shown: getComputedStyle(document.getElementById('fallback')).display !== 'none', items: Array.from(document.querySelectorAll('#fblist li')).map(li => li.textContent.replace(/\s+/g, ' ')) }));
  const fbA = fb.items[13] || '', fbB = fb.items[14] || '';
  check('fallback lists 15 scenes with the closing cards, footer and stages', fb.shown && fb.items.length === 15 && SLIDE_A.items.every(i => fbA.includes(i[0] + ': ' + i[1])) && fbA.includes(SLIDE_A.foot) && fbA.includes(SLIDE_A.head) && SLIDE_B.items.every(i => fbB.includes(i[1])) && fbB.includes('Stage 4 (conditional): ') && fbB.includes(SLIDE_B.head), JSON.stringify([fbA, fbB]));
  await fp.close();
  await b.close();

  const failed = Object.keys(checks).filter(k => !checks[k].ok);
  const result = { url, errors, passed: Object.keys(checks).length - failed.length, failed, checks, screenshots: fs.readdirSync(outDir).filter(f => f.endsWith('.png')).map(f => path.join(outDir, f)) };
  fs.writeFileSync(path.join(outDir, 'report.json'), JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 2));
  process.exit(failed.length || errors.length ? 1 : 0);
})().catch(e => { console.error('CONTROLS TEST FAILED', e); process.exit(1); });
