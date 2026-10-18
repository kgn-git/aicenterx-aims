# Initiative film template

This folder holds the shared template for the five initiative films agreed in issue #1, with sub-issues #2 to #6. Each film shows one AI initiative from the AI Center X prototype in an **actual situation of use**: the real people, place and moment where the AI is used. Examples are a loan applicant in a banking app, a contact-centre call, a recruiter's queue, a card payment under review and a planning meeting. Each film is grounded in that initiative's **AI Canvas** and governance record. The films are standalone. They are not scenes in Village Film C, and they are not set in the robot village.

| File | What it is |
|---|---|
| `film-template.html` | A working film skeleton. It runs as it is, with a placeholder office scene. Copy it and edit only its `CONFIG` block. |
| `README.md` | This file: the technical contract, how to make a film, the script document structure and the settings kit. |
| `../../test/film_controls_test.py` | The shared controls and layout test. Every film must pass it. |

`simulation/Village Film C - Three Questions.html` and its `Script and Protocols.md` remain the format and structure reference only. Do not edit them.

---

## 1. Technical contract

The Village script cites `test/BRIEF.md`, `test/BRIEF-C2.md` and `test/CLIENT-FEEDBACK-C2.md`. Those files are not in the repo, so this section restates the contract the Village Film follows, as the template implements it. Where the two differ, this section governs the initiative films.

### 1.1 Page

- One self-contained HTML file per film, in `simulation/<initiative>/`. It contains the CSS, the script and all text.
- External resources are limited to two. The first is Three.js **r128** from cdnjs, with the exact `<script>` tag and SRI hash used in the template. The second is Google Fonts: Fraunces for headlines and IBM Plex Sans for body text.
- No build step and no other libraries. The page works from `file://`.
- `document.title` is set from `CONFIG.title`. Keep the static `<title>` and the `description` meta in step with it.

### 1.2 `window.FILM` API

| Member | Meaning |
|---|---|
| `ready` | `true` once the first frame is on screen, or once the fallback is shown. |
| `mode` | `'direct'` (hardware GL), `'2d'` (software GL, read back through a 2D canvas) or `'fallback'` (text only). |
| `duration` | Film length in seconds: the start plus the duration of the last scene. |
| `scenes` | `[{name, start, dur, beat}]`, one entry per `CONFIG.beats` entry. |
| `seek(t)` | Shows exactly the frame for `t` and pauses. |
| `play()`, `pause()`, `time()`, `playing` | Playback. `playing` is a getter. |
| `next()`, `prev()`, `restart()` | `next` goes to the next scene start and wraps to 0 after the last scene. `prev` goes to the current scene's start if more than 1.5 s into it, otherwise to the previous scene's start. Both keep the current play state. `restart` goes to 0 and plays. |
| `clearance(t)` | `{d, who, cam}`: the distance from the camera to the nearest collider or visible person at `t`. |
| `minClearance(step)` | The worst `clearance` over the whole film, sampled every `step` seconds (default 0.1). |
| `signature(t)` | A fingerprint of the world at `t`: camera, every object's transform and visibility, material colours, and screen contents. |
| `present()` | Diagnostics for the 2D presentation path. |

`window.FILM_CONFIG` is a JSON copy of the text and timing in `CONFIG`, without functions or camera keys. The test reads it, and later tools such as a prototype integration or a readability checker can read it too.

### 1.3 Determinism

The film state is a **pure function of `t`**. `seek(t)` must give the same picture and the same overlay whatever was shown before, and the test checks this through `FILM.signature`.

- `build()` creates every object once. After it runs, the template snapshots every object's transform and visibility, every material's colour, emissive and opacity, every light, the background, the fog and every screen.
- Before each `update(t)` call, the template restores that snapshot. `update` therefore only sets what differs from the build-time state at time `t`. It never adds or removes objects, and it never keeps state between calls.
- For variety, use `kit.rng(seed)` inside `build()`. Do not use `Math.random()` or `Date` anywhere in `update()`.

### 1.4 Timeline

- `CONFIG.beats` is contiguous: each entry starts where the one before ends. The template logs a console error if it is not, and that error fails the test.
- `beat: 1-4` are the four story beats. `beat: 0` is an open or close card.
- One beat may span several consecutive entries, for example two seeded faults in beat 3. They share the numeral, one scrubber segment and one rail dot, and the scene list shows them as sub-entries.
- The four beats run **45-60 s** in total. Each card runs **10 s or less**.
- Cuts land exactly on entry boundaries.
- The film autoplays and loops. While playing, there is a short black flash at each cut. The last 0.7 s fades to black with the caption.

### 1.5 Overlay

The overlay holds **the only readable text in the film**.

| Element | Content |
|---|---|
| Top left | The **setting**: the place and moment, for example "Mobile banking app, Tuesday 21:40". It sits on a small pill with a dot in the beat's accent colour. |
| Top right | The **initiative** name, the same on every scene. |
| Beat row | The big **beat numeral** (1-4) in the accent colour. Beside it go the **source** line (where the beat comes from, for example "AI Canvas: Business Problem") and the four-step indicator, `The situation → The AI at work → What can go wrong → How it is kept safe`, with the current beat lit. The row is hidden on cards. At phone width the indicator shows the current beat in words and the others as dots. |
| Caption, `[data-caption]` | One **headline**, at most one **support** line, an optional **infographic** (cards in a row, or a roadmap of stages) and an optional footer. |
| Note | An optional small line under the caption, for example "Seeded fault, staged for this film." |
| Step chips | Optional buttons for the steps inside one beat. Each seeks to the start of its step, and the active chip is lit. |
| Accent rule | A thin rule on the left of the caption block in the beat's accent colour. Cards use the neutral paper tone. |

Default accents are:

| Beat | Accent |
|---|---|
| 1 The situation | teal `#2a9d8f` |
| 2 The AI at work | blue `#4a86d8` |
| 3 What can go wrong | red `#d84a3a` |
| 4 How it is kept safe | green `#3fa34d` |
| Cards | neutral `#e8e6e1` |

A pale tint of each accent is used for small text over the picture.

In-world screens, boards, phones and tags show **glyphs, bars, rows and colours only, never words**. The colour language is the same in every film:

| Colour | Meaning |
|---|---|
| Green | Passed or safe |
| Amber | Held for a person |
| Red | Fault or risk |
| Blue | The AI or its data |
| Grey | Idle |

### 1.6 Camera

- Each entry has camera keys in **local time**, eased with a quintic curve. Three forms are available:
  - `[lt, px,py,pz, lx,ly,lz]` looks at a point.
  - `[lt, px,py,pz, sx,sy,sz, nx,ny]` is aimed: the subject lands at the screen offset (`nx`, `ny`) in half-frames, `+x` right and `+y` up.
  - Adding a 10th element to the aimed form keeps the horizon level.
- Keep the subject in the **upper right**, around `0.2 / 0.2`. The caption takes the lower left, and the card slides take the lower half, so aim at about `0 / 0.4` there.
- On portrait screens the aim is centred and lifted, and the lens is wider (64° instead of 48°).
- The camera never enters geometry. It stays at least `CONFIG.minClearance` from every collider and every visible person, checked at 0.1 s steps. The default is 1.0 m for indoor sets; the Village Film used 2.5 m outdoors.
- `update()` may override the camera with `ctx.camKeys(...)`, `kit.camAim(...)` or `kit.camOrbit(...)`.

### 1.7 Controls

**Playback bar.** Previous scene, play/pause, next scene, the scrubber, a keyboard hint, the time readout, and restart set apart at the far end.

- The scrubber has one segment per beat group in the accent colour and a neutral segment per card, with a tick at every other scene start. Click seeks; press and drag scrubs.
- Every button has a tooltip naming its key.
- The bar and rail fade to 35 % opacity after 2.5 s without input while playing, never while paused.

**Keyboard.** `Space` plays and pauses, unless a button has focus. `←` and `→` step scenes. `Home` restarts. `Esc` closes the scene list.

**Paused.** A paused frame shows the full caption, and a `Paused` pill appears at the top centre. Below 1100 px wide the pill sits under the setting label.

**Navigation.** At rest it is a rail on the right: one numbered dot per beat group, plus a list button. The full list (cards by name, beats by numeral and label, multi-scene beats with their entries) flies out on hover or keyboard focus, or is pinned with the list button. The current entry is a solid pill in the accent colour; hover is only an underline.

**Phone width (640 px or less).**

- The corner labels stack.
- The rail becomes a row under them, and the list opens as a sheet over a dimmed backdrop.
- The scrubber gets its own row above the buttons.
- Cards stack, and the roadmap turns vertical.
- Chips wrap without connector lines.

### 1.8 Fallback

If Three.js fails to load or WebGL cannot start, the page shows `CONFIG.fallbackTitle`, the note "This film needs 3D graphics (WebGL). Your browser could not start it. Here is the film in words.", and every scene in words. Each scene shows its beat number and name, then the headline, the support line, the note, and each card as `Title: line` with the footer. `FILM.ready` becomes `true` with `FILM.mode === 'fallback'`.

### 1.9 Software GL

On a software GL driver such as SwiftShader or llvmpipe, which covers headless test runs, frames are read back through a pixel-pack buffer and fence and shown through a 2D canvas. The template keeps this machinery from the Village Film unchanged. Add `?present=2d` to the URL to force this path.

### 1.10 Testing

```
python test/film_controls_test.py "simulation/<initiative>/<Film name>.html" [outDir]
```

The test uses Python Playwright and Chromium with SwiftShader. Screenshots go to `test/shots/<film name>/` by default, which is ignored by git, together with `report.json`. The test prints a JSON report and exits with code 1 on any failure. It checks:

- the timeline against `CONFIG`, the four-beat structure and the runtime
- the overlay text at every scene
- determinism, both for overlay and world, by seeking in any order and by playing versus seeking
- play, pause, next, prev and restart; the bar buttons; the scrubber click and drag; the keyboard; the chips; the scene list and rail; the paused state; the end fade and loop; the idle fade
- camera clearance
- layout of every scene at 1280×720, 390×844 and 1920×1080: inside the viewport, nothing clipped, clear of the bar, rail, Paused pill and corner labels, readable sizes
- the phone scene list
- the fallback, both with three.js blocked and with WebGL disabled
- no console errors or warnings, no failed requests and no page errors

---

## 2. Making a new film

1. **Write the script first.** Write `simulation/<initiative>/<Film name> - Script and Protocols.md` following section 3 below, and get it agreed in the initiative's sub-issue.
2. **Copy the template.** Copy `film-template.html` to `simulation/<initiative>/<Film name>.html`. Update the `<title>`, the `description` meta and the comment at the top.
3. **Fill in `CONFIG`.**
   - `title`, `initiative`, `fallbackTitle`.
   - `beats`: one entry per row of the shot script. Copy the on-screen text exactly as written in Part 1, with `start` and `dur` from the script.
   - `accent` and `accentLight`: keep the defaults unless the script says otherwise.
   - `minClearance` and `env`: the background, fog, shadow area and the centre the sun aims at.
4. **Build the set.** In `build(THREE, scene, kit)`, build the set from the props kit (section 5). Return an object of handles to everything `update()` animates. Register a collider with `kit.coll()` or `kit.collBox()` for anything the camera might approach; the kit's furniture registers its own.
5. **Stage the action.** In `update(t, o, ctx)`, stage the world action from the shot script as a function of `t`. You can use film time `t` for action that carries across beats, or `ctx.lt` and `ctx.u` within one entry. Screens change through `screen.show(spec)`; never draw words.
6. **Set the camera.** Set each entry's `cam` keys. Keep the subject upper right and clear of the caption, and stay at least `minClearance` from every collider and person.
7. **Test and review.** Run `python test/film_controls_test.py "<film.html>"` until it exits 0. Look at every screenshot it writes; the test checks layout, not whether the picture tells the story.
8. **Leave the template alone.** Do not change anything below `END OF CONFIG` in a film. If a film needs new shared machinery or a new prop that another film could use, add it to the template here, and re-run the test on the template and on every film.

### `CONFIG.beats` entry fields

| Field | Required | Shown as |
|---|---|---|
| `beat` | yes | 0 for a card; 1-4 for the story beats (numeral, indicator, accent). |
| `name` | yes | The scene name: in the scene list, `FILM.scenes`, the fallback and the scrubber's `aria-valuetext`. Usually the beat label, or "What can go wrong — fault 2" for a second entry in one beat. |
| `start`, `dur` | yes | Seconds. Must be contiguous. |
| `setting` | yes | Top-left label: the place and the moment. |
| `head` | yes | The headline. |
| `sup` | no | One support line. |
| `source` | beats 1-4 | The line beside the numeral: which AI Canvas blocks or governance records the beat draws on. |
| `note` | no | A small line under the caption, for example to mark a staged fault. |
| `chips` | no | `[{label, at}]`: step buttons, where `at` is local time. |
| `cards` or `stages` | no | `[{ic, at, title, text, cond}]`: an infographic revealed at local times `at`. `stages` draws a roadmap, and `cond: true` draws a conditional stage as an outlined node with dashed connectors. Icons: `shield doc gate people data check alert loop chart clock lock person`. |
| `foot`, `footAt` | no | A one-line footer under the infographic, and when it appears. |
| `nav` | no | A shorter label for the scene list. |
| `cam` | yes | Camera keys in local time (section 1.6). |

---

## 3. The script document: `<Film name> - Script and Protocols.md`

Every film has a script and protocol document beside it, adapted from the Village Film's. Phase 1 of each sub-issue produces this document, and the film is built from it once it is agreed. It is written in plain language and claims no results: every number is a **design parameter**.

### Header

- **Governing sources.** Issue #1 and the initiative's sub-issue. The initiative's record in `index.html`: the `INITIATIVES` entry and the AI Canvas in `CANVASES`, plus `RISKS`, `INCIDENTS`, `CONTROLS`, `EVIDENCE`, `DECISIONS`, `IMPACTS`, `MODELS`, `SYSTEM_CARDS`, `DATASOURCES` and `INIT_SOURCES`, and supplier entries where relevant. Name each source by its id.
- **Runtime line.** For example: `Runtime 58 s: open 4 s → 1 The situation 12 s → 2 The AI at work 14 s → 3 What can go wrong 12 s → 4 How it is kept safe 12 s → close 4 s`. Every entry is its own scene in `FILM.scenes`, and cuts land on entry boundaries. The film autoplays, loops and is seekable as a pure function of t.
- **Design-parameter statement.** "All numbers in this document are design parameters unless labelled otherwise. No results are reported." People are the prototype's fictional people and roles (`PEOPLE`), plus fictional customers. Name no real organisation or person.

### Part 1: Shot script

- **Conventions.** This is the overlay contract from section 1.5 as it applies to this film: the setting labels, the initiative label, the beat numerals and indicator, and the accent colours. It also covers what the in-world screens show (glyphs only) and the colour language: green passed, amber held for a person, red fault, blue AI or data.
- **Situation of use.** In one paragraph: who is involved, where, at what moment, and what triggers the AI. This is the frame for the whole film.
- **Shot table.** One row per `CONFIG.beats` entry. Columns:
  - `#`, `start s`, `dur s`, `beat`
  - `setting` (place and moment)
  - `source` (AI Canvas blocks or record ids)
  - `camera` (position, move, and where the subject sits on screen)
  - `world action` (what people, screens and props visibly do, with local times)
  - `headline` (exact on-screen text)
  - `support line` (exact)
  - `note`, `chips` or `cards` (exact)
  - `accent`

  The four beats map to the AI Canvas as follows:

  | Beat | Draws on |
  |---|---|
  | 1 The situation | Business Problem; who is involved and what triggers the AI. |
  | 2 The AI at work | Objective Function, Modeling Approach, Data Strategy, Customer Value. |
  | 3 What can go wrong | The initiative's risks and incidents, staged as **seeded faults**. |
  | 4 How it is kept safe | Controls, board decisions, evidence, Model Training (the feedback loop), and the next gate. |

- **Word count and readability.** A table with one row per on-screen line, giving the line, the number of words, the limit and the Flesch-Kincaid grade. Count words as whitespace-separated tokens that contain a letter or digit. Calculate the grade as 0.39 × words ÷ sentences + 11.8 × syllables ÷ words − 15.59, counting syllables as vowel groups. The limits:

  | Line | Limit |
  |---|---|
  | Headline | 14 words or fewer |
  | Support line | 18 words or fewer |
  | Source line | 10 words or fewer |
  | Note | 10 words or fewer |
  | Chip | 2 words or fewer |
  | Card title | 4 words or fewer |
  | Card or stage line | 14 words or fewer |
  | Footer | 16 words or fewer |
  | All on-screen text in the film | 220 words or fewer |
  | Flesch-Kincaid grade, every line | 8 or lower |

  Fixed overlay text is not counted: the beat indicator, the corner labels, the control labels and the `Paused` pill. Any client-worded line is used verbatim, flagged, and reported rather than enforced, as in the Village script.
- **Plain-language conventions.**
  1. Full sentences, never fragments.
  2. People first. Beat 1 names who has the stake. Beat 2 says what the customer or user gains. Beat 3 says who would be harmed and how. Beat 4 says who checks, and what they can now trust or decide.
  3. Jargon is replaced, not explained on screen. Include a mapping table: on-screen phrase → AI Canvas block or governance record and field.
  4. No result is stated anywhere on screen.

### Part 2: Protocols

Part 2 is the record behind the film, so that every staged event can be traced to the prototype's data.

| Section | Content |
|---|---|
| Initiative summary | Stage, risk tier, owner and sponsor (by role), model and supplier, from the prototype record. |
| AI Canvas | All seven blocks. For an incomplete canvas, draft the missing blocks here as **labelled assumptions for review**, based on the initiative summary, model record, system card and data sources. `index.html` is not changed. |
| Setting and props | The set, built from the settings kit (section 4); the people (fictional roles); what each screen shows (glyph spec); and what each colour means in this film. |
| Seeded faults | One row per staged fault: what the viewer sees, the risk or incident it stands for (by id), the ground truth, and why it is staged rather than real. |
| Controls and evidence | Each control shown in beat 4, with its id; the evidence that shows it works; the board decision it rests on; who acts and when. |
| Feedback loop | How Model Training uses the outcome of the case, as shown on screen: what flows back, who approves it, and how often. |
| Next gate | The next stage gate, its criteria and the decision owner, as recorded or as a labelled assumption. |
| Measures shown | Any number or bar on screen, as a design parameter with its source. |
| Ethics and depiction | Fictional people only; no real organisation, brand or customer data; no claimed results; how the film avoids implying a result. |
| Real-world transfer | What a viewer such as a board member, owner or customer should take away, in one paragraph. |

---

## 4. Settings kit: sets for the five films

The sets and props each film needs (issue #1, settings kit item), and which can be shared. **Kit today** means the piece already exists in `film-template.html`. **Add** means a film needs it. A piece that more than one film needs goes into the template's props kit, not into one film.

| Film (sub-issue) | Situation of use | Set | Kit today | Add |
|---|---|---|---|---|
| Retail Credit Risk Scoring, `rcr` (#2) | A loan applicant applies in the banking app at home; a credit officer reviews a referred case | A living room with a sofa and a phone in hand; a bank back office with a credit officer's desk | `room`, `windowPane`, `door`, `desk`, `chair`, `monitor`, `phone`, `person`, `link`, `rack`, `ring`, `plant`, `shelf` | `sofa`, `lamp` (domestic room) |
| Customer Service Copilot, `chatbot` (#3) | A contact-centre agent on a live call with a customer, the copilot suggesting replies | A contact-centre floor with rows of desks, agents in headsets and a team leader's wall display | `desk`, `chair`, `monitor` (suggestion rows and badge), `person({headset:true})`, `wallScreen` (queue line), `phone` (the caller at home, in a second set) | `deskRow` (repeat helper) and a low `partition` between desks |
| CV Screening Assistant, `hiring` (#4) | A recruiter works through an applicant queue; a candidate applies from a café or home | A recruiter's workspace and a candidate's phone | `desk`, `monitor` with `tiles` (the applicant queue as coloured cards), `person`, `phone`, `ring` | `cafeTable` (optional) |
| Fraud Triage Model, `fraud` (#5) | A card payment at a shop till is flagged; an analyst at a review desk triages the alert | A shop counter with a payment terminal; a fraud review desk with alert queue screens | `counter`, `person`, `monitor` (`tiles` alert queue), `wallScreen`, `link` (payment to model), `ring` | `terminal` (card reader with a glyph screen), `card` (payment card), `shopShelf` |
| Demand Forecasting, `forecast` (#6) | A planning meeting decides next week's stock from the forecast; a warehouse receives it | A planning room with a table and a wall display; a warehouse aisle | `wallScreen` (line chart with a threshold), `desk` (as a meeting table), `chair`, `person`, `link` (forecast to warehouse) | `palletRack`, `pallet`, `forklift` (simple) |

Shared across all five: people (staff, customers, reviewers), desks, chairs, monitors and phones with glyph screens, the data `link`, status `ring`s, the server `rack` for the AI service, and the wall display for monitoring and evidence. Rooms use `room({w, d, h})` with an open front, so the camera can see in from outside or above.

---

## 5. Props kit reference

Every helper is on the `kit` object passed to `build()` and `update()`. Units are metres; `y` is up and the floor is at 0. Furniture and people face `+z`; rotate them with `ry`.

### Maths and materials

| Group | Helpers |
|---|---|
| Maths | `clamp`, `lerp`, `smooth`, `ease` (quintic), `ramp(t, a, b)` (smooth 0 to 1 between a and b), `lin`, `frac`, `tri`, `rng(seed)` (deterministic), `V(x, y, z)`, `PI` |
| Primitives | `box(color, sx, sy, sz, x, y, z, parent, opt)`, `cyl(color, r, h, ...)`, `sph(color, r, ...)`, `mesh(geo, ...)`, `grp(x, y, z, parent)`, `mat(color, opt)` (cached Lambert), `emis(color, intensity)` (emissive, not cached) |
| Colliders | `coll(x0, y0, z0, x1, y1, z1, label)`, and `collBox(x, z, w, d, h, ry, label)` for a footprint that is rotated |
| Palettes | `PAL` (ground, floor, walls, wood, desk, metal, five skin tones, six hair colours, shirt and trouser colours by role); `STATUS` (`ok`, `warn`, `fault`, `ai`, `idle` as CSS colours) |
| Lights | `lights.hemi`, `lights.sun`, `lights.fill`. They may be changed in `update()`; they are restored every frame. |

### Sets

| Helper | Builds |
|---|---|
| `room({w, d, h, x, z, floor, wall, back, left, right, ground})` | A floor, back and side walls (each can be turned off) and an outer ground plane, with wall colliders. |
| `windowPane({x, y, z, w, h, ry})` | A daylight window. |
| `door({x, z, ry})` | A door. |
| `desk({x, z, ry, w, d, h})` | A desk. |
| `counter({x, z, ry, w, d, h})` | A counter. |
| `chair({x, z, ry, color})` | A chair. |
| `shelf({x, z, ry, w, h, seed})` | A bookcase with coloured binders. |
| `plant({x, z, s})` | A potted plant. |
| `rack({x, z, ry})` | A server rack; call `.set(t, on)` for blinking LEDs. |
| `tag({x, y, z, color})` | A colour plate. |
| `ring({x, z, r})` | A status ring on the floor; `.pulse(t, color, k, steady)`. |
| `link({from, to, lift, n})` | A data arc; `.set(t, k, reverse, color)` makes packets flow along it. |

### Glyph screens

`monitor({x, z, deskH, ry, w, h})`, `wallScreen({x, y, z, ry, w, h})`, `phone({parent | x, y, z})` and `glyphScreen(w, h, opt)` each return a screen. Call `screen.show(spec)` in `update()`. Spec fields, all optional:

| Field | Draws |
|---|---|
| `bg`, `header` | The background, and an app bar in this colour. |
| `rows`, `lit` | Text-like strokes, of which the first `lit` are filled in. |
| `mark: {row, color}` | One row highlighted. |
| `tiles: [colours]` | A queue of cards instead of rows. |
| `bars: [0..1]`, `barColor`, `threshold`, `over` | Bars; those above the dashed threshold are drawn in `over` (red by default). |
| `line: [0..1]`, `lineColor` | A line chart. |
| `progress`, `progressColor` | A progress bar. |
| `badge: {glyph, color}` | A badge. Glyphs: `check cross warn clock loop person shield lock dot`. |
| `off` | The screen is dark. |

Screens repaint only when the spec changes, with values rounded to 0.01. To keep repaints rare, quantise slowly changing data, for example to half-seconds.

### People

`person({shirt, trousers, skin, hair, longHair, headset, badge, sleeves, shoes})` returns an articulated figure that faces `+z`. Its `userData` holds `body`, `head`, the arms `la`, `ra` with elbows `le`, `re`, the legs `ll`, `rl` with knees `lk`, `rk`, and the hand anchors `handL` and `handR` (attach a phone with `phone({parent: p.userData.handR})`). Every person counts for the camera clearance check.

Poses:

| Helper | Pose |
|---|---|
| `place(p, x, z, ry)` | Stands the person at a point, facing `ry`. |
| `walk(p, [[x, z], ...], u, t)` | Walks along a polyline with a gait; `u` runs 0 to 1. |
| `sit(p, k)` | Sits on a chair at the same point; `k` runs 0 to 1. |
| `typing(p, t, k)` | Types. |
| `holdPhone(p, k)` | Holds a phone. |
| `point(p, k)` | Points. |
| `gesture(p, k, t)` | Raises a hand. |
| `look(p, yaw, pitch)` | Turns the head. |

A seated person faces the same way as their chair.

### Camera

`camKeys(keys, lt)`, `camAim(...)`, `camAimLevel(...)` and `camOrbit(cx, cy, cz, r, h0, h1, a0, a1, u, ly)` are described in section 1.6.
