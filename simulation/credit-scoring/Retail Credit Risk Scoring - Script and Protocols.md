# Retail Credit Risk Scoring — Script and Protocols

Governing sources: the AI Canvas for `rcr` in `CANVASES` and the initiative's governance record in `index.html` (`INITIATIVES`, `PEOPLE`, `RISKS`, `INCIDENTS`, `DECISIONS`, `EVIDENCE`, `IMPACTS`, `CONTROLS`, `MODELS`, `SYSTEM_CARDS`, `DIAGRAMS`, `DATASOURCES` / `INIT_SOURCES`, `ASSETS`, `SOURCING`, `CHANGE`, `WAVES`, `MEETINGS`, `REGS`), read as data and not changed. Plan and acceptance criteria: GitHub issue #2 (phase 1 of the Retail Credit Risk Scoring film), parent issue #1 (shared approach, beat structure, runtime target). Technical contract: `simulation/_template/README.md`. Format and conventions only: `simulation/Village Film C - Three Questions - Script and Protocols.md`. This film is **not** a scene in Village Film C and is **not** set in the robot village: it is set where the model is actually used, in a personal-loan application, at an underwriting desk, in a contact centre, at a model-risk desk and at the governance board.

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
| Customer Value | A same-session answer; a decline is confirmed by an underwriter and carries reason codes the servicing channel can actually read back. | Shots 6, 7, 10 |
| Data Strategy | Bureau feed and internal account history into the customer feature store; no special-category data. | Shot 4 |

### Governance record for `rcr`

| Record | Content (from `index.html`) |
|---|---|
| Initiative `rcr` | Retail Credit Risk Scoring. Stage Pilot, tier High, BU Retail Banking, disposition "Conditions" (amber), value "On track", sourcing build-in-house, no supplier. Summary: "A gradient-boosted scoring model that speeds up retail credit decisioning ahead of a board decision to scale." Regulations: `eu-ai-act` (requires A.5, A.6, A.8, A.9), `gdpr` (A.7), `iso-23894` (A.5, A.6). Assets: `as-emb` (consumes), `as-fs` customer feature store (contributes). |
| People by role | Owner **Maria Okafor**, Head of Credit Risk Analytics (owner of r2, e1; owner of control A.9). Sponsor **David Chen**, COO Retail Banking (change owner; competence seat). Model owner **Jonah Park**, ML Engineering Lead (owner of `md-credit`, its system card, r3, e2). **Marcus Webb**, Head of Model Risk (raised n6; owner of control A.6; AIMS-manager seat). **Tomas Berg**, Data Protection Officer (raised n4; owner of controls A.5 and A.8; impact-assessment and data-privacy seats). **Priya Nandakumar**, Chief Risk Officer (took d2; AI-risk-owner seat; owner of A.10). **Alicia Reyes**, Board Chair (chairs `bm-q2` and `bm-jul`). Underwriter and servicing agent appear in the record only as roles (system card "underwriter"; canvas "servicing channel"); they have no `PEOPLE` entry and stay unnamed here. |
| Operating model | One model, used everywhere. It scores in session; clear approvals are issued automatically; every decline or borderline score is confirmed by an underwriter, with reason codes, before the applicant is told; a contested decline returns to an underwriter (impact-assessment scope, system card, diagram, canvas Customer Value, all as below). |
| Impact assessment | Status in-progress. Scope: "Retail credit decisioning: clear approvals are issued automatically; every decline or borderline score is confirmed by an underwriter, with reason codes, before the applicant is told; a contested decline returns to an underwriter." Entries: economic harm to individuals, possible / major, "Exclusion from credit following a mis-scored application."; discrimination against groups, possible / major, "Disparate approval rates across protected attributes." |
| Risk **r2** | Disparate impact in credit approval across protected groups. Harm discrimination, possible / major, Test & Evaluate, control A.5, owner Maria, status "Mitigation in progress", treatment mitigate with 30-day review, decision d2. Why: "A model that systematically declines a protected group is both a fair-lending and an EU AI Act high-risk exposure." |
| Risk **r3** | Model drift undetected between quarterly reviews. Harm safety, likely / moderate, Operate & Monitor, control A.6, owner Jonah, status "Monitor planned", treatment mitigate with 90-day review, no decision. Why: "Retail credit behaviour shifts with rates — a stale model quietly mis-scores a widening share of applicants." |
| Incident **n4** | Model `md-credit`, classification rights-impact, reportable, Operate & Monitor, raised 2026-06-24 by Tomas, status **open**, risk r2. "Applicant contested an underwriter-confirmed decline with no explanation available." Root cause: "Reason codes not surfaced to the servicing channel." |
| Incident **n6** | Model `md-credit`, classification performance-drift, not reportable, Operate & Monitor, raised 2026-07-05 by Marcus, status **open**, risk r3. "Approval rate drifted four points after the June rate change." Root cause: "Affordability features shifted faster than the quarterly retrain." |
| Decision **d2** | Risk treatment on r2, by Priya, 2026-06-12, at `bm-q2`: "Mitigate: re-weight the flagged cohort and re-test before the scale decision; review every 30 days." |
| Board sessions | `bm-q1` Q1 management review (2026-04-03, held) reviewed rcr, no gate items. `bm-q2` Q2 governance board (2026-06-12, held, chair Alicia, seven of the eight seats present, held by six people: Tomas holds both the impact-assessment and the data-privacy seat) minuted "Credit scoring mitigation agreed." `bm-jul` Q3 governance board (2026-07-24, status scheduled, chair Alicia) lists rcr and hiring for review. (`bm-jul-x`, the out-of-cycle session of 2026-07-14, reviewed only the service copilot; it is not staged here.) |
| Evidence **e1** | Bias audit "Fair-lending disparity test, Q2", owner Maria, control A.5, captured 2026-06-05, due 2026-09-05: "Four-fifths rule tested across five protected attributes; two cohorts within tolerance, one flagged for re-test." Filed a week before d2, so the order test → decision holds in the record. |
| Evidence **e2** | Model card "Credit scoring model card v3", owner Jonah, control A.8, captured 2026-06-02, no due date: "Intended use, out-of-scope use, training window, calibration method and known limitations." |
| Controls | A.5 impact assessment (in-progress, Tomas); A.6 AI life cycle (in-progress, Marcus); A.7 data for AI systems (in-progress, Leah Simmons); A.8 information for interested parties (**not-started**, Tomas); A.9 use of AI systems and human oversight (in-progress, Maria); A.10 third-party relationships (in-progress, Priya). |
| Model `md-credit` | Retail credit GBM 3.2, Classification, in-use, in-house, conforms to the reference stack, asset `as-fs`. Note: "Gradient-boosted trees with a monotonic affordability constraint and a calibration layer." (`md-embed`, the shared document embedding model, also lists rcr; no canvas block or diagram node uses it, so the film does not stage it.) |
| System card `md-credit` | Reviewed 2026-06-02. Intended use: "Score retail credit applications in session: clear approvals are issued automatically, and every decline or borderline score goes to an underwriter, who decides." Out of scope: commercial lending, collections prioritisation, any use on an existing customer's held facility. Training data: "36 months of internal account history plus bureau features; no special-category attributes." Evaluation: "AUC 0.81 on a held-out quarter; calibration checked per decile; four-fifths disparity test per protected attribute." Limitations: "Thin-file applicants are under-represented; performance degrades when rates move sharply." Oversight: "An underwriter confirms every decline and borderline score, with reason codes, before the applicant is told; a contested decline returns to an underwriter." |
| Diagram `rcr` (10 nodes) | Application intake → customer feature store ← bureau feed; feature store → credit GBM scorer → (score + reasons) → calibration + reason codes; calibration → (clear approval) → automatic approval → core banking decision; calibration → (decline or borderline) → underwriter review → (confirmed + reason codes) → core banking decision; scorer ⇢ (weekly) drift + disparity monitor → model risk alert. |
| Data sources | `ds-core` Core banking accounts (category Financial transactions: high sensitivity, personal data) and `ds-bureau` Credit bureau feed (category Third-party / purchased data: high sensitivity, personal data; system "Bureau API"), both feeding `as-fs`. The bureau provider is not named in the record and has no `SUPPLIERS` entry; the film does not name one. |
| Sourcing | build-in-house: "The scoring logic is the lending policy — it has to be inspectable and defensible in an appeal, so it is not bought." |
| Change | Owner David, ambition Reshape, ADKAR awareness 85, desire 60, knowledge 55, ability 30, reinforcement 10. Interventions: "Underwriter shadow-scoring week", "Reason-code reading guide for servicing", "Floor-walker support for the first two weeks". |
| Wave objective | `w1-o1` (wave 1 "Prove it"): "Cut retail credit decision time to under an hour", measured as median time to decision. |

---

## Usage situation

The film follows one fictional applicant through one real use of the model, then steps behind the counter to the people who watch it.

| Element | In the film | Traces to |
|---|---|---|
| Who applies | **Nadia** (fictional), 31, a home-care nurse who has banked with the bank for four years, so it holds her account history. Her old car has broken down and she needs a small personal loan to replace it (staged: €6,000 over 36 months; a design parameter). Nothing on screen or in this document gives Nadia a protected characteristic, and the flagged cohort in shot 9 is never linked to her. | Business Problem ("applicant"); Data Strategy (internal account history) |
| Where and when | At her kitchen table, on her phone, in the bank's app, on a weekday evening after work, at about half past six, with the street lamps already on (staged). The bank's underwriters are still on shift at that hour (staged: the underwriting team covers referrals until 20:00), which is what lets a referred application be answered in the same session. | Customer Value ("a same-session answer"); `w1-o1` (median time to decision under an hour) |
| Trigger | She submits the loan application in the app. Application intake runs a credit search with the bureau and pulls her account history; both land in the customer feature store. | Diagram `rcr` (application intake, bureau feed, feature store); Data Strategy |
| What the AI outputs | A calibrated probability that she defaults within the 90-day definition, and the reason codes behind it (staged as three codes, one per feature family: affordability, bureau history, account behaviour). | Objective Function; Modeling Approach; diagram node "Calibration + reason codes" |
| Who acts on it | Her score is not a clear approval, so it does not go out automatically: it drops into the underwriters' referral queue. An **underwriter** reviews the application, the bureau summary, the score and its three reason codes, and decides; here she confirms the decline, with reason codes, before Nadia is told. Within the hour Nadia's app shows the answer: declined, which credit bureau was searched, and a number to call. Next morning she calls the contact centre to ask why. A **servicing agent** should be able to read the reasons back and, if she contests the decline, send it back to an underwriter. | System card intended use and oversight; impact-assessment scope; diagram (decline or borderline → underwriter review → confirmed + reason codes → core banking decision); Customer Value; n4 |
| How the faults are noticed | The agent cannot see the reasons, so the call is logged as a complaint; complaints that touch a data-subject right reach the DPO, who raised n4 (staged route; the record gives the raiser and the date, not the route). At the **model-risk desk**, the June rate change has moved approvals by four points; no automated alert exists yet (r3 "Monitor planned"), and the shift is found by a person reading the month-end figures, which fits n6 being raised by the Head of Model Risk on 5 July (staged route). The Q2 **fair-lending test**, filed on 5 June, flagged one cohort for re-test (e1). | n4 (raised by Tomas, 2026-06-24); n6 (raised by Marcus, 2026-07-05); r3; e1 (captured 2026-06-05) |
| Behind the scenes | The quarterly retrain will not catch a rate-driven shift in time (r3); the planned weekly drift and disparity monitor is the control. The **governance board** decided at its Q2 session to re-weight the flagged cohort and re-test before it decides whether to scale (d2), with the risk reviewed every 30 days; rcr is on the agenda of the next board session (`bm-jul`). | n6, r3, diagram monitor node, Model Training; e1, r2, d2, `bm-q2`, `bm-jul` |

Nadia's case stages the kind of event that n4 records; it is not the recorded case itself, and the film shows no dates. What the film deliberately leaves open: whether Nadia's own decline was right. The impact assessment's first harm is "exclusion from credit following a mis-scored application"; the film shows that she can get her reasons and have a person look again, not what the person decides.

## Canvas assumptions

None. All seven canvas blocks for `rcr` are filled in `index.html`, so no block had to be drafted. The film does need a few **staging assumptions**, which are choices about how to show the record, not additions to it. Each is labelled for review:

| id | Staging assumption | Why it is needed | Record it rests on |
|---|---|---|---|
| SA1 | Nadia, her job, the car, the loan size (€6,000 over 36 months), the hour she applies and the underwriting team's evening cover are fictional. | A usage film needs one concrete applicant, and a same-session answer for a referred application needs an underwriter on shift. | Issue #1 ("fictional applicants/customers are fine"); Customer Value |
| SA2 | Three reason codes per decision, one for each feature family. | The record says "reason codes" but gives no count. | Objective Function; system card oversight |
| SA3 | The app shows the decision, which credit bureau was searched and a number to call, but not the reason codes; the reasons reach Nadia when the servicing channel reads them back. | The record does not say what the app displays. Consumer-credit rules require a lender that refuses credit on the basis of a database search to tell the applicant which database it consulted, so the bureau is shown; the explanation itself is given on request. | Customer Value; n4 root cause |
| SA4 | Nadia's score falls on the decline side, so it is referred to an underwriter, who confirms the decline. The film does not say whether the score was a decline or a borderline one. | The record routes both to the same underwriter review. | System card intended use and oversight; impact-assessment scope; diagram `rcr` |
| SA5 | The n6 drift is drawn as a fall in the approval rate. | A line has to move one way; the record gives the size (four points), not the direction. | n6 |
| SA6 | The fairness test is drawn as three cohort bars, two within tolerance and one flagged. | e1 reports "two cohorts within tolerance, one flagged" from a test across five protected attributes; the per-attribute breakdown is not in the record. | e1 |
| SA7 | The weekly drift and disparity monitor is pictured working in Beat 4, as an illustration of the intended control; its headline calls it planned. | It is the control the record intends; r3's status is "Monitor planned". The picture shows what it is for, the words say it is not yet in place, and so does Part 2. | Diagram `rcr`; r3 |
| SA8 | Reason codes on the servicing screen (shot 10) are shown as the required state ("must show"). | n4 is open; the canvas Customer Value and the change intervention "Reason-code reading guide for servicing" describe the target. | n4; Customer Value; `CHANGE.rcr` |
| SA9 | The re-test under d2 is shown as pending (an outlined, dashed bar and an hourglass), never as passed. | d2 is a decision to act; no re-test result is on file. | d2; r2 status "Mitigation in progress" |
| SA10 | The n6 shift is found by a person reading the month-end figures, not by an alert; the contested call is logged as a complaint, which is how n4 reaches the DPO. | The record names who raised each incident and when, not how it was noticed. No automated drift alert exists (r3), and n6 was raised five days after the end of June. | n4 (Tomas, 2026-06-24); n6 (Marcus, 2026-07-05); r3 |
| SA11 | A challenger is promoted only after the model-risk function signs it off. | Model Training says only "challenger runs shadow before promotion"; independent review before a model change is standard model-risk practice. | Model Training; control A.6 (owner Marcus Webb, Head of Model Risk) |

## Open points for review

Resolved this round, now consistent in the record: **(a)** automated or reviewed: the system card, impact-assessment scope, diagram, canvas and n4 all describe the same operating model (automatic clear approvals; every decline or borderline score confirmed by an underwriter; a contested decline returns to an underwriter); **(b)** the "above the threshold" wording is gone from the system card; **(c)** e1 is now dated 2026-06-05, before d2 (2026-06-12).

These points should be confirmed by the owners before phase 2, because the film draws them:

1. **e1's scope and its data.** Five protected attributes tested, three cohorts described; the film shows only the three cohorts (SA6). Which attributes, and on what lawful basis? Age and sex are personal data but not special-category data; if any attribute is (for example ethnic origin), using it to detect bias needs a basis such as EU AI Act Art. 10(5) with its safeguards, and the Data Strategy line "no special-category data" should say it means model inputs. Owner: Maria, with Tomas.
2. **Is the impact assessment the FRIA?** Creditworthiness scoring of natural persons is a high-risk use (EU AI Act Annex III 5(b)), and Art. 27 requires a deployer of such a system to carry out a fundamental-rights impact assessment before first use. The `rcr` assessment is in progress while the model is in use in the pilot. The owners should say whether it is meant to be the FRIA and whether its sign-off is a condition of the scale decision. Owner: Tomas (A.5), with Maria.
3. **Is the underwriter review meaningful?** An underwriter who confirms almost every referred decline is a rubber stamp, and then the score is in effect the decision, with the full GDPR Art. 22 safeguards (human intervention, a chance to contest, an explanation) applying to it. The record holds no measure of how often underwriters depart from the score. Owner: Maria (A.9), with Tomas.
4. **Who handles a contested decline, and how fast?** The record says it "returns to an underwriter". Whether that must be a different underwriter from the one who confirmed it, and the response time, are not set. The film shows the ticket reaching the underwriting team, not a named person. Owner: Maria.
5. **A.8 is not started**, although e2 (model card) is filed against it and n4 is a transparency failure: an applicant asking why a high-risk system's output led to a decline is the request that the EU AI Act's right to an explanation (Art. 86) and the GDPR's information and access rights are there to answer. The content of the in-app decline notice (SA3) belongs here too. Owner: Tomas.
6. **r3 has no decision**, and its monitor is "planned". The film shows the monitor as the intended control (SA7). Owner: Jonah, with Marcus (A.6).
7. **The bureau feed has no supplier record**, although it is third-party purchased data (A.10). The film does not name a bureau. Owner: Priya.
8. **`md-embed` lists rcr** but no canvas block or diagram node uses it. Not staged. Owner: Leah.
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
| Amber `#e9a23b` | Sent to a person, or flagged for a closer look: underwriter referral, a complaint, a model-risk alert, the flagged cohort |
| Red ring `#d84a3a` | A fault from the record: a red ring pulses on the floor, desk or screen where it happens (shots 7, 8, 9 only) |
| Translucent white, dashed outline | Shadow: the challenger model, whose outputs never reach a customer |

**Glyph vocabulary** (in-world, no words): decision tick in a circle (approved, green); circle with a bar (declined, slate); three **reason chips**, each a rounded tile with an icon and a bar whose length shows its weight: a wallet (affordability), a clock over a document (bureau history; the same glyph marks the bureau searched on Nadia's decline notice), a card with a wave (account behaviour); a form with rows (the application summary); a handset (call us); an amber card with a folded corner (a complaint); a sheet with bars (the month-end figures); a stack of small trees (the gradient-boosted model); a ring lens (calibration); a semicircular dial with a needle (the probability); a one-way slider with an arrow (the monotonic affordability constraint); a line chart inside a band (approval rate and its tolerance); bars with a dashed line at four-fifths (the fairness test); an hourglass (pending); an empty sign-off box (approval still to come); a calendar ring of 30 pips (review cadence); a closed barrier gate with an amber lamp (the scale-up gate).

**Overlay.** The overlay follows the template contract (`simulation/_template/README.md` §1.5 and §1.7) without change. These elements are allowed, and no others:

| Element | Content in this film |
|---|---|
| Setting, top left | The setting name from the shot table, on a small scrim pill with a dot in the beat's accent. |
| Initiative label, top right | `Retail Credit Risk Scoring`, the same on every scene, the open and close cards included. |
| Beat numeral | The large beat number `1`-`4` in the beat's accent, at the start of the beat row. It numbers the four beats, never a shot. Hidden on the cards. |
| Source line | A small line beside the numeral naming the record the shot traces to (table below). At most 10 words, no record ids, no digits. Hidden on the cards. |
| Beat indicator | `The situation → The AI at work → What can go wrong → How it is kept safe` on the beat row, current beat lit in a pale tint of its accent; at phone width the current beat in words and the others as dots. Hidden on the cards. |
| Caption, `[data-caption]` | One headline, at most one support line, and a thin rule on the left in the beat's accent. No infographic, footer, note or step chips are used. |
| Navigation rail | One numbered dot per beat (`1`-`4`, the same numbers as the beat numeral) plus a list button; the list shows Introduction, the four beats with their shots by setting name, and Close. |
| Playback bar and `Paused` pill | Previous scene, play/pause, next scene, scrubber (one segment per beat in its accent, a neutral segment per card, a tick at every shot), keyboard hint `Space` pause/play and `← →` scenes, the time, restart set apart; the `Paused` pill when paused. |

**Source lines** (exact; every one traces to a record in this document):

| shot | source line (exact) | record it names |
|---|---|---|
| 2 | `AI Canvas: Business Problem` | Canvas Business Problem |
| 3 | `AI Canvas: Business Problem` | Canvas Business Problem |
| 4 | `AI Canvas: Data Strategy, Objective Function` | Canvas Data Strategy and Objective Function |
| 5 | `AI Canvas: Objective Function, Modeling Approach` | Canvas Objective Function and Modeling Approach |
| 6 | `AI Canvas: Customer Value; system card oversight` | Canvas Customer Value; system card `md-credit` intended use and oversight |
| 7 | `Incident log: a decline with no reasons` | Incident n4 |
| 8 | `Incident log and risk register: model drift` | Incident n6; risk r3 |
| 9 | `Risk register and fair-lending test` | Risk r2; evidence e1 |
| 10 | `AI Canvas: Customer Value; system card oversight` | Canvas Customer Value; system card `md-credit` oversight; impact-assessment scope |
| 11 | `Planned control; AI Canvas: Model Training` | r3 ("Monitor planned"); diagram monitor node; canvas Model Training |
| 12 | `Board decision, with evidence on file` | Decision d2 at `bm-q2`; evidence e1 |

On the last scene the caption holds while the picture fades to black, so caption and picture leave together.

**Fallback:** if WebGL cannot start, the page shows the open headline (`A loan can be decided in minutes, with checks around it.`), the note `This film needs 3D graphics (WebGL). Your browser could not start it. Here is the film in words.`, and then every scene by beat and setting name (for example `What can go wrong — The contact centre`, with the beat numeral as the template sets it) with its headline and support line exactly as below; no shot numbers and no times.

### Numbering convention

The film has one initiative, told in four **beats** and thirteen **shots** (eleven in the beats, plus the open and close cards). Shots are named by their setting; the shot numbers in this document are for reference and never appear on screen. The only digits in labels are the beat numerals `1`-`4` on the beat row and on the navigation dots, which the template uses to number the four beats. Otherwise numbers appear on screen only inside sentences, and only where they come from the record: "90 days" (Objective Function), "four points" (n6), "four-fifths" (e1), "30 days" (d2), and "three main reasons" (SA2). The time readout `0:00 / 0:59` is a clock, not a label.

Accent colours (the overlay rule, the beat numeral and the beat's scrubber segment): open and close neutral `#e8e6e1`; The situation and The AI at work, credit blue `#4a7fd4`; What can go wrong, red `#d84a3a`; How it is kept safe, green `#3fa34d`.

### Sets

| Set | Shots | Can be shared with |
|---|---|---|
| K1 Nadia's kitchen after dark: table, phone, a car key on the table, a window with a street lamp and the broken-down car under it | 2, 13 | — |
| K2 The old review desk: paper files in stacks, an in-tray, a wall clock, two desaturated clerk figures | 3 | Fraud Triage Model (#5) analyst desk |
| K3 Inside the scoring system: an abstract dark space with the feature store (a lit cabinet of drawers), the tree stack, the calibration ring, the dial | 4, 5 | — |
| K4 The underwriting desk: one desk, two monitors, an underwriter figure, an amber referral tray. It stands at the back of the K5 floor, so shot 10 can pan from the agent to the tray without a cut (shot 6 lights it for evening, shot 10 for morning) | 6, 10 | Fraud Triage Model (#5) review desk |
| K5 The contact centre: a pod of four desks, headsets, the servicing agent's monitor, a complaints tray at the end of the pod | 7, 10 | Customer Service Copilot (#3) |
| K6 The model-risk desk: two figures (a third, from credit-risk analytics, stands at the fairness panel in shot 9), a wall dashboard (approval-rate chart, fairness bars, a quarterly calendar strip), a desk lamp that can turn amber | 8, 9, 11 | Fraud Triage Model (#5); Demand Forecasting (#6) planning room |
| K7 The board room: a table with six people seated (seven seats present, one person holding two), board papers, a wall screen | 12 | All five initiative films |

### Shots

| # | start s | dur s | beat | setting (top-left, exact) | camera | world action (what is visibly on screen) | headline (exact) | support line (exact) | accent | traces to |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 4 | Open | `A loan in minutes` | Slow crane down from 2.6 m to 1.7 m outside Nadia's kitchen window after dark; the camera stays outside (≥ 0.6 m from the wall and frame) and ends framed by the open window, her lit phone upper right | A street lamp, the broken-down car at the kerb with its hazard lights blinking; inside, Nadia sits at the kitchen table, the phone lighting her hands | A loan can be decided in minutes, with checks around it. | We follow one loan from a phone to the board room. | neutral | Business Value; initiative summary |
| 2 | 4 | 4 | The situation | `At home, in the banking app` | Over-the-shoulder at 1.3 m, 1.0 m behind and right of Nadia, slow push-in to the phone; the phone is aimed into the upper right (offset +0.25 / +0.2), the table lower left | The app screen shows glyphs only: a car icon, a coin stack and a slider set to the loan size, a term ring; she drags the slider, taps the submit glyph; a spinner ring starts | Nadia needs a small loan to replace her broken-down car. | She applies in her banking app one evening after work. | credit blue | Business Problem (the applicant at the point of decision); usage situation; SA1 |
| 3 | 8 | 4 | The situation | `The old way: by hand` | Contrast vignette, desaturated: slow lateral dolly at 1.5 m along the old review desk, 1.8 m back | Paper files pile up in the in-tray; the wall clock's hands spin through several days; two clerks lift the same file and give it opposite marks (one slate bar, one green tick); in a small inset window frame on the desk edge, a phone like Nadia's goes dark and is put face down (the applicant gives up) | Checking loans by hand takes days. | Some applicants give up, and two staff can judge one file in two ways. | credit blue | Business Problem ("slow and inconsistent … applicant drop-off") |
| 4 | 12 | 4 | The AI at work | `Inside the scoring system` | Abstract set; the camera follows the data from 4 m back at 2.2 m height, a smooth arc toward the feature store, aimed upper right (offset +0.2 / +0.15) | Two streams of ice-blue packets arrive: one from a bureau glyph (a document with a clock), one from a bank-vault glyph (her four years of account history); they drop into drawers of the lit feature-store cabinet. Off to one side, a single grey token marked with a crossed-out circle stands apart with no path to the cabinet: no special-category data is part of the feed | The model reads her credit file and how she uses her account. | It is never given data on health, religion or race. | credit blue | Data Strategy; Objective Function (bureau history, account behaviour); `ds-bureau`, `ds-core`; diagram (intake, bureau feed, feature store); system card training data |
| 5 | 16 | 5 | The AI at work | `Inside the scoring system` | Continues from the cabinet: slow orbit of 30° around the tree stack at 1.8 m, 3.5 m out | Features leave the cabinet as packets and pass through a stack of small trees (the gradient-boosted model), each tree briefly lighting; one packet carries the wallet glyph and rides a one-way slider: as the wallet shrinks, the arrow moves the dial needle only toward higher risk (1.5-3.0 s). The stack's output passes through the calibration ring lens, and the needle settles on the probability dial (3.5-4.5 s) | It estimates how likely she is to fall 90 days behind on her loan. | If she can afford less, her risk score can never go down. | credit blue | Objective Function (probability of 90-day default); Modeling Approach (gradient-boosted trees, monotonic affordability constraint, calibration layer); `md-credit` |
| 6 | 21 | 5 | The AI at work | `The underwriting desk` | Over-the-shoulder at 1.4 m, 1.1 m behind the underwriter, then a 1.2 s cut-in-style push (no cut) to frame the monitor upper right and Nadia's phone in a small picture-in-picture glyph frame lower right of the monitor | Evening light. A green tick glyph slides past the desk into a chute without stopping (a clear approval for someone else, issued automatically, 0-1.0 s); an amber referral card drops into the underwriter's tray (1.0 s). The monitor shows the application summary (a form with rows), the dial and three reason chips (wallet, clock-over-document, card-with-wave) with bars of different lengths, and two live controls, a green approve tick and a slate decline bar; the underwriter studies the screen and taps the decline bar (2.5 s); in the picture-in-picture frame Nadia's spinner resolves into the slate declined glyph with the small bureau glyph and the handset glyph beside it (3.5 s) | A clear yes goes out at once; anything else goes to an underwriter. | The underwriter checks the three main reasons, and her app says no. | credit blue | System card intended use ("clear approvals are issued automatically, and every decline or borderline score goes to an underwriter, who decides") and oversight; impact-assessment scope; diagram (calibration → clear approval → automatic approval; decline or borderline → underwriter review → confirmed + reason codes → core banking decision); Customer Value; SA1, SA2, SA3, SA4 |
| 7 | 26 | 5 | What can go wrong | `The contact centre` | Morning light; wide establishing at 1.6 m on the pod from 2.4 m, then a slow push that stops 1.0 m behind the agent, monitor aimed upper right (offset +0.25 / +0.2) | Nadia, at home with her coat on, holds her phone to her ear (small inset frame, upper left); a ringing pulse reaches the agent's headset; the agent's monitor shows Nadia's decision record with the slate declined glyph, and beside it three **empty** reason-chip slots, dashed; a red ring pulses around the empty slots (2.0 s); the agent turns to the keyboard and an amber complaint card drops into the complaints tray at the end of the pod (3.5-4.5 s) | Next morning Nadia calls to ask why, but the agent sees no reasons. | The reasons stayed in the scoring system and never reached the agent's screen. | red | **Fault F1** = the kind of event recorded as incident **n4** (rights-impact, reportable, open; "Applicant contested an underwriter-confirmed decline with no explanation available"; root cause "reason codes not surfaced to the servicing channel"); risk r2; impact-assessment entry 1; Customer Value (the gap); SA10 |
| 8 | 31 | 4 | What can go wrong | `The model risk desk` | Static three-quarter view at 1.5 m, 2.2 m from the wall dashboard, a slow 3 % push; dashboard upper right | A calendar strip on the wall shows a rate-change marker (a percent glyph with a step mark; the record gives no direction for the change) in June; on the approval-rate chart the line steps out of its band by a visible gap (four grid steps, one per point; SA5) just after the marker (1.0-2.0 s), and a red ring pulses on the gap; the desk lamp stays dark (no alert fires); a model-risk figure lays a month-end figures sheet beside the chart and points to the gap (2.5-3.5 s); the next quarterly-retrain marker sits far to the right of the strip | After the June rate change, approvals drift by four points. | No alert fires; model risk finds it later in the monthly figures. | red | **Fault F2** = incident **n6** (performance-drift, open; raised by the Head of Model Risk; root cause "affordability features shifted faster than the quarterly retrain"); risk **r3** ("Monitor planned"); Model Training (quarterly retrain); system card limitation ("degrades when rates move sharply"); SA5, SA10 |
| 9 | 35 | 5 | What can go wrong | `The fair-lending test` | Turns from the chart to the dashboard's second panel: slow pan at 1.5 m, 2.0 m out, panel upper right | A third figure (the credit-risk analytics team that owns the test) stands at the panel. Three cohort bars rise one after another (0.5 / 1.2 / 1.9 s) against a dashed line at four-fifths of the highest bar; two end above the line in green; the third stops below it and turns amber, a red ring pulsing at its foot (2.6 s); a small flag glyph pins to it | A fairness test flags one group of applicants for a closer look. | Its approval rate is below four-fifths of the top group's rate. | red | **Fault F3** = risk **r2**; evidence **e1** (four-fifths rule; one cohort flagged for re-test); impact-assessment entry 2; SA6 |
| 10 | 40 | 5 | How it is kept safe | `The contact centre` | Same pod as shot 7 and the same push, so the change is the only difference; then a 1.5 s pan to the underwriting desk in the background, aimed upper right | The agent's monitor now shows the three reason chips filled in their slots, beside a small reading-guide glyph (an open booklet); the agent points to each chip in turn as a speech glyph with the matching icon rises from the headset (0.8-2.6 s); the agent taps the amber review glyph and an amber ticket travels across the room into the underwriting team's referral tray (3.0-4.5 s); the film does not show who picks it up | The agent's screen must show the reasons, so they can be read back. | Nadia can ask an underwriter to look at her case again. | green | n4 remediation target (SA8); Customer Value; Business Value ("what makes it contestable"); system card oversight and impact-assessment scope ("a contested decline returns to an underwriter"); controls A.8, A.9; change intervention "Reason-code reading guide for servicing" |
| 11 | 45 | 5 | How it is kept safe | `The model risk desk` | Same view as shot 8, then a slow dolly left at 1.5 m to bring the second monitor into frame upper right | A weekly tick mark sweeps along the approval-rate chart; at the first tick after the rate-change marker the desk lamp turns **amber** and an amber alert glyph lands on the desk (1.0 s) (SA7); on the second monitor, the tree stack runs beside a **translucent dashed copy** (the challenger) on the same packets, and the copy's outputs fall into a dashed tray that leads nowhere, next to an empty sign-off box (2.0-3.5 s; SA11); along the bottom, a bar of 36 small segments (the rolling 36-month training window) slides three segments to the right, one quarter, at the retrain marker (4.0 s) | A weekly check is planned to catch drift and unfair results between retrains. | A new model runs in the shadow, then needs model risk sign-off. | green | Diagram (weekly drift + disparity monitor → model risk alert); r3 treatment (mitigate, monitor planned); control A.6; Model Training (quarterly retrain, rolling 36-month window, challenger in shadow before promotion); SA7, SA11 |
| 12 | 50 | 5 | How it is kept safe | `The governance board` | Crane down from 2.4 m to 1.6 m over the end of the board table, 2.2 m from the nearest seated figure; wall screen upper right | Six figures at the table: the seven seats present at `bm-q2`, where d2 was taken, are held by six people, because the DPO holds both the impact-assessment and the data-privacy seat (chair, AIMS manager, AI risk owner, DPO, internal audit, competence owner); two papers lie on the table, one with bars (the fairness test) and one with a card outline (the model card); on the wall screen, the flagged amber bar from shot 9 is redrawn as an **outlined, dashed** bar with an **hourglass** above it (pending re-test, SA9); a calendar ring of 30 pips fills once (1.0-3.5 s); beside it a barrier gate stays closed under an amber lamp | The bank re-weights that group's training data and tests again before scaling. | Progress is checked every 30 days, with the fairness test on file. | green | Decision **d2** (by Priya at `bm-q2`: re-weight the flagged cohort, re-test before the scale decision, review every 30 days); r2 treatment; evidence **e1**, **e2**; controls A.5, A.8; `bm-jul` (next scheduled review of rcr) |
| 13 | 55 | 4 | Close | `What comes next` | Returns to Nadia's kitchen, now in morning light: camera at 1.1 m height, slow pull-back from 1.2 m to 2.4 m from the phone, ≥ 0.9 m from Nadia | Nadia puts her phone down after the call; it still shows the slate declined glyph, the bureau glyph and the handset glyph (the app shows no reasons, SA3). Above the phone a small amber ticket glyph with an hourglass hovers, a film device rather than an app screen, for the underwriter review the agent opened in shot 10; the outcome is never shown. The last 0.7 s fades to black with the caption, then the film loops | Answers should come fast, with reasons people can read and challenge. | Next gate: the board decides whether the pilot can scale. | neutral | Business Value; Customer Value; initiative summary ("ahead of a board decision to scale"); `bm-jul`; wave objective `w1-o1` |

### Word count and readability (on-screen text set by this script)

Counted as in the Village Film: by whitespace-separated tokens that contain a letter or a digit. Every line here is the team's own wording, so every limit is enforced: headline ≤ 14 words, support line ≤ 14 words, Flesch-Kincaid grade ≤ 8 (0.39 × words ÷ sentences + 11.8 × syllables ÷ words − 15.59, vowel-group syllable count, sentences counted at `.`, `!` or `?`). A new limit, needed because shots are short: **reading pace ≤ 5.5 words per second** of shot time (headline plus support line), which is the Village Film's own average (473 words in 86 s). The lines below are stored as `test/credit-scoring-lines.json` (written by `python test/credit-scoring_test.py --write-lines`) and checked with the same readability tool before any build ships.

| shot | headline words | support words | words / s | FK headline | FK support |
|---|---|---|---|---|---|
| 1 Open | 11 | 11 | 5.5 | 5.9 | 3.7 |
| 2 At home | 10 | 10 | 5.0 | 6.0 | 7.2 |
| 3 The old way | 6 | 14 | 5.0 | 2.5 | 7.6 |
| 4 Inside, data | 12 | 10 | 5.5 | 5.8 | 7.2 |
| 5 Inside, score | 14 | 12 | 5.2 | 6.7 | 3.8 |
| 6 Underwriting desk | 13 | 12 | 5.0 | 7.6 | 4.8 |
| 7 Contact centre, fault | 13 | 13 | 5.2 | 4.9 | 6.7 |
| 8 Model risk, drift | 10 | 12 | 5.5 | 7.2 | 7.8 |
| 9 Fair-lending test | 12 | 11 | 4.6 | 5.8 | 6.9 |
| 10 Contact centre, reasons | 13 | 11 | 4.8 | 3.1 | 6.9 |
| 11 Model risk, monitor | 13 | 12 | 5.0 | 6.7 | 4.8 |
| 12 Governance board | 12 | 12 | 4.8 | 7.8 | 6.8 |
| 13 Close | 11 | 10 | 5.2 | 6.9 | 7.2 |
| **Total** | **150** | **150** | **300 words in 59 s (5.1 / s)** | max **7.8** | max **7.8** |

Fixed overlay furniture is not part of the count: the setting names top-left, the initiative label top-right, the beat numerals, the source lines (each ≤ 10 words, listed above), the beat indicator (`The situation → The AI at work → What can go wrong → How it is kept safe`, 15 words), the `Paused` pill, the labels and tooltips of the playback controls and the scene navigation, and the fallback note. No footnotes and no record ids (n4, r2, d2 …) appear on screen; they live in this document.

### Plain-language conventions

1. **Full sentences, never fragments.** Every line has its own subject and verb, in everyday words. The one colon line ("Next gate: …") is a full sentence after the colon; the semicolon lines (shots 6 and 8) join two full sentences.
2. **People first.** Beat 1 names the person with the stake (Nadia); Beat 3 says what went wrong for a person or a group before what went wrong in the model; Beat 4 says who can now do what (the agent can read the reasons back; Nadia can have an underwriter look again; model risk signs off a new model; the board decides).
3. **Faithful tense.** Things that happened are in the record (n4, n6, e1, d2) and are staged as events. Controls that are intended but not yet in place are worded as such: the reasons on the servicing screen as the required state ("must show"), the weekly monitor as planned ("is planned to catch"), the re-test as still to come ("before scaling"), and the close as an aim ("should come fast"). Part 2 states their status. No line says an incident is fixed, a test passed or the model is fair.
4. **Jargon is replaced, not explained on screen.** The film words on the left stand for the record terms on the right:

| on screen | record term |
|---|---|
| "decided in minutes", "answers should come fast" | Business Value "cuts decision latency from days to minutes"; `w1-o1` median time to decision under an hour |
| "checking loans by hand takes days", "some applicants give up", "two staff can judge one file in two ways" | Business Problem: manual review "slow and inconsistent, driving delay and applicant drop-off" |
| "her credit file" | bureau history, `ds-bureau` Credit bureau feed |
| "how she uses her account" | account-behaviour features from internal account history, `ds-core` |
| "it is never given data on health, religion or race" | Data Strategy "no special-category data"; system card "no special-category attributes" (health, religion and racial or ethnic origin are examples of special-category data). The line is about the model's inputs; it does not claim that other features cannot stand in for these, which is what the fairness test in shot 9 checks |
| "how likely she is to fall 90 days behind on her loan" | Objective Function "probability of 90-day default" (the exact default definition and horizon are in model card e2) |
| "if she can afford less, her risk score can never go down" | Modeling Approach "monotonic constraint on affordability" (monotonic: the score never moves the other way; the direction, worse affordability never lowering risk, is the usual one and is staged, not stated in the record) |
| "a clear yes goes out at once; anything else goes to an underwriter" | System card intended use "clear approvals are issued automatically, and every decline or borderline score goes to an underwriter, who decides"; diagram nodes "Automatic approval" and "Underwriter review" |
| "the underwriter checks the three main reasons, and her app says no" | System card oversight "an underwriter confirms every decline and borderline score, with reason codes, before the applicant is told"; Customer Value "a same-session answer; a decline is confirmed by an underwriter"; reason-code count staged (SA2); how the app shows it staged (SA3) |
| "the agent sees no reasons", "never reached the agent's screen" | n4 "no explanation available"; root cause "reason codes not surfaced to the servicing channel" |
| "after the June rate change, approvals drift by four points" | n6 "approval rate drifted four points after the June rate change" |
| "no alert fires; model risk finds it later in the monthly figures" | r3 "Model drift undetected between quarterly reviews", status "Monitor planned" (no alert exists yet); n6 raised by Marcus Webb, Head of Model Risk, on 2026-07-05; the month-end figures are staged (SA10) |
| "a fairness test flags one group" | e1 "fair-lending disparity test … one flagged for re-test"; r2 |
| "below four-fifths of the top group's rate" | the four-fifths rule (adverse impact ratio < 0.80), which the bank uses as its screening trigger (e1; system card evaluation). It is a flag for a closer look, not a legal finding: falling below it does not by itself show unlawful discrimination, and staying above it does not prove fairness |
| "the agent's screen must show the reasons, so they can be read back" | Customer Value "reason codes the servicing channel can actually read back"; n4 remediation target |
| "ask an underwriter to look at her case again" | impact-assessment scope and system card oversight "a contested decline returns to an underwriter" |
| "a weekly check is planned to catch drift and unfair results" | diagram "Drift + disparity monitor" (weekly) → "Model risk alert"; r3 status "Monitor planned" |
| "a new model runs in the shadow, then needs model risk sign-off" | Model Training "challenger runs shadow before promotion"; sign-off by the model-risk function staged (SA11), control A.6 owned by the Head of Model Risk |
| "re-weights that group's training data and tests again before scaling" | d2 "re-weight the flagged cohort and re-test before the scale decision" (re-weighting changes how much the cohort's examples count in training; it does not add anything to an individual's score) |
| "progress is checked every 30 days" | d2 "review every 30 days"; r2 treatment `reviewCadenceDays: 30`, owner Maria (the record does not say the board itself meets every 30 days) |
| "the fairness test on file" | evidence e1 (the model card e2 is shown as a paper on the table, not named on screen) |
| "next gate: the board decides whether the pilot can scale" | initiative summary "ahead of a board decision to scale"; stage Pilot; `bm-jul` |
| "reasons people can read and challenge" (worded as an aim, "should", because n4 is open) | Business Value "standardises the basis of a decline, which is also what makes it contestable" |

5. **What never changes in a rewrite:** the order of the four beats, the three faults and their record ids, the rule that a decline is slate and never red, the rule that the re-test is shown pending, and the rule that no result is stated anywhere on screen.

---

## Part 2 — Protocol

The film shows the decision path once, with three recorded faults. This protocol specifies how the same three faults would be **staged in a simulation** of the `rcr` decision path, to test whether the controls the record commits to would catch them. It runs on synthetic applicants and a replica model, never on the live scorer or on customer records. Its findings would support, not replace, the work the record already assigns: the re-test under d2 on the real model (Maria), the impact assessment (Tomas), and the monitor planned under r3 (Jonah). Nothing here has been run.

### Aim

Test, before the board's scale decision, whether three controls on the `rcr` decision path work when the faults already recorded against it are seeded: (1) reason codes reaching the servicing channel, so a declined applicant gets an explanation and a contested decline goes back to an underwriter (against n4); (2) a weekly drift and disparity monitor, so a rate-driven shift is caught between quarterly retrains (against n6 and r3); (3) re-weighting the flagged cohort and re-testing it, so approval rates stay within the four-fifths rule without losing accuracy or calibration (against r2, as decided in d2).

### Why it matters to people

A personal-loan decision changes what someone can do next: replace a car, get to work, cover a gap. The canvas promises a same-session answer, and its Business Value line says the speed only counts if a decline is contestable. If the reasons do not reach the person who answers the phone, a confirmed "no" is a "no" nobody can explain (n4). If rates move and nothing checks the model in between, more people are scored on a stale picture every week until the next retrain (n6, r3). If one group is approved less often than others, the harm falls on that whole group (r2, impact assessment entry 2).

### AI-safety and governance question

When the model points to no, does a person decide, can the applicant get reasons a person can read back, and does a contested decline go back to a person; and will the bank notice, between quarterly retrains, when the model drifts or treats one group worse, before the board decides to scale it?

### Setting and props (simulation)

- **Replica decision path**, built in-house to the `rcr` diagram: application intake → feature store → scorer → calibration and reason codes → either automatic approval (clear approvals) or underwriter review (every decline or borderline score, confirmed with reason codes) → decision record, plus the weekly drift and disparity monitor and the model-risk alert. The scorer is a gradient-boosted tree model with a monotonic constraint on affordability and a calibration layer, trained on synthetic data with the same feature families as `md-credit` (bureau history, affordability, account behaviour). It is a replica, not `md-credit` 3.2; its numbers are not the production model's.
- **Synthetic applicant generator**: produces applications with bureau, affordability and account-behaviour features, a seeded default outcome at the 90-day definition, and a synthetic cohort label used **only** by the test harness (never passed to the scorer). Generator parameters are design parameters set by the team, not fitted to customer records.
- **Simulated time**: 13 simulated weeks = one quarter between retrains; 1,500 applications per simulated week (design parameter). The rolling training window is 36 simulated months of synthetic history, as in Model Training. Because a 90-day default takes months to show, the monitor watches what moves at once (the approval rate, the score mix and the input features), not observed defaults.
- **Servicing desktop mock-up** in a training room: the contact-centre screen showing the decision record, with or without the reason-code field (the arm), the reading-guide card from the change intervention, and the button that logs a contested decline for underwriter review.
- **Underwriter referral queue**: a mock-up of the referral tray, staffed by role-play underwriters, who see the application summary, the score and its reason codes and can approve or decline.
- **Model-risk dashboard**: approval rate per week with a tolerance band; population stability of the affordability features; adverse impact ratio per synthetic cohort.
- **Contest-call scripts**: fixed caller scripts for a declined applicant asking why, played by trained role-players reading from a card; each scripted case has a known decision record with its true reason codes.

### Actors (roles)

| Role | In the film | In the protocol | Person in the record |
|---|---|---|---|
| Applicant | Nadia (fictional), shots 1-2, 6-7, 10, 13 | Synthetic applicants; contest calls by role-players reading a fixed script | — (fictional) |
| Underwriter | Shots 6, 10 | Role-play underwriters from credit operations; decide referred cases and handle contested declines | — (role only) |
| Servicing agent | Shots 7, 10 | Role-play servicing agents from the contact centre, volunteers | — (role only) |
| Initiative owner; owner of r2, e1, A.9 | Figure at the fairness panel, shot 9 (the test owner's team) | Lead for fault F3 and for the underwriter-review path | Maria Okafor, Head of Credit Risk Analytics |
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
| F1 | An applicant contests an underwriter-confirmed decline and the servicing channel has no explanation | Incident **n4** (rights-impact, reportable, open; root cause "Reason codes not surfaced to the servicing channel"); risk **r2**; impact entry 1 | 7 (fault), 10 (control) | In arm S0 the servicing desktop receives the decision record without the reason-code field, as at n4 |
| F2 | A rate change shifts affordability faster than the quarterly retrain | Incident **n6** (performance-drift, open; root cause "Affordability features shifted faster than the quarterly retrain"); risk **r3**; system card limitation | 8 (fault), 11 (control) | At the start of simulated week 4 the generator shifts the affordability features of new applications by a seeded amount sized so that, on the frozen replica, the weekly approval rate moves by four points, the size recorded in n6. The retrain stays at week 13 |
| F3 | One cohort's approval rate falls below four-fifths of the highest cohort's | Risk **r2**; evidence **e1**; impact entry 2; decision **d2** | 9 (fault), 12 (control) | The synthetic training sample under-represents one cohort so that its adverse impact ratio on the replica falls below 0.80 while two other cohorts stay within tolerance, mirroring e1's "two cohorts within tolerance, one flagged" |

Recorded material not seeded: the thin-file limitation in the system card (no risk or incident is recorded against it; reported as a covariate in F3), the out-of-scope uses in the system card, and anything involving `md-embed`.

### Procedure

1. **Before the first run:** pre-register this protocol (hypotheses, arms, measures, margins, seeds) with the model-risk function; Marcus and Tomas sign it off; the generator seed list is drawn and filed.
2. **Build check:** the replica passes the monotonic-affordability check (no applicant's score falls when only affordability worsens) and the per-decile calibration check on a clean synthetic hold-out before any fault is seeded.
3. **F1, contest calls:** 60 scripted contest calls (30 per arm) on underwriter-confirmed declines drawn from the replica, each with a known set of three reason codes. Agents are randomised to arm; each agent takes calls in one arm only. Calls are recorded for scoring and deleted after scoring.
4. **F2, drift replay:** 20 replay runs per arm, each 13 simulated weeks with a different seed; the shift starts at week 4; the arm decides whether the weekly monitor runs.
5. **F3, re-weight and re-test:** train the replica as is (W0) and with the flagged cohort re-weighted (W1), on the same synthetic training set and seed; evaluate both on the same synthetic hold-out with 1,000 bootstrap resamples.
6. **Throughout:** clear approvals issue automatically; every simulated decline or borderline score goes to the role-play underwriter queue and is decided there, with reason codes, before the decision record is written; a contested decline from F1 goes back to the queue. Underwriter decisions that differ from the replica's indication are logged.
7. **After:** export logs with checksums; two raters blind to arm score the F1 calls; results go to the next 30-day review under d2 and to the next board session that reviews rcr, whatever they show.

### Conditions / arms

- **F1. Arm S0, decision only:** the servicing screen shows the decision and no reasons (as at n4). **Arm S1, reasons surfaced:** the screen shows the three reason codes with the reading-guide card. Held constant: caller scripts, decision records, the review path.
- **F2. Arm M0, quarterly only:** no monitor between retrains; the first scheduled look is the week-13 retrain. **Arm M1, weekly monitor:** the drift and disparity monitor runs every simulated week and raises a model-risk alert when the approval rate leaves its band (±3 points around the four-week baseline) or the population stability index of any affordability feature exceeds 0.1 (both design parameters). At 1,500 applications a week the weekly approval rate moves by about 1.3 points (one standard deviation) by chance alone, so a ±2-point band would alert on about one quiet week in ten; the wider band keeps chance alerts rare, and the feature-stability test carries most of the early warning. Held constant: seeds, shift size and start week, retrain schedule.
- **F3. Arm W0, unweighted:** the replica as trained. **Arm W1, re-weighted:** the flagged cohort's training weight raised to match its share of the synthetic population (d2). Held constant: features, monotonic constraint, calibration method, hold-out set.

### Measures and logging

| Variable | Definition | Logged by |
|---|---|---|
| `reasons_read_back` | Per call: the agent states all three reason codes of the decision record correctly, in plain words (yes / no) | Two raters blind to arm; third rater on disagreement; agreement reported |
| `wrong_reason_stated` | Per call: the agent states a reason that is not in the decision record | Raters |
| `review_offered` | Per call: the agent offers to send the decline back to an underwriter, and logs it when the caller accepts | Raters; review-queue log |
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
| `uw_departure_rate` | Share of referred cases where the role-play underwriter's decision differs from the replica's indication; reported as a check on whether the review is more than a rubber stamp (open point 3), descriptive only | Review queue |
| `live_system_touched` | Any read from or write to a production system or customer record (must be 0) | Infrastructure audit log |

### Pre-registered hypotheses

Not on screen: the film shows the recorded events and the intended controls, and states no prediction and no result.

- **H1 (F1, n4):** If the reason codes reach the servicing screen with the reading guide (S1), then agents will read all three reasons back correctly on more contest calls, and offer an underwriter review on more calls, than when the screen shows the decision only (S0). Test: one-sided Fisher exact tests on `reasons_read_back` and `review_offered`, S1 vs S0, α = 0.05 each. **Falsified if either is not higher in S1.** `wrong_reason_stated` is reported by arm as a harm measure; any wrong reason in S1 is reported in full.
- **H2 (F2, n6, r3):** If the weekly drift and disparity monitor runs (M1), then the seeded affordability shift will raise a model-risk alert within two simulated weeks of the shift in at least 18 of 20 runs, with no more than three false alerts across the 60 pre-shift run-weeks (weeks 1-3 of all 20 runs). **Falsified if either condition fails.** `decided_before_alert` is reported for M0 and M1 to show how many decisions each arm leaves on the shifted model; it is descriptive, because M0 has no in-between check by construction.
- **H3 (F3, r2, d2):** If the flagged cohort is re-weighted (W1), then its adverse impact ratio will reach at least 0.80 with every other cohort staying at or above 0.80, while AUC falls by no more than 0.01 and decile calibration error rises by no more than 0.005 against the unweighted replica (W0), and the monotonic-affordability check still passes. Test: bootstrap 95 % intervals; the lower bound of `min_air` must be ≥ 0.80 and the upper bounds of the AUC loss and calibration rise must be within the margins. **Falsified if any condition fails.** The replica's AUC is not compared with the 0.81 recorded on the system card for `md-credit`; they are different models on different data. A pass would show only that re-weighting can close the gap on synthetic data; whether the real gap is explained by legitimate credit factors is for the re-test under d2.

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

The same decision path runs every day in the app: an applicant, a score with reasons, an automatic yes or an underwriter's decision, and a phone call when the answer is no. What the simulation can tell the owners and the board is whether a servicing agent with the reasons on screen can explain a decline and send it back to an underwriter, whether a weekly check would have caught the June shift before the quarterly retrain, and whether re-weighting the flagged cohort keeps every group within the four-fifths rule without costing accuracy or calibration. Those are the three questions the board needs answered before the scale decision.

### Traceability

| Film element or fault | Canvas blocks | Governance record ids |
|---|---|---|
| Shot 1 Open | Business Value | `rcr` summary; `w1-o1` |
| Beat 1, shot 2 At home | Business Problem; Customer Value | `rcr`; impact-assessment scope |
| Beat 1, shot 3 The old way | Business Problem | `rcr` |
| Beat 2, shot 4 Inside, data | Data Strategy; Objective Function | `ds-bureau`, `ds-core`, `as-fs`; diagram `rcr`; system card training data; A.7 |
| Beat 2, shot 5 Inside, score | Objective Function; Modeling Approach | `md-credit` (model note); diagram `rcr`; e2 |
| Beat 2, shot 6 Underwriting desk | Customer Value; Business Value | diagram `rcr` (automatic approval; underwriter review); system card intended use and oversight; impact-assessment scope; A.9; change intervention "Underwriter shadow-scoring week" |
| Beat 3, shot 7 Contact centre / F1 | Customer Value (gap) | **n4**; r2; impact entry 1; A.8 |
| Beat 3, shot 8 Model risk desk / F2 | Model Training | **n6**; **r3**; system card limitations; A.6 |
| Beat 3, shot 9 Fair-lending test / F3 | Objective Function (features that can carry disparity) | **r2**; **e1**; impact entry 2; A.5 |
| Beat 4, shot 10 Contact centre, reasons | Customer Value; Business Value | n4 (target remediation); system card oversight; impact-assessment scope (a contested decline returns to an underwriter); A.8, A.9; change intervention "Reason-code reading guide for servicing" |
| Beat 4, shot 11 Model risk desk, monitor | Model Training | diagram `rcr` (weekly drift + disparity monitor, model risk alert); r3 treatment; A.6 |
| Beat 4, shot 12 Governance board | Business Value | **d2**; r2 treatment (30-day review); **e1**, **e2**; `bm-q2`, `bm-jul`; A.5, A.8 |
| Shot 13 Close | Business Value; Customer Value | `rcr` summary (board decision to scale); `bm-jul`; `w1-o1` |
| H1 | Customer Value | n4, r2, A.8, A.9 |
| H2 | Model Training | n6, r3, A.6 |
| H3 | Modeling Approach; Data Strategy | r2, e1, d2, A.5 |
