# Retail Credit Risk Scoring — Script and Protocols

Governing sources: the AI Canvas for `rcr` in `CANVASES` and the initiative's governance record in `index.html` (`INITIATIVES`, `PEOPLE`, `RISKS`, `INCIDENTS`, `DECISIONS`, `EVIDENCE`, `IMPACTS`, `CONTROLS`, `MODELS`, `SYSTEM_CARDS`, `DIAGRAMS`, `DATASOURCES` / `INIT_SOURCES`, `ASSETS`, `SOURCING`, `CHANGE`, `WAVES`, `MEETINGS`, `REGS`), read as data and not changed. Plan and acceptance criteria: GitHub issue #2 (phase 1 of the Retail Credit Risk Scoring film), parent issue #1 (shared approach, beat structure, runtime target). Format and conventions only: `simulation/Village Film C - Three Questions - Script and Protocols.md`. This film is **not** a scene in Village Film C and is **not** set in the robot village: it is set where the model is actually used, in a personal-loan application, at an underwriting desk, in a contact centre, at a model-risk desk and at the governance board.

Runtime 59 s: open card 4 s → Beat 1 The situation 8 s (shots 4 / 4) → Beat 2 The AI at work 14 s (4 / 5 / 5) → Beat 3 What can go wrong 14 s (5 / 4 / 5) → Beat 4 How it is kept safe 15 s (5 / 5 / 5) → close card 4 s. The four beats run 51 s, inside the 45-60 s target of issue #1; the two cards add 8 s. Every shot is its own scene in `FILM.scenes`; cuts land exactly on shot boundaries. Autoplay, loop, seekable (a pure function of t).

All numbers in this document are **design parameters** unless they are labelled as taken from the record (they then carry the record id, for example "four points (n6)" or "AUC 0.81 (system card `md-credit`)"). No results are reported anywhere: the film stages events that are already in the governance record and the controls the record commits to, and the hypotheses in Part 2 are pre-registered predictions for a simulation that has not been run. Nothing on screen claims that an incident is closed, a risk is mitigated or a test has passed.

---

## The record this script is built from

### AI Canvas (7 of 7 blocks filled)

| Block | Canvas text (verbatim) | Where the film uses it |
|---|---|---|
| Business Problem | Manual retail credit review is slow and inconsistent, driving delay and applicant drop-off at the point of decision. | Shot 3 |
| Business Value | Cuts decision latency from days to minutes and standardises the basis of a decline, which is also what makes it contestable. | Shots 1, 6, 10, 13 |
| Objective Function | Probability of 90-day default, predicted from bureau history, affordability and account-behaviour features. | Shots 4, 5 |
| Modeling Approach | Gradient-boosted trees with a monotonic constraint on affordability, plus a calibration layer. | Shot 5 |
| Model Training | Quarterly retrain on a rolling 36-month window; challenger runs shadow before promotion. | Shots 8, 11 |
| Customer Value | A same-session answer with reason codes the servicing channel can actually read back. | Shots 6, 7, 10 |
| Data Strategy | Bureau feed and internal account history into the customer feature store; no special-category data. | Shot 4 |

### Governance record for `rcr`

| Record | Content (from `index.html`) |
|---|---|
| Initiative `rcr` | Retail Credit Risk Scoring. Stage Pilot, tier High, BU Retail Banking, disposition "Conditions" (amber), value "On track", sourcing build-in-house, no supplier. Summary: "A gradient-boosted scoring model that speeds up retail credit decisioning ahead of a board decision to scale." Regulations: `eu-ai-act` (requires A.5, A.6, A.8, A.9), `gdpr` (A.7), `iso-23894` (A.5, A.6). Assets: `as-emb` (consumes), `as-fs` customer feature store (contributes). |
| People by role | Owner **Maria Okafor**, Head of Credit Risk Analytics (owner of r2, e1; owner of control A.9). Sponsor **David Chen**, COO Retail Banking (change owner; board competence seat). Model owner **Jonah Park**, ML Engineering Lead (owner of `md-credit`, its system card, r3, e2). **Marcus Webb**, Head of Model Risk (raised n6; owner of control A.6; AIMS-manager seat). **Tomas Berg**, Data Protection Officer (raised n4; owner of controls A.5 and A.8; impact-assessment seat). **Priya Nandakumar**, Chief Risk Officer (took d2; AI-risk-owner seat; owner of A.10). **Alicia Reyes**, Board Chair (chairs `bm-q2` and `bm-jul`). Underwriter and servicing agent appear in the record only as roles (system card "underwriter"; canvas "servicing channel"); they have no `PEOPLE` entry and stay unnamed here. |
| Impact assessment | Status in-progress. Scope: "Automated credit decisioning for retail applicants, with a human override path." Entries: economic harm to individuals, possible / major, "Exclusion from credit following a mis-scored application"; discrimination against groups, possible / major, "Disparate approval rates across protected attributes." |
| Risk **r2** | Disparate impact in credit approval across protected groups. Harm discrimination, possible / major, Test & Evaluate, control A.5, owner Maria, status "Mitigation in progress", treatment mitigate with 30-day review, decision d2. Why: "A model that systematically declines a protected group is both a fair-lending and an EU AI Act high-risk exposure." |
| Risk **r3** | Model drift undetected between quarterly reviews. Harm safety, likely / moderate, Operate & Monitor, control A.6, owner Jonah, status "Monitor planned", treatment mitigate with 90-day review, no decision. Why: "Retail credit behaviour shifts with rates — a stale model quietly mis-scores a widening share of applicants." |
| Incident **n4** | Model `md-credit`, classification rights-impact, reportable, Operate & Monitor, raised 2026-06-24 by Tomas, status **open**, risk r2. "Applicant contested an automated decline with no explanation available." Root cause: "Reason codes not surfaced to the servicing channel." |
| Incident **n6** | Model `md-credit`, classification performance-drift, not reportable, Operate & Monitor, raised 2026-07-05 by Marcus, status **open**, risk r3. "Approval rate drifted four points after the June rate change." Root cause: "Affordability features shifted faster than the quarterly retrain." |
| Decision **d2** | Risk treatment on r2, by Priya, 2026-06-12, at `bm-q2`: "Mitigate: re-weight the flagged cohort and re-test before the scale decision; review every 30 days." |
| Board sessions | `bm-q1` (2026-04-03, held) reviewed rcr, no gate items. `bm-q2` Q2 governance board (2026-06-12, held, chair Alicia, seven seats present) minuted "Credit scoring mitigation agreed." `bm-jul` Q3 governance board (2026-07-10, status scheduled, chair Alicia) lists rcr for review. |
| Evidence **e1** | Bias audit "Fair-lending disparity test, Q2", owner Maria, control A.5, captured 2026-06-18, due 2026-09-18: "Four-fifths rule tested across five protected attributes; two cohorts within tolerance, one flagged for re-test." |
| Evidence **e2** | Model card "Credit scoring model card v3", owner Jonah, control A.8, captured 2026-06-02, no due date: "Intended use, out-of-scope use, training window, calibration method and known limitations." |
| Controls | A.5 impact assessment (in-progress, Tomas); A.6 AI life cycle (in-progress, Marcus); A.7 data for AI systems (in-progress, Leah Simmons); A.8 information for interested parties (**not-started**, Tomas); A.9 use of AI systems and human oversight (in-progress, Maria); A.10 third-party relationships (in-progress, Priya). |
| Model `md-credit` | Retail credit GBM 3.2, Classification, in-use, in-house, conforms to the reference stack, asset `as-fs`. Note: "Gradient-boosted trees with a monotonic affordability constraint and a calibration layer." (`md-embed`, the shared document embedding model, also lists rcr; no canvas block or diagram node uses it, so the film does not stage it.) |
| System card `md-credit` | Reviewed 2026-06-02. Intended use: "Score retail credit applications to support, never replace, an underwriter decision." Out of scope: commercial lending, collections prioritisation, any use on an existing customer's held facility. Training data: "36 months of internal account history plus bureau features; no special-category attributes." Evaluation: "AUC 0.81 on a held-out quarter; calibration checked per decile; four-fifths disparity test per protected attribute." Limitations: "Thin-file applicants are under-represented; performance degrades when rates move sharply." Oversight: "Every decline above the threshold is reviewable by an underwriter, with reason codes." |
| Diagram `rcr` | Application intake → customer feature store ← bureau feed; feature store → credit GBM scorer → (score + reasons) → calibration + reason codes → underwriter review → (decision) → core banking decision; scorer ⇢ (weekly) drift + disparity monitor → model risk alert. |
| Data sources | `ds-core` Core banking accounts (Financial transactions, high sensitivity, personal data) and `ds-bureau` Credit bureau feed (Third-party / purchased data, high sensitivity, personal data, via "Bureau API"), both feeding `as-fs`. The bureau provider is not named in the record and has no `SUPPLIERS` entry; the film does not name one. |
| Sourcing | build-in-house: "The scoring logic is the lending policy — it has to be inspectable and defensible in an appeal, so it is not bought." |
| Change | Owner David, ambition Reshape, ADKAR awareness 85, desire 60, knowledge 55, ability 30, reinforcement 10. Interventions: "Underwriter shadow-scoring week", "Reason-code reading guide for servicing", "Floor-walker support for the first two weeks". |
| Wave objective | `w1-o1` (wave 1 "Prove it"): "Cut retail credit decision time to under an hour", measured as median time to decision. |

---

## Usage situation

The film follows one fictional applicant through one real use of the model, then steps behind the counter to the people who watch it.

| Element | In the film | Traces to |
|---|---|---|
| Who applies | **Nadia** (fictional), 31, a home-care nurse who has banked with the bank for four years, so it holds her account history. Her old car has broken down and she needs a small personal loan to replace it (staged: €6,000 over 36 months; a design parameter). Nothing on screen or in this document gives Nadia a protected characteristic, and the flagged cohort in shot 9 is never linked to her. | Business Problem ("applicant"); Data Strategy (internal account history) |
| Where and when | At her kitchen table, on her phone, in the bank's app, at about nine in the evening after a late shift (staged). | Customer Value ("same-session answer") |
| Trigger | She submits the loan application in the app. Application intake pulls her bureau file and her account history into the customer feature store. | Diagram `rcr` (application intake, bureau feed, feature store); Data Strategy |
| What the AI outputs | A calibrated probability that she defaults within the 90-day definition, and the reason codes behind it (staged as three codes, one per feature family: affordability, bureau history, account behaviour). | Objective Function; Modeling Approach; diagram node "Calibration + reason codes" |
| Who acts on it | An **underwriter** checks the score and its reasons and confirms the decision inside the session; her app shows the answer the same evening: declined, with a way to call. Next morning she calls the contact centre to contest it; a **servicing agent** must read the reasons back and can open an underwriter review (the human override path). | System card intended use and oversight; impact-assessment scope ("with a human override path"); Customer Value; n4 |
| Behind the scenes | At the **model-risk desk**, the June rate change has moved approvals by four points (n6) and the quarterly retrain will not catch it in time (r3); the planned weekly drift and disparity monitor is the control. The Q2 **fair-lending test** has flagged one cohort (e1, r2). The **governance board** has decided to re-weight and re-test that cohort before it decides whether to scale (d2), reviewing every 30 days. | n6, r3, diagram monitor node, Model Training; e1, r2, d2, `bm-q2`, `bm-jul` |

What the film deliberately leaves open: whether Nadia's own decline was right. The impact assessment's first harm is "exclusion from credit following a mis-scored application"; the film shows that she can get her reasons and ask a person to look again, not what the person decides.

## Canvas assumptions

None. All seven canvas blocks for `rcr` are filled in `index.html`, so no block had to be drafted. The film does need a few **staging assumptions**, which are choices about how to show the record, not additions to it. Each is labelled for review:

| id | Staging assumption | Why it is needed | Record it rests on |
|---|---|---|---|
| SA1 | Nadia, her job, the car and the loan size (€6,000 over 36 months) are fictional. | A usage film needs one concrete applicant. | Issue #1 ("fictional applicants/customers are fine") |
| SA2 | Three reason codes per decision, one for each feature family. | The record says "reason codes" but gives no count. | Objective Function; system card oversight |
| SA3 | The app shows the decision and a call option; the reasons reach Nadia when the servicing channel reads them back. | The record does not say whether the app itself displays reason codes. | Customer Value; n4 root cause |
| SA4 | The underwriter confirms each decline inside the session. | The diagram routes every decision through "Underwriter review" and the system card says the model supports, never replaces, an underwriter. | Diagram `rcr`; system card (see Open points: n4 calls the decline "automated") |
| SA5 | The n6 drift is drawn as a fall in the approval rate. | A line has to move one way; the record gives the size (four points), not the direction. | n6 |
| SA6 | The fairness test is drawn as three cohort bars, two within tolerance and one flagged. | e1 reports "two cohorts within tolerance, one flagged" from a test across five protected attributes; the per-attribute breakdown is not in the record. | e1 |
| SA7 | The weekly drift and disparity monitor is pictured working in Beat 4, as an illustration of the intended control; its headline calls it planned. | It is the control the record intends; r3's status is "Monitor planned". The picture shows what it is for, the words say it is not yet in place, and so does Part 2. | Diagram `rcr`; r3 |
| SA8 | Reason codes on the servicing screen (shot 10) are shown as the required state ("must show"). | n4 is open; the canvas Customer Value and the change intervention "Reason-code reading guide for servicing" describe the target. | n4; Customer Value; `CHANGE.rcr` |
| SA9 | The re-test under d2 is shown as pending (an outlined, dashed bar and an hourglass), never as passed. | d2 is a decision to act; no re-test result is on file. | d2; r2 status "Mitigation in progress" |

## Open points for review

The record is consistent enough to script, but these nine points should be confirmed by the owners before phase 2, because the film draws them:

1. **Automated or reviewed?** The system card says the model supports, never replaces, an underwriter decision; the impact-assessment scope says "automated credit decisioning … with a human override path"; n4 says the applicant contested an "automated decline". The script follows the diagram (every decision passes underwriter review, SA4). Owner: Maria (A.9), with Tomas (A.5).
2. **Which declines are reviewable?** The system card says "every decline above the threshold is reviewable by an underwriter". The film shows a review being offered to Nadia without saying which side of the threshold she is on. Owner: Jonah.
3. **e1's scope.** Five protected attributes tested, three cohorts described. The film shows only the three cohorts (SA6). Owner: Maria.
4. **A.8 is not started**, although e2 (model card) is filed against it and reason codes are the transparency ask behind n4. Owner: Tomas.
5. **r3 has no decision**, and its monitor is "planned". The film shows the monitor as the intended control (SA7). Owner: Jonah, with Marcus (A.6).
6. **The bureau feed has no supplier record**, although it is third-party purchased data (A.10). The film does not name a bureau. Owner: Priya.
7. **`md-embed` lists rcr** but no canvas block or diagram node uses it. Not staged. Owner: Leah.
8. **Dates around d2.** d2 (2026-06-12, `bm-q2`) decides to re-weight "the flagged cohort", but e1, the test that flags it, is dated 2026-06-18, six days later. The film shows no dates and keeps the order test → decision; the owners should say whether an earlier test run flagged the cohort or e1's date is the filing date. Owner: Maria, with Priya.
9. **Direction of the June rate change and of the drift.** n6 gives neither. The film draws the rate marker without a direction and the drift as a fall (SA5). Owner: Marcus.

---

## Part 1 — Shot script

Conventions: `start` and `dur` in seconds. The camera never enters geometry: in the room sets (kitchen, desks, contact centre, board room) it keeps **≥ 0.6 m** from every collider and **≥ 0.9 m** from every human figure, and in the abstract "inside the scoring system" set **≥ 1.5 m** from every object, verified by `FILM.clearance(t)` at 0.1 s steps (design parameters, scaled down from the Village Film's 2.5 m because these sets are rooms, not a village). All readable text lives in the HTML overlay. Nothing in-world carries words the viewer must read: the phone, monitors, wall dashboards, paper files and board papers show only glyphs, bars, dials, pips and colours. Human figures are low-poly and faceless, in the same style as the Village Film's real-world vignettes; nobody's name appears anywhere on screen except the fictional applicant's first name in the overlay. Inset frames (Nadia's phone beside the underwriter's monitor in shot 6, Nadia at home in shot 7) are small framed dioramas placed in the world, built from the same props; no render-to-texture or second camera is needed.

**Colour carries the meaning in-world, the same in every shot:**

| Colour | Meaning |
|---|---|
| Ice blue `#9fc6d6` | Data moving: bureau and account packets, features flowing into the store and the scorer |
| Green `#3fa34d` | Approved, or within tolerance |
| Slate `#7a8691` | Declined. A decline is a normal outcome, not a fault, so it is never red |
| Amber `#e9a23b` | Sent to a person, or flagged for a closer look: underwriter review, a model-risk alert, the flagged cohort |
| Red ring `#d84a3a` | A fault from the record: a red ring pulses on the floor, desk or screen where it happens (shots 7, 8, 9 only) |
| Translucent white, dashed outline | Shadow: the challenger model, whose outputs never reach a customer |

**Glyph vocabulary** (in-world, no words): decision tick in a circle (approved, green); circle with a bar (declined, slate); three **reason chips**, each a rounded tile with an icon and a bar whose length shows its weight: a wallet (affordability), a clock over a document (bureau history), a card with a wave (account behaviour); a handset (call us); a stack of small trees (the gradient-boosted model); a ring lens (calibration); a semicircular dial with a needle (the probability); a one-way slider with an arrow (the monotonic affordability constraint); a line chart inside a band (approval rate and its tolerance); bars with a dashed line at four-fifths (the fairness test); an hourglass (pending); a calendar ring of 30 pips (review cadence); a closed barrier gate with an amber lamp (the scale-up gate).

**Overlay:** top-left, the setting on its own small scrim pill (see the table); top-right, `Retail Credit Risk Scoring` (blank on the open and close cards). Under the headline area sits the four-step beat indicator `The situation → The AI at work → What can go wrong → How it is kept safe` on its own dark pill, with the current beat lit in a pale tint of the beat's accent; at phone width it shows the current beat in words and the other three as dots. Then one headline, at most one support line, and a thin rule in the beat's accent colour. The open and close cards show no beat indicator. The `data-caption` element carries the headline and its support line for every scene. The beat indicator, playback bar (previous scene, play/pause, next scene, scrubber with one segment per beat in its accent and a neutral segment for each card, a tick at every shot, keyboard hint `Space` pause/play and `← →` scenes, the time, restart set apart), `Paused` pill, scene navigation rail (Introduction, the four beats with their shots by setting name, Close) and phone-width behaviour follow the Village Film exactly. On the last scene the caption holds while the picture fades to black, so caption and picture leave together.

**Fallback:** if WebGL cannot start, the page shows the open headline (`A loan can be decided in minutes, with checks around it.`), the note `This film needs 3D graphics (WebGL). Your browser could not start it. Here is the film in words.`, and then every scene by beat and setting name (for example `What can go wrong — The contact centre`) with its headline and support line exactly as below; no scene numbers and no times.

### Numbering convention

The film has one initiative, told in four **beats** and thirteen **shots** (eleven in the beats, plus the open and close cards). Beats are named by words only, on the beat indicator; shots are named by their setting. The shot numbers in this document are for reference and never appear on screen; no label anywhere on screen carries a digit. Numbers appear on screen only inside sentences, and only where they come from the record: "90 days" (Objective Function), "four points" (n6), "four-fifths" (e1), "30 days" (d2), and "three main reasons" (SA2). The time readout `0:00 / 0:59` is a clock, not a label.

Accent colours (the overlay rule and the beat's scrubber segment): open and close neutral `#e8e6e1`; The situation and The AI at work, credit blue `#4a7fd4`; What can go wrong, red `#d84a3a`; How it is kept safe, green `#3fa34d`.

### Sets

| Set | Shots | Can be shared with |
|---|---|---|
| K1 Nadia's kitchen at night: table, phone, a car key on the table, a window with a street lamp and the broken-down car under it | 2, 13 | — |
| K2 The old review desk: paper files in stacks, an in-tray, a wall clock, two desaturated clerk figures | 3 | Fraud Triage Model (#5) analyst desk |
| K3 Inside the scoring system: an abstract dark space with the feature store (a lit cabinet of drawers), the tree stack, the calibration ring, the dial | 4, 5 | — |
| K4 The underwriting desk: one desk, two monitors, an underwriter figure, an amber review tray. It stands at the back of the K5 floor, so shot 10 can pan from the agent to the tray without a cut (shot 6 lights it for night, shot 10 for morning) | 6, 10 | Fraud Triage Model (#5) review desk |
| K5 The contact centre: a pod of four desks, headsets, the servicing agent's monitor | 7, 10 | Customer Service Copilot (#3) |
| K6 The model-risk desk: two figures (a third, from credit-risk analytics, stands at the fairness panel in shot 9), a wall dashboard (approval-rate chart, fairness bars, a quarterly calendar strip), a desk lamp that can turn amber | 8, 9, 11 | Fraud Triage Model (#5); Demand Forecasting (#6) planning room |
| K7 The board room: a table with seven seats, board papers, a wall screen | 12 | All five initiative films |

### Shots

| # | start s | dur s | beat | setting (top-left, exact) | camera | world action (what is visibly on screen) | headline (exact) | support line (exact) | accent | traces to |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 4 | Open | `A loan in minutes` | Slow crane down from 2.6 m to 1.7 m outside Nadia's kitchen window at night; the camera stays outside (≥ 0.6 m from the wall and frame) and ends framed by the open window, her lit phone upper right | A street lamp, the broken-down car at the kerb with its hazard lights blinking; inside, Nadia sits at the kitchen table, the phone lighting her hands | A loan can be decided in minutes, with checks around it. | We follow one loan from a phone to the board room. | neutral | Business Value; initiative summary |
| 2 | 4 | 4 | The situation | `At home, in the banking app` | Over-the-shoulder at 1.3 m, 1.0 m behind and right of Nadia, slow push-in to the phone; the phone is aimed into the upper right (offset +0.25 / +0.2), the table lower left | The app screen shows glyphs only: a car icon, a coin stack and a slider set to the loan size, a term ring; she drags the slider, taps the submit glyph; a spinner ring starts | Nadia needs a small loan to replace her broken-down car. | She applies in her banking app after a late shift. | credit blue | Business Problem (the applicant at the point of decision); usage situation |
| 3 | 8 | 4 | The situation | `The old way: by hand` | Contrast vignette, desaturated: slow lateral dolly at 1.5 m along the old review desk, 1.8 m back | Paper files pile up in the in-tray; the wall clock's hands spin through several days; two clerks lift the same file and give it opposite marks (one slate bar, one green tick); in a small inset window frame on the desk edge, a phone like Nadia's goes dark and is put face down (the applicant gives up) | Checking loans by hand takes days. | Some applicants give up, and two staff can judge one file in two ways. | credit blue | Business Problem ("slow and inconsistent … applicant drop-off") |
| 4 | 12 | 4 | The AI at work | `Inside the scoring system` | Abstract set; the camera follows the data from 4 m back at 2.2 m height, a smooth arc toward the feature store, aimed upper right (offset +0.2 / +0.15) | Two streams of ice-blue packets arrive: one from a bureau glyph (a document with a clock), one from a bank-vault glyph (her four years of account history); they drop into drawers of the lit feature-store cabinet. Off to one side, a single grey token marked with a crossed-out circle stands apart with no path to the cabinet: no special-category data is part of the feed | The model reads her credit file and how she uses her account. | It never uses data on health, religion or race. | credit blue | Data Strategy; Objective Function (bureau history, account behaviour); `ds-bureau`, `ds-core`; diagram (intake, bureau feed, feature store) |
| 5 | 16 | 5 | The AI at work | `Inside the scoring system` | Continues from the cabinet: slow orbit of 30° around the tree stack at 1.8 m, 3.5 m out | Features leave the cabinet as packets and pass through a stack of small trees (the gradient-boosted model), each tree briefly lighting; one packet carries the wallet glyph and rides a one-way slider: as the wallet shrinks, the arrow moves the dial needle only toward higher risk (1.5-3.0 s). The stack's output passes through the calibration ring lens, and the needle settles on the probability dial (3.5-4.5 s) | It estimates how likely she is to fall 90 days behind on her loan. | If she can afford less, her risk score can never go down. | credit blue | Objective Function (probability of 90-day default); Modeling Approach (gradient-boosted trees, monotonic affordability constraint, calibration layer); `md-credit` |
| 6 | 21 | 5 | The AI at work | `The underwriting desk` | Over-the-shoulder at 1.4 m, 1.1 m behind the underwriter, then a 1.2 s cut-in-style push (no cut) to frame the monitor upper right and Nadia's phone in a small picture-in-picture glyph frame lower right of the monitor | The underwriter's monitor shows the dial and three reason chips (wallet, clock-over-document, card-with-wave) with bars of different lengths, and an untouched amber override handle; the underwriter studies it, taps confirm (2.5 s); in the picture-in-picture frame Nadia's spinner resolves into the slate declined glyph and a handset glyph (3.5 s) | Then an underwriter checks the score and the three main reasons for it. | That evening, Nadia's app tells her the answer is no. | credit blue | Customer Value (same-session answer); diagram (calibration + reason codes → underwriter review → core banking decision); system card intended use; SA2, SA3, SA4 |
| 7 | 26 | 5 | What can go wrong | `The contact centre` | Morning light; wide establishing at 1.6 m on the pod from 2.4 m, then a slow push that stops 1.0 m behind the agent, monitor aimed upper right (offset +0.25 / +0.2) | Nadia, at home with her coat on, holds her phone to her ear (small inset frame, upper left); a ringing pulse reaches the agent's headset; the agent's monitor shows Nadia's decision record with the slate declined glyph, and beside it three **empty** reason-chip slots, dashed; a red ring pulses around the empty slots (2.0 s); the agent spreads both hands | Next morning Nadia calls to ask why, but the agent sees no reasons. | The reasons stayed in the scoring system and never reached the agent's screen. | red | **Fault F1** = incident **n4** (rights-impact, reportable, open; root cause "reason codes not surfaced to the servicing channel"); risk r2; impact-assessment entry 1; Customer Value (the gap) |
| 8 | 31 | 4 | What can go wrong | `The model risk desk` | Static three-quarter view at 1.5 m, 2.2 m from the wall dashboard, a slow 3 % push; dashboard upper right | A calendar strip on the wall shows a rate-change marker (a percent glyph with a step mark; the record gives no direction for the change) in June; on the approval-rate chart the line steps out of its band by a visible gap (four grid steps, one per point; SA5) just after the marker (1.0-2.0 s), and a red ring pulses on the gap; the next quarterly-retrain marker sits far to the right of the strip; the desk lamp stays dark | After the June rate change, approvals drift by four points. | Between quarterly retrains, a shift like this can go unseen. | red | **Fault F2** = incident **n6** (performance-drift, open; root cause "affordability features shifted faster than the quarterly retrain"); risk **r3**; Model Training (quarterly retrain); system card limitation ("degrades when rates move sharply") |
| 9 | 35 | 5 | What can go wrong | `The fair-lending test` | Turns from the chart to the dashboard's second panel: slow pan at 1.5 m, 2.0 m out, panel upper right | A third figure (the credit-risk analytics team that owns the test) stands at the panel. Three cohort bars rise one after another (0.5 / 1.2 / 1.9 s) against a dashed line at four-fifths of the highest bar; two end above the line in green; the third stops below it and turns amber, a red ring pulsing at its foot (2.6 s); a small flag glyph pins to it | A fairness test flags one group of applicants for a closer look. | Its approval rate is below four-fifths of the highest group's rate. | red | **Fault F3** = risk **r2**; evidence **e1** (four-fifths rule; one cohort flagged for re-test); impact-assessment entry 2; SA6 |
| 10 | 40 | 5 | How it is kept safe | `The contact centre` | Same pod as shot 7 and the same push, so the change is the only difference; then a 1.5 s pan to the underwriting desk in the background, aimed upper right | The agent's monitor now shows the three reason chips filled in their slots, beside a small reading-guide glyph (an open booklet); the agent points to each chip in turn as a speech glyph with the matching icon rises from the headset (0.8-2.6 s); the agent taps the amber review glyph and an amber ticket travels across the room into the underwriter's review tray (3.0-4.5 s) | The agent's screen must show the reasons, so they can be read back. | Nadia can ask an underwriter to look at her case again. | green | n4 remediation target (SA8); Customer Value; Business Value ("what makes it contestable"); system card oversight; impact-assessment scope (human override path); controls A.8, A.9; change intervention "Reason-code reading guide for servicing" |
| 11 | 45 | 5 | How it is kept safe | `The model risk desk` | Same view as shot 8, then a slow dolly left at 1.5 m to bring the second monitor into frame upper right | A weekly tick mark sweeps along the approval-rate chart; at the first tick after the rate-change marker the desk lamp turns **amber** and an amber alert glyph lands on the desk (1.0 s) (SA7); on the second monitor, the tree stack runs beside a **translucent dashed copy** (the challenger) on the same packets, and the copy's outputs fall into a dashed tray that leads nowhere (2.0-3.5 s); along the bottom, a bar of 36 small segments (the rolling 36-month training window) slides three segments to the right, one quarter, at the retrain marker (4.0 s) | A weekly check is planned to catch drift and unfair results between retrains. | A new model runs in the shadow before it can replace the old one. | green | Diagram (weekly drift + disparity monitor → model risk alert); r3 treatment (mitigate, monitor planned); control A.6; Model Training (quarterly retrain, rolling 36-month window, challenger in shadow before promotion) |
| 12 | 50 | 5 | How it is kept safe | `The governance board` | Crane down from 2.4 m to 1.6 m over the end of the board table, 2.2 m from the nearest seated figure; wall screen upper right | Seven figures at the table (the seven seats present at `bm-q2`, where d2 was taken); two papers lie on the table, one with bars (the fairness test) and one with a card outline (the model card); on the wall screen, the flagged amber bar from shot 9 is redrawn as an **outlined, dashed** bar with an **hourglass** above it (pending re-test, SA9); a calendar ring of 30 pips fills once (1.0-3.5 s); beside it a barrier gate stays closed under an amber lamp | The bank re-weights that group and tests again before the scale decision. | Progress is checked every 30 days, with the fairness test on file. | green | Decision **d2** (by Priya at `bm-q2`: re-weight the flagged cohort, re-test before the scale decision, review every 30 days); r2 treatment; evidence **e1**, **e2**; controls A.5, A.8; `bm-jul` (next scheduled review of rcr) |
| 13 | 55 | 4 | Close | `What comes next` | Returns to Nadia's kitchen, now in morning light: camera at 1.1 m height, slow pull-back from 1.2 m to 2.4 m from the phone, ≥ 0.9 m from Nadia | Nadia puts her phone down after the call; it still shows the slate declined glyph and the handset glyph (the app shows no reasons, SA3). Above the phone a small amber ticket glyph with an hourglass hovers, a film device rather than an app screen, for the underwriter review the agent opened in shot 10; the outcome is never shown. The last 0.7 s fades to black with the caption, then the film loops | Answers should come fast, with reasons people can read and challenge. | Next gate: the board decides whether the pilot can scale. | neutral | Business Value; Customer Value; initiative summary ("ahead of a board decision to scale"); `bm-jul`; wave objective `w1-o1` |

### Word count and readability (on-screen text set by this script)

Counted as in the Village Film: by whitespace-separated tokens that contain a letter or a digit. Every line here is the team's own wording, so every limit is enforced: headline ≤ 14 words, support line ≤ 14 words, Flesch-Kincaid grade ≤ 8 (0.39 × words ÷ sentences + 11.8 × syllables ÷ words − 15.59, vowel-group syllable count, sentences counted at `.`, `!` or `?`). A new limit, needed because shots are short: **reading pace ≤ 5.5 words per second** of shot time (headline plus support line), which is the Village Film's own average (473 words in 86 s). The lines below should be stored as `test/credit-scoring-lines.json` in phase 2 and checked with the same readability tool before any build ships.

| shot | headline words | support words | words / s | FK headline | FK support |
|---|---|---|---|---|---|
| 1 Open | 11 | 11 | 5.5 | 5.9 | 3.7 |
| 2 At home | 10 | 10 | 5.0 | 6.0 | 4.8 |
| 3 The old way | 6 | 14 | 5.0 | 2.5 | 7.6 |
| 4 Inside, data | 12 | 9 | 5.3 | 5.8 | 7.6 |
| 5 Inside, score | 14 | 12 | 5.2 | 6.7 | 3.8 |
| 6 Underwriting desk | 13 | 10 | 4.6 | 5.8 | 4.8 |
| 7 Contact centre, fault | 13 | 13 | 5.2 | 4.9 | 6.7 |
| 8 Model risk, drift | 10 | 10 | 5.0 | 7.2 | 7.2 |
| 9 Fair-lending test | 12 | 11 | 4.6 | 5.8 | 8.0 |
| 10 Contact centre, fixed | 13 | 11 | 4.8 | 3.1 | 6.9 |
| 11 Model risk, monitor | 13 | 14 | 5.4 | 6.7 | 7.6 |
| 12 Governance board | 12 | 12 | 4.8 | 7.8 | 6.8 |
| 13 Close | 11 | 10 | 5.3 | 6.9 | 7.2 |
| **Total** | **150** | **147** | **297 words in 59 s (5.0 / s)** | max **7.8** | max **8.0** |

Fixed overlay furniture is not part of the count: the setting names top-left, the title `Retail Credit Risk Scoring` top-right, the beat indicator (`The situation → The AI at work → What can go wrong → How it is kept safe`, 15 words), the `Paused` pill, the labels and tooltips of the playback controls and the scene navigation, and the fallback note. No footnotes and no record ids (n4, r2, d2 …) appear on screen; they live in this document.

### Plain-language conventions

1. **Full sentences, never fragments.** Every line has its own subject and verb, in everyday words. The one colon line ("Next gate: …") is a full sentence after the colon.
2. **People first.** Beat 1 names the person with the stake (Nadia); Beat 3 says what went wrong for a person or a group before what went wrong in the model; Beat 4 says who can now do what (the agent can read the reasons back; Nadia can ask for a review; the board decides).
3. **Faithful tense.** Things that happened are in the record (n4, n6, e1, d2) and are staged as events. Controls that are intended but not yet in place are worded as such: the reasons on the servicing screen as the required state ("must show"), the weekly monitor as planned ("is planned to catch"), the re-test as still to come ("before the scale decision"), and the close as an aim ("should come fast"). Part 2 states their status. No line says an incident is fixed, a test passed or the model is fair.
4. **Jargon is replaced, not explained on screen.** The film words on the left stand for the record terms on the right:

| on screen | record term |
|---|---|
| "decided in minutes", "answers should come fast" | Business Value "cuts decision latency from days to minutes"; `w1-o1` median time to decision under an hour |
| "checking loans by hand takes days", "some applicants give up", "two staff can judge one file in two ways" | Business Problem: manual review "slow and inconsistent, driving delay and applicant drop-off" |
| "her credit file" | bureau history, `ds-bureau` Credit bureau feed |
| "how she uses her account" | account-behaviour features from internal account history, `ds-core` |
| "never uses data on health, religion or race" | Data Strategy "no special-category data"; system card "no special-category attributes" (health, religion and racial or ethnic origin are examples of special-category data) |
| "how likely she is to fall 90 days behind on her loan" | Objective Function "probability of 90-day default" (the exact default definition is in model card e2) |
| "if she can afford less, her risk score can never go down" | Modeling Approach "monotonic constraint on affordability" (monotonic: the score never moves the other way; the direction, worse affordability never lowering risk, is the usual one and is staged, not stated in the record) |
| "the three main reasons" | reason codes from the "Calibration + reason codes" node (count staged, SA2) |
| "an underwriter checks the score" | diagram "Underwriter review"; system card "support, never replace, an underwriter decision" |
| "that evening, Nadia's app tells her the answer is no" | Customer Value "a same-session answer"; diagram "Core banking decision" (how the app shows it is staged, SA3) |
| "the agent sees no reasons", "never reached the agent's screen" | n4 "no explanation available"; root cause "reason codes not surfaced to the servicing channel" |
| "after the June rate change, approvals drift by four points" | n6 "approval rate drifted four points after the June rate change" |
| "between quarterly retrains, a shift like this can go unseen" | r3 "model drift undetected between quarterly reviews"; Model Training "quarterly retrain" |
| "a fairness test flags one group" | e1 "fair-lending disparity test … one flagged for re-test"; r2 |
| "below four-fifths of the highest group's rate" | the four-fifths rule (adverse impact ratio < 0.80) |
| "the agent's screen must show the reasons, so they can be read back" | Customer Value "reason codes the servicing channel can actually read back"; n4 remediation target |
| "ask an underwriter to look at her case again" | human override path (impact-assessment scope); system card "reviewable by an underwriter, with reason codes" |
| "a weekly check is planned to catch drift and unfair results" | diagram "Drift + disparity monitor" (weekly) → "Model risk alert"; r3 status "Monitor planned" |
| "a new model runs in the shadow before it can replace the old one" | Model Training "challenger runs shadow before promotion" |
| "re-weights that group and tests again before the scale decision" | d2 "re-weight the flagged cohort and re-test before the scale decision" |
| "progress is checked every 30 days" | d2 "review every 30 days"; r2 treatment `reviewCadenceDays: 30`, owner Maria (the record does not say the board itself meets every 30 days) |
| "the fairness test on file" | evidence e1 (the model card e2 is shown as a paper on the table, not named on screen) |
| "next gate: the board decides whether the pilot can scale" | initiative summary "ahead of a board decision to scale"; stage Pilot; `bm-jul` |
| "reasons people can read and challenge" (worded as an aim, "should", because n4 is open) | Business Value "standardises the basis of a decline, which is also what makes it contestable" |

5. **What never changes in a rewrite:** the order of the four beats, the three faults and their record ids, the rule that a decline is slate and never red, the rule that the re-test is shown pending, and the rule that no result is stated anywhere on screen.

---

## Part 2 — Protocol

The film shows the decision path once, with three recorded faults. This protocol specifies how the same three faults would be **staged in a simulation** of the `rcr` decision path, to test whether the controls the record commits to would catch them. It runs on synthetic applicants and a replica model, never on the live scorer or on customer records. Its findings would support, not replace, the work the record already assigns: the re-test under d2 on the real model (Maria), the impact assessment (Tomas), and the monitor planned under r3 (Jonah). Nothing here has been run.

### Aim

Test, before the board's scale decision, whether three controls on the `rcr` decision path work when the faults already recorded against it are seeded: (1) reason codes reaching the servicing channel, so a declined applicant gets an explanation and a human review (against n4); (2) a weekly drift and disparity monitor, so a rate-driven shift is caught between quarterly retrains (against n6 and r3); (3) re-weighting the flagged cohort and re-testing it, so approval rates stay within the four-fifths rule without losing accuracy or calibration (against r2, as decided in d2).

### Why it matters to people

A personal-loan decision changes what someone can do next: replace a car, get to work, cover a gap. The canvas promises a same-session answer, and its Business Value line says the speed only counts if a decline is contestable. If the reasons do not reach the person who answers the phone, a fast "no" is a "no" nobody can explain (n4). If rates move and the model does not notice, more people are mis-scored every week until the next retrain (n6, r3). If one group is approved less often than others, the harm falls on that whole group (r2, impact assessment entry 2).

### AI-safety and governance question

When the model says no, can the applicant get reasons a person can read back and ask a person to look again; and will the bank notice, between quarterly retrains, when the model drifts or treats one group worse, before the board decides to scale it?

### Setting and props (simulation)

- **Replica decision path**, built in-house to the `rcr` diagram: application intake → feature store → scorer → calibration and reason codes → underwriter review → decision record, plus the weekly drift and disparity monitor and the model-risk alert. The scorer is a gradient-boosted tree model with a monotonic constraint on affordability and a calibration layer, trained on synthetic data with the same feature families as `md-credit` (bureau history, affordability, account behaviour). It is a replica, not `md-credit` 3.2; its numbers are not the production model's.
- **Synthetic applicant generator**: produces applications with bureau, affordability and account-behaviour features, a seeded default outcome at the 90-day definition, and a synthetic cohort label used **only** by the test harness (never passed to the scorer). Generator parameters are design parameters set by the team, not fitted to customer records.
- **Simulated time**: 13 simulated weeks = one quarter between retrains; 1,500 applications per simulated week (design parameter). The rolling training window is 36 simulated months of synthetic history, as in Model Training.
- **Servicing desktop mock-up** in a training room: the contact-centre screen showing the decision record, with or without the reason-code field (the arm), and the reading-guide card from the change intervention.
- **Underwriter review queue**: a mock-up of the review tray, staffed by role-play underwriters.
- **Model-risk dashboard**: approval rate per week with a tolerance band; population stability of the affordability features; adverse impact ratio per synthetic cohort.
- **Contest-call scripts**: fixed caller scripts for a declined applicant asking why, played by trained role-players reading from a card; each scripted case has a known decision record with its true reason codes.

### Actors (roles)

| Role | In the film | In the protocol | Person in the record |
|---|---|---|---|
| Applicant | Nadia (fictional), shots 1-2, 6-7, 10, 13 | Synthetic applicants; contest calls by role-players reading a fixed script | — (fictional) |
| Underwriter | Shots 6, 10 | Role-play underwriters from credit operations; confirm decisions and handle review tickets | — (role only) |
| Servicing agent | Shots 7, 10 | Role-play servicing agents from the contact centre, volunteers | — (role only) |
| Initiative owner; owner of r2, e1, A.9 | Figure at the fairness panel, shot 9 (the test owner's team) | Lead for fault F3 and for the human-override path | Maria Okafor, Head of Credit Risk Analytics |
| Model owner; owner of r3, e2 | Model-risk desk figure, shots 8, 11 | Builds and runs the replica, the generator and the monitor (F2) | Jonah Park, ML Engineering Lead |
| Model risk; raised n6; A.6 | Model-risk desk figure, shots 8, 11 | Signs off the pre-registration; independent review of F2 and F3 | Marcus Webb, Head of Model Risk |
| DPO; raised n4; A.5, A.8 | Board figure, shot 12 | Data gate G1; impact-assessment link; lead for F1 scoring | Tomas Berg, Data Protection Officer |
| Took d2; AI risk owner | Board figure, shot 12 | Receives results for the 30-day review | Priya Nandakumar, Chief Risk Officer |
| Board chair | Board figure, shot 12 | Results go to the next board session that reviews rcr | Alicia Reyes, AI Governance Board Chair |
| Sponsor; change owner | — | Owns the reading-guide and floor-walker interventions used in arm S1 | David Chen, COO, Retail Banking |

### Seeded faults

Every fault is a recorded incident or risk; none is invented.

| id | Fault (staged) | Record | Film shot | How it is seeded in the simulation |
|---|---|---|---|---|
| F1 | A declined applicant contests and the servicing channel has no explanation | Incident **n4** (rights-impact, reportable, open; root cause "Reason codes not surfaced to the servicing channel"); risk **r2**; impact entry 1 | 7 (fault), 10 (control) | In arm S0 the servicing desktop receives the decision record without the reason-code field, as at n4 |
| F2 | A rate change shifts affordability faster than the quarterly retrain | Incident **n6** (performance-drift, open; root cause "Affordability features shifted faster than the quarterly retrain"); risk **r3**; system card limitation | 8 (fault), 11 (control) | At the start of simulated week 4 the generator shifts the affordability features of new applications by a seeded amount sized so that, on the frozen replica, the weekly approval rate moves by four points, the size recorded in n6. The retrain stays at week 13 |
| F3 | One cohort's approval rate falls below four-fifths of the highest cohort's | Risk **r2**; evidence **e1**; impact entry 2; decision **d2** | 9 (fault), 12 (control) | The synthetic training sample under-represents one cohort so that its adverse impact ratio on the replica falls below 0.80 while two other cohorts stay within tolerance, mirroring e1's "two cohorts within tolerance, one flagged" |

Recorded material not seeded: the thin-file limitation in the system card (no risk or incident is recorded against it; reported as a covariate in F3), the out-of-scope uses in the system card, and anything involving `md-embed`.

### Procedure

1. **Before the first run:** pre-register this protocol (hypotheses, arms, measures, margins, seeds) with the model-risk function; Marcus and Tomas sign it off; the generator seed list is drawn and filed.
2. **Build check:** the replica passes the monotonic-affordability check (no applicant's score falls when only affordability worsens) and the per-decile calibration check on a clean synthetic hold-out before any fault is seeded.
3. **F1, contest calls:** 60 scripted contest calls (30 per arm) on decision records drawn from the replica, each with a known set of three reason codes. Agents are randomised to arm; each agent takes calls in one arm only. Calls are recorded for scoring and deleted after scoring.
4. **F2, drift replay:** 20 replay runs per arm, each 13 simulated weeks with a different seed; the shift starts at week 4; the arm decides whether the weekly monitor runs.
5. **F3, re-weight and re-test:** train the replica as is (W0) and with the flagged cohort re-weighted (W1), on the same synthetic training set and seed; evaluate both on the same synthetic hold-out with 1,000 bootstrap resamples.
6. **Throughout:** every simulated decline above the threshold is reviewable, as the system card's oversight line says, and can be sent to the role-play underwriter queue; overrides are logged.
7. **After:** export logs with checksums; two raters blind to arm score the F1 calls; results go to the next 30-day review under d2 and to the next board session that reviews rcr, whatever they show.

### Conditions / arms

- **F1. Arm S0, decision only:** the servicing screen shows the decision and no reasons (as at n4). **Arm S1, reasons surfaced:** the screen shows the three reason codes with the reading-guide card. Held constant: caller scripts, decision records, the review path.
- **F2. Arm M0, quarterly only:** no monitor between retrains; the first scheduled look is the week-13 retrain. **Arm M1, weekly monitor:** the drift and disparity monitor runs every simulated week and raises a model-risk alert when the approval rate leaves its band (±2 points around the four-week baseline) or the population stability index of any affordability feature exceeds 0.2 (both design parameters). Held constant: seeds, shift size and start week, retrain schedule.
- **F3. Arm W0, unweighted:** the replica as trained. **Arm W1, re-weighted:** the flagged cohort's training weight raised to match its share of the synthetic population (d2). Held constant: features, monotonic constraint, calibration method, hold-out set.

### Measures and logging

| Variable | Definition | Logged by |
|---|---|---|
| `reasons_read_back` | Per call: the agent states all three reason codes of the decision record correctly, in plain words (yes / no) | Two raters blind to arm; third rater on disagreement; agreement reported |
| `wrong_reason_stated` | Per call: the agent states a reason that is not in the decision record | Raters |
| `review_offered` | Per call: the agent offers an underwriter review | Raters; review-queue log |
| `time_to_reason_s` | Seconds from the caller's "why?" to the first correct reason | Call recording |
| `weeks_to_alert` | Simulated weeks from the shift (week 4) to the first model-risk alert; M0 is set to the week-13 retrain | Monitor log |
| `false_alert` | Alerts raised in weeks 1-3, before any shift | Monitor log |
| `decided_before_alert` | Applications decided on the shifted population before the first alert | Replica decision log |
| `approval_rate_shift_pts` | Weekly approval rate minus the four-week pre-shift baseline | Dashboard |
| `psi_affordability` | Population stability index of each affordability feature, weekly | Monitor |
| `air(cohort)`, `min_air` | Adverse impact ratio: a cohort's approval rate ÷ the highest cohort's approval rate; the smallest across cohorts | Test harness |
| `auc`, `calib_err_decile` | Discrimination and mean absolute calibration error across deciles, on the synthetic hold-out | Test harness |
| `monotonic_ok` | The monotonic-affordability check still passes after re-weighting | Test harness |
| `thin_file_share` | Share of thin-file synthetic applicants per cohort (covariate) | Generator |
| `override_count` | Underwriter decisions that differ from the replica's | Review queue |
| `live_system_touched` | Any read from or write to a production system or customer record (must be 0) | Infrastructure audit log |

### Pre-registered hypotheses

Not on screen: the film shows the recorded events and the intended controls, and states no prediction and no result.

- **H1 (F1, n4):** If the reason codes reach the servicing screen with the reading guide (S1), then agents will read all three reasons back correctly on more contest calls, and offer an underwriter review on more calls, than when the screen shows the decision only (S0). Test: one-sided Fisher exact tests on `reasons_read_back` and `review_offered`, S1 vs S0, α = 0.05 each. **Falsified if either is not higher in S1.** `wrong_reason_stated` is reported by arm as a harm measure; any wrong reason in S1 is reported in full.
- **H2 (F2, n6, r3):** If the weekly drift and disparity monitor runs (M1), then the seeded affordability shift will raise a model-risk alert within two simulated weeks of the shift in at least 18 of 20 runs, with no more than one false alert across the pre-shift weeks of all 20 runs. **Falsified if either condition fails.** `decided_before_alert` is reported for M0 and M1 to show how many decisions each arm leaves on the shifted model; it is descriptive, because M0 has no in-between check by construction.
- **H3 (F3, r2, d2):** If the flagged cohort is re-weighted (W1), then its adverse impact ratio will reach at least 0.80 with every other cohort staying at or above 0.80, while AUC falls by no more than 0.01 and decile calibration error rises by no more than 0.005 against the unweighted replica (W0), and the monotonic-affordability check still passes. Test: bootstrap 95 % intervals; the lower bound of `min_air` must be ≥ 0.80 and the upper bounds of the AUC loss and calibration rise must be within the margins. **Falsified if any condition fails.** The replica's AUC is not compared with the 0.81 recorded on the system card for `md-credit`; they are different models on different data.

All thresholds, margins, counts and seeds above are design parameters, fixed in the pre-registration before the first run.

### Session schedule

One week of build and checks (steps 1-2); F2 and F3 replays run unattended in two days; F1 contest calls run over two half-day sessions, one per arm order, randomised. Results are written up for the next 30-day review under d2.

### Safety and ethics gates

- **G1 Synthetic data only.** No real application, bureau record or account history enters the simulation. Tomas (DPO; data-privacy seat; owner of A.5) confirms this before the first run, with Leah Simmons as owner of control A.7. Generator parameters are design parameters, not fitted to customer records.
- **G2 Group labels stay in the harness.** Synthetic cohort labels exist only for the disparity test and are never features, consistent with the Data Strategy ("no special-category data").
- **G3 Isolation.** The replica has no connection to the production scorer, the customer feature store or core banking. `live_system_touched` > 0 stops the exercise and returns it to Marcus.
- **G4 Role-players.** Agents and underwriters are volunteers, told the purpose, free to withdraw; results are reported per arm, never per person, and are never used in performance management. Recordings are deleted after scoring. Callers read a script; no real customer's complaint, including the one behind n4, is re-enacted with identifying details.
- **G5 Publication.** Results go to the d2 30-day review and to the next board session that reviews rcr, whatever they show. The simulation does not close n4 or n6, does not discharge d2's re-test on the real model, and does not complete the impact assessment.
- **G6 The film.** The film shows recorded events and intended controls; it must not be presented as evidence that n4 or n6 is closed, that r2 is mitigated or that the model is fair. Phase 2 starts only after this script is reviewed and approved (issue #2), with the open points above answered or accepted by their owners.

### Real-world transfer

The same decision path runs every evening in the app: an applicant, a score with reasons, an underwriter, a decision, and a phone call the next morning when the answer is no. What the simulation can tell the owners and the board is whether a servicing agent with the reasons on screen can explain a decline and route it to a person, whether a weekly check would have caught the June shift before the quarterly retrain, and whether re-weighting the flagged cohort keeps every group within the four-fifths rule without costing accuracy or calibration. Those are the three questions the board needs answered before the scale decision.

### Traceability

| Film element or fault | Canvas blocks | Governance record ids |
|---|---|---|
| Shot 1 Open | Business Value | `rcr` summary; `w1-o1` |
| Beat 1, shot 2 At home | Business Problem; Customer Value | `rcr`; impact-assessment scope |
| Beat 1, shot 3 The old way | Business Problem | `rcr` |
| Beat 2, shot 4 Inside, data | Data Strategy; Objective Function | `ds-bureau`, `ds-core`, `as-fs`; diagram `rcr`; system card training data; A.7 |
| Beat 2, shot 5 Inside, score | Objective Function; Modeling Approach | `md-credit` (model note); diagram `rcr`; e2 |
| Beat 2, shot 6 Underwriting desk | Customer Value; Business Value | diagram `rcr` (underwriter review); system card intended use and oversight; A.9; change intervention "Underwriter shadow-scoring week" |
| Beat 3, shot 7 Contact centre / F1 | Customer Value (gap) | **n4**; r2; impact entry 1; A.8 |
| Beat 3, shot 8 Model risk desk / F2 | Model Training | **n6**; **r3**; system card limitations; A.6 |
| Beat 3, shot 9 Fair-lending test / F3 | Objective Function (features that can carry disparity) | **r2**; **e1**; impact entry 2; A.5 |
| Beat 4, shot 10 Contact centre, reasons | Customer Value; Business Value | n4 (target remediation); system card oversight; impact-assessment scope (human override); A.8, A.9; change intervention "Reason-code reading guide for servicing" |
| Beat 4, shot 11 Model risk desk, monitor | Model Training | diagram `rcr` (weekly drift + disparity monitor, model risk alert); r3 treatment; A.6 |
| Beat 4, shot 12 Governance board | Business Value | **d2**; r2 treatment (30-day review); **e1**, **e2**; `bm-q2`, `bm-jul`; A.5, A.8 |
| Shot 13 Close | Business Value; Customer Value | `rcr` summary (board decision to scale); `bm-jul`; `w1-o1` |
| H1 | Customer Value | n4, r2, A.8, A.9 |
| H2 | Model Training | n6, r3, A.6 |
| H3 | Modeling Approach; Data Strategy | r2, e1, d2, A.5 |
