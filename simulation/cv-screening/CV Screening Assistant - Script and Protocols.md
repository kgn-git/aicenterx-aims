# CV Screening Assistant — Script and Protocols

Governing sources: the AI Canvas for the initiative **CV Screening Assistant** (`hiring`) and its governance record in `index.html` (`INITIATIVES`, `CANVASES.hiring`, `IMPACTS.hiring`, `RISKS` r1 and r4, `DECISIONS` d1, `EVIDENCE` e5, `MEETINGS` bm-q2, bm-jul-x and bm-jul, `BOARD_SEATS`, `MODELS` and `SYSTEM_CARDS` md-embed, `DATASOURCES` ds-cvs, `SUPPLIERS` sup-tr, `SOURCING`, `CHANGE`, `BUDGETS`, `WAVES` w3-o1, `CONTROLS` A.5 to A.10), and the plan in GitHub issue #4 (parent #1). The technical contract is `simulation/_template/README.md`. Format and structure follow `simulation/Village Film C - Three Questions - Script and Protocols.md`; nothing from the robot village is used. This is a standalone film, set where the assistant would be used: a recruiter's desk, an audit desk, an applicant's kitchen and the governance board.

Runtime 59 s: open card 4 s → Beat 1 The situation 10 s (5 / 5) → Beat 2 The AI at work 13.5 s (4.5 / 4.5 / 4.5) → Beat 3 What can go wrong 15 s (4 / 5 / 6) → Beat 4 How it is kept safe 12.5 s (4.5 / 4 / 4) → close card 4 s. The four beats together run 51 s, inside the 45-60 s target set in #1. Every shot is its own scene in `FILM.scenes`, and cuts land exactly on shot boundaries. Autoplay, loop, seekable (a pure function of t).

**Status of the use case.** The initiative is at stage *Idea*, tier *High*, disposition *Blocked*. The board holds it at the gate (d1). So the film shows the assistant **as proposed**, never as something in use. Every applicant and every CV in the film is made up. No real application from `ds-cvs` (Applicant CVs) is used in the film or in the protocol.

All numbers in this document are **design parameters** unless labelled otherwise. No results are reported anywhere. The hypotheses are pre-registered predictions. The "planted fault" in Beat 3 is a staged test fault, not a finding about the proposed assistant.

**Revision (realism review).** This version was revised after a read-through by two critics: a talent-acquisition practitioner (recruiter and HR business partner) and an AI-governance and regulatory lead (EU AI Act, GDPR including Art. 22, ISO/IEC 42001 and 23894, EU equal-treatment law). The changes: the queue order and screening practice are now as recruiters really work (oldest first, eligibility questions first, a bulk "not progressing" step); the claim that the tool "never decides" is softened, and Beat 3 now shows the real risk behind it: a low-ranked CV closed without anyone reading it; the applicant's "why?" is a reply to a rejection email, answered with a template; the board minutes a decision instead of stamping a card; e5 is now named as the draft FRIA, in line with the record; and Part 2 adds the legal points the gate will meet (provider duties, DPIA, Art. 22 and AI Act Art. 86, how to read the four-fifths rule, consulting employee representatives). The on-screen word total is unchanged at 278.

---

## Usage situation

The scene is a high-volume external requisition in People / HR, the scope named in the impact assessment ("Shortlisting support for external hiring across all requisitions in People / HR").

| Element | In the film | Traces to |
|---|---|---|
| **Who uses the AI** | A recruiter in People / HR (a role, unnamed). The recruiter makes the shortlist; the assistant only orders the queue. | Business Problem; Modeling Approach ("it ranks for a recruiter and never decides on its own") |
| **Who is affected** | Applicants to the requisition. Two are shown: a matched pair of made-up CVs (Beat 3, audit desk) and one made-up applicant who is turned down (Beat 3, kitchen). | Customer Value; `IMPACTS.hiring` (affected: groups, individuals) |
| **Where** | Recruiter's desk in an open-plan People / HR office. Then an independent auditor's desk, an applicant's kitchen at home, the governance board room and the Data Protection Officer's office. | Business Problem; d1; e5 |
| **When** | A Monday morning, after the job advert has closed (design parameter: 1,200 applications in 10 days for a customer-service adviser role, counted after the applicant tracking system's standard eligibility questions such as right to work and shift availability). The recruiter also carries other open requisitions and can screen about 120 CVs properly in the time set aside (design parameter). The applicant tracking system lists applications oldest first, so the latest applicants sit at the bottom. The rejection reaches the applicant about two weeks later and is read on a weekday evening. | Business Problem ("cannot read every application for a high-volume requisition"); SA1 |
| **What triggers the AI** | The advert closes, and the queue is far larger than the recruiter can read. As proposed, the assistant scores every application in the queue against the requisition. | Business Problem; Objective Function |
| **Input** | Application text and structured CV fields, read through the applicant tracking system. Special-category data is in scope, and that question is unresolved. | Data Strategy; ds-cvs (category *HR / employee records*: high sensitivity, personal data) |
| **What the AI does** | It embeds each application with the shared document embedding model (md-embed v1.4) and scores how well it matches the requisition. | Modeling Approach; Objective Function; md-embed |
| **What the AI outputs** | A ranked queue: a match bar on every application, closest matches first, and a shortlist line the recruiter can see. It gives no accept or reject decision. | Modeling Approach; Objective Function |
| **Who acts on it** | The recruiter opens the top of the queue, moves applications into the shortlist tray, and can pull any application up from below the line. Once the shortlist is full, the rest of the queue is closed as "not progressing" in one bulk step, as recruiters do today (SA5). As proposed, the shortlist choices would later become the feedback the model learns from. | Modeling Approach; Model Training; SA5 |
| **What the applicant sees** | An outcome only: a standard rejection email. An applicant who replies to ask why gets the standard "we cannot give individual feedback" answer. If their CV sat below the line, no one read it, and the proposal has no way yet to turn a match score into a reason. | Customer Value ("a rejected candidate cannot yet be given the reason"); impact entry 2 (transparency); SA4; SA5 |
| **What is held** | All of it. The board holds the use case at the gate until a fundamental-rights impact assessment (FRIA) and an independent bias audit are complete. The FRIA is on file as a draft (e5). | d1; r1; r4; e5; Business Value ("no value is claimed while the use case is held at the gate") |

## Canvas assumptions

**None needed.** All seven AI Canvas blocks for `hiring` are filled in the prototype (the canvas register shows 8 of 8 initiatives complete). Issue #4 was written when only Business Problem and Data Strategy were filled; the other five blocks have since been added and are built into `index.html`. This script quotes the canvas as it now stands:

| Block | Canvas text (verbatim, `CANVASES.hiring`) |
|---|---|
| Business Problem | Recruiters cannot read every application for a high-volume requisition, so good candidates are missed. |
| Business Value | Recruiter time moves from first-pass reading to a reviewable shortlist; no value is claimed while the use case is held at the gate. |
| Objective Function | Match between an application and the requisition, scored from CV text and structured CV fields; which fields must be excluded as protected-group proxies is undecided. |
| Modeling Approach | Similarity ranking on the shared document embedding model, co-built with TalentRank Partners; it ranks for a recruiter and never decides on its own. |
| Model Training | Nothing is trained while the gate holds; as proposed, recruiter shortlist decisions are the feedback, and an independent bias audit must clear each version first. |
| Customer Value | As proposed, every application is considered rather than missed, but a rejected candidate cannot yet be given the reason for the outcome. |
| Data Strategy | Application text and structured CV fields; special-category data is in scope and unresolved. |

**Staging assumptions (not canvas content).** The film and the protocol need a few concrete details that neither the canvas nor the record states. Each one is a design parameter for review, not a fact about the initiative:

- **SA1:** The requisition is for customer-service advisers and draws 1,200 applications that pass the standard eligibility questions. The recruiter can screen about 120 properly, and the shortlist holds 40 (for a telephone screen). The queue is listed oldest first.
- **SA2:** The field that differs within the matched pair on screen is a **career break** of 12 months or more. It is one of several candidate proxy fields (Part 2, F1). The canvas leaves open which fields count as proxies, so this is an example, not a decision.
- **SA3:** The assistant shows a **shortlist line** at the 40th place in the queue. The canvas says the assistant ranks; where a recruiter would see a cut-off is not recorded.
- **SA4:** The rejected applicant asks why by **replying to the rejection email**. The reply that comes back is the standard template ("we are unable to give individual feedback"). The canvas says no reason can yet be given; the channel is not recorded.
- **SA5:** Once the shortlist of 40 is full, the recruiter closes the rest of the queue as **"not progressing"** in one bulk step, as is common practice with an applicant tracking system. The record does not say what happens below the line; this assumption is what turns a rank into an outcome, and Part 2 (O8) treats it as the main legal question.

## Governance record used (all from `index.html`)

| Record | Content | Owner / by |
|---|---|---|
| Initiative `hiring` | CV Screening Assistant. Stage Idea, tier High, BU People / HR, disposition Blocked, value Not started. Sourcing partner-co-build with sup-tr. Consumes asset as-emb. Regulations eu-ai-act, gdpr, iso-23894. Summary: "Proposed CV screening aid — held at the gate pending a fundamental-rights impact assessment and bias audit." | Owner Leah Simmons (Head of Data Science); sponsor Sam Duarte (Chief Commercial Officer) |
| Risk **r1** | No signed-off fundamental-rights impact assessment on a high-risk hiring use case. Harm discrimination; likely / severe; Plan & Design; control A.5; status *Blocked at gate*; treatment *avoid*, 30-day review; decision d1. Why: "EU AI Act Annex III high-risk employment use. The board made a signed-off FRIA a gate condition, so deploying without one breaches that decision and leaves the deployer's high-risk duties unevidenced." | Tomas Berg (DPO) |
| Risk **r4** | No bias audit before shortlisting decisions. Harm discrimination; likely / major; Develop; control A.6; status *Not started*; no treatment; no decision. Why: "Automated shortlisting without a bias audit risks discriminatory outcomes at scale." | Tomas Berg (DPO) |
| Decision **d1** | aiia-trigger, 2026-06-12, meeting bm-q2: "Board holds CV screening at the gate until a FRIA and an independent bias audit are complete." | Alicia Reyes (Board Chair) |
| Meeting **bm-q2** | Q2 governance board, 2026-06-12, held, quorate: 7 of 8 seats filled by six people (Tomas Berg holds both the AI Impact Assessment Owner and the DPO seats; the competence seat is David Chen, COO Retail Banking; the lifecycle seat is vacant). Reviewed hiring, rcr, chatbot. Minute: "CV screening held at the gate. Credit scoring mitigation agreed. Chatbot assessment signed off for pilot scope." | Chair Alicia Reyes |
| Meeting **bm-jul-x** | Out-of-cycle board session, 2026-07-14, held. Reviewed chatbot only; `hiring` was not on its agenda. | Chair Alicia Reyes |
| Meeting **bm-jul** | Q3 governance board, 2026-07-24, status *scheduled* in the record; reviews rcr and hiring. | Chair Alicia Reyes |
| Evidence **e5** | "CV screening fundamental-rights impact assessment (FRIA), draft", kind aiia, control A.5, captured 2026-06-28, due 2026-07-31: "The FRIA the board required at the gate: scope, affected groups and harm entries drafted; sign-off withheld pending the independent bias audit." | Tomas Berg (DPO) |
| Impact assessment (`IMPACTS.hiring`, the FRIA's content) | Status in-progress. Scope: "Fundamental-rights impact assessment (FRIA) required by the board: shortlisting support for external hiring across all requisitions in People / HR." Entry 1: discrimination, groups, likely, severe, "Systematic under-shortlisting of candidates from a protected group." Entry 2: transparency, individuals, likely, major, "A rejected candidate cannot obtain the reason for the outcome." | (A.5, Tomas Berg) |
| Incidents | **None recorded for `hiring`.** The one incident on the model it would use is **n8** (raised on `chatbot`, model md-embed, security-breach, open): "Shared embedding index returned document titles across business units"; root cause "No per-tenant isolation on the shared vector index." | n8 raised by Leah Simmons |
| Model **md-embed** | Document embedding model v1.4, LLM/NLP, in use, in-house, consumed by chatbot, rcr and hiring, asset as-emb. | Leah Simmons |
| System card md-embed | Intended use: "Produce retrieval embeddings for internal document search across the portfolio." Out of scope: "Any use as a standalone decision signal, or on personal data outside the approved corpora." Training data: "Open-weights base, adapted on internal document titles; no customer text." Evaluation: Recall@10 per consuming initiative. Limitations: "Domain drift as the corpus grows; no per-tenant isolation of the index." Oversight: "Consumers must show the retrieved source alongside any generated text." Reviewed 2026-05-11. | Leah Simmons |
| Data source **ds-cvs** | Applicant CVs, category HR / employee records (high sensitivity, personal data), system Applicant tracking, feeds as-emb. | — |
| Supplier **sup-tr** | TalentRank Partners, partner-co-build, posture High, control A.10: "Co-build partner on the held hiring use case; no assessment on file." Sourcing rationale: "Co-build with a partner who has the assessment science; the legal exposure stays with us, which is the open question." | (A.10, Priya Nandakumar) |
| Controls | A.5 impact assessment, in progress (Tomas Berg). A.6 life cycle, in progress (Marcus Webb). A.7 data, in progress (Leah Simmons). A.8 information for interested parties, **not started** (Tomas Berg). A.9 use and human oversight, in progress (Maria Okafor). A.10 third parties, in progress (Priya Nandakumar). | as listed |
| Change | Ambition Reshape; ADKAR 30 / 20 / 10 / 5 / 0 (all below the 40 weakness threshold); no interventions planned. | Sam Duarte |
| Wave | Wave 3 "New ground", objective w3-o1 "Reach a defensible position on AI in hiring", measured as "FRIA and bias audit complete and signed off". | Lead Sam Duarte |
| Budget | 410 total (technology 150, data 110, people and process 150); 45 spent. Units as in the prototype. | — |

---

## Part 1 — Shot script

Conventions: `start` and `dur` in seconds. The film is set indoors at human scale, so the camera clearance is a design parameter of **≥ 0.6 m from every collider and every figure**, checked by `FILM.clearance(t)` at 0.1 s steps (the Village Film's 2.5 m is for an outdoor village). Eye-level shots sit at 1.2-1.5 m (a seated or standing person's eye line). An aimed camera places the subject at a stated screen offset (`+x` right of centre, `+y` above centre, as fractions of the half-frame), so the subject sits in the upper right and the lower left, under the caption block, is plain desk, floor or wall.

**All readable text lives in the HTML overlay.** Screens, cards, folders and phones in the world carry only glyphs, bars and colours: no words, no digits and no names. Figures are low-poly and neutral. No figure's face, skin tone, clothing or body is used to signal a protected characteristic, and the matched pair in Beat 3 are two CV cards, not two people.

Colour meanings in the world (fixed for the whole film):

| Colour | Meaning |
|---|---|
| **Blue** `#4a7fd4` | An application (a CV card) |
| **Amber** `#e9a23b` | The assistant's output: a match bar on a card, and the rank order |
| **Green** `#3fa34d` | A person's decision: a recruiter's shortlist tick, a filled check box, a signature |
| **Red** `#d84a3a` | A fault or a harm: the planted fault, an unanswered "why", the hold padlock on the use-case card and the gate |
| **Grey** `#8a8f98` | Not reached or not available: an unread card, an empty reason, an unsigned line |
| **Dashed white line** | The shortlist line in the queue |

Accent colour for the overlay rule and the beat indicator: People / HR violet `#8e6cc9`. The open and close cards use the neutral paper accent `#e8e6e1`.

The overlay shows (the overlay contract of `simulation/_template/README.md` §1.5):
- the four-step beat indicator `The situation → The AI at work → What can go wrong → How it is kept safe`, with the current beat lit (at phone width, the current beat in words and the others as dots);
- one headline and at most one support line;
- a thin rule in the accent colour;
- top left, the setting: `The recruiter's desk`, `Inside the assistant`, `The audit desk`, `An applicant's kitchen`, `The governance board`, `The privacy office`, and `CV Screening Assistant` on the open and close cards.

**Allowed overlay extras.** The template adds four overlay elements beyond the headline, support line and indicator. All four are kept in this film, and they are the only other readable overlay elements allowed:
1. **Initiative label, top right.** It is the same on every scene. In this film the slot carries the fixed pill `Held at the gate · made-up applicants` instead of the bare initiative name (the name is already in the setting label on the cards and in the title). It tells the viewer throughout that nothing shown is in use.
2. **Beat numeral.** The large numeral `1` to `4` in the People / HR violet accent, at the start of the beat row, on beat shots only. It numbers the four beats, not the shots.
3. **Numbered navigation dots.** The rail on the right has one numbered dot per beat group (`1` to `4`), plus the open and close cards and a list button. The fly-out list names cards by name, beats by numeral and label, and each shot of a multi-shot beat by its short navigation label (table below).
4. **Source line.** A small line in the beat row naming the record the shot traces to, 10 words or fewer. Every source line names a real record in `index.html` (a canvas block, risk, impact entry, decision, meeting, evidence item or control). It never names a protocol label such as F1, SA2 or H2. It never cites a result. The beat row, and with it the source line, is hidden on the open and close cards.

| shot | source line (exact on-screen text) | records it names | navigation label (fly-out list) |
|---|---|---|---|
| 1.1 | AI Canvas: Business Problem | `CANVASES.hiring` businessProblem | Too many CVs |
| 1.2 | AI Canvas: Business Problem | `CANVASES.hiring` businessProblem | Who gets read first |
| 2.1 | AI Canvas: Objective Function, Data Strategy, Modeling Approach | `CANVASES.hiring` | Scoring each CV |
| 2.2 | AI Canvas: Modeling Approach; control A.9 | `CANVASES.hiring` modelingApproach; `CONTROLS` A.9 | Ranked for the recruiter |
| 2.3 | AI Canvas: Customer Value, Business Value | `CANVASES.hiring` customerValue, businessValue | Every CV scored |
| 3.1 | Risk r4; impact assessment, entry 1 | r4; `IMPACTS.hiring` entry 1 | Two equal CVs |
| 3.2 | Risk r4; impact assessment, entry 1 (staged test) | r4; `IMPACTS.hiring` entry 1 | The planted fault |
| 3.3 | AI Canvas: Customer Value; impact entry 2 | `CANVASES.hiring` customerValue; `IMPACTS.hiring` entry 2 | No reason given |
| 4.1 | Board decision d1, Q2 board, 12 June 2026 | d1; bm-q2 (2026-06-12) | The board holds it |
| 4.2 | Evidence e5, FRIA draft; control A.5 | e5; `CONTROLS` A.5 | Review not signed |
| 4.3 | AI Canvas: Model Training; risk r4; control A.6 | `CANVASES.hiring` modelTraining; r4; `CONTROLS` A.6 | No training yet |

Changed this round: shot 3.2's source line no longer names the protocol label "planted fault F1" (not a record); it now reads "(staged test)". Shot 4.2's names e5 as the FRIA draft, in line with e5's title.

The overlay, playback bar, scene navigation, `Paused` pill, phone-width layout and `data-caption` behaviour follow the shared template from #1. The caption carries the headline and the support line for every shot. On the close card the caption holds while the picture fades to black, so caption and picture leave together.

### Numbering convention

The film tells one initiative in four **beats**. The only numbers the overlay shows are the beat numerals `1` to `4` (the beat row and the navigation dots, one number per beat), the record ids and the date in a source line, and the clock in the playback bar. There is no scenario numeral (there is only one initiative), no shot number and no hypothesis label. The shot numbers below (`0`, `1.1` … `4.3`, `C`) are for this document and the test only.

| # | start s | dur s | beat | setting (top left) | camera | world action (what figures and objects visibly do) | headline (exact on-screen text) | support line (exact) | traces to |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 4 | Open card | CV Screening Assistant | Slow push from 3.2 m to 2.4 m toward a dim recruiter's desk at 1.4 m height, the monitor aimed upper right (offset +0.25 / +0.18) | The monitor glows. A column of blue CV cards fills its left side. A small red padlock sits in the screen's top corner. The office beyond is empty and the lights are low. | CV Screening Assistant, as it is proposed. | Every applicant here is made up. The tool is on hold. | Initiative `hiring` (stage Idea, disposition Blocked); d1 |
| 1.1 | 4 | 5 | The situation | The recruiter's desk | Over the shoulder, 1.6 m behind the seated recruiter at 1.35 m; a slow push in; the monitor upper right (offset +0.25 / +0.15) | Monday morning light. A requisition card (a headset glyph) sits at the top of the screen, beside two smaller requisition cards (the recruiter's other open roles). Blue CV cards drop into the queue column one after another, the ten days of the advert compressed, until the column runs past the bottom of the screen. A thin bar beside the column fills past a dashed mark (the reading budget) and keeps going in grey. The recruiter scrolls to the end of the column and back to the top. | One job advert brought in far more CVs than anyone can read. | Good people are missed when no one gets to their CV. | Business Problem; SA1 |
| 1.2 | 9 | 5 | The situation | The recruiter's desk | From the side of the desk at 1.3 m, 2.0 m away; a slow dolly along the desk edge; the screen upper right (offset +0.22 / +0.16) | The recruiter works from the top of the list, which runs oldest first: each opened card flashes white and moves aside, most after a few seconds' look. The wall clock (hands only) sweeps from morning to mid-afternoon, and the window light turns warm. The cards still at the bottom of the column, the latest applicants, turn grey, unread. | CVs near the bottom of the pile may never be opened. | The recruiter has to choose who gets read first. | Business Problem; SA1 |
| 2.1 | 14 | 4.5 | The AI at work | Inside the assistant | A separate abstract set standing for the inside of the assistant: a flat, lit space where the cards float at life-size scale. The shot opens on the monitor's glow fading out (0.3 s) and the camera pushes slowly from 2.0 m to 1.4 m at 1.4 m height toward the active card, which sits upper right (offset +0.2 / +0.2). The camera never passes through the monitor | One blue CV card splits into thin text bars (the CV text) and a row of small square tiles (the structured fields: education, experience, skills, dates). A dotted arc runs from the card to the requisition card. An amber match bar grows along the card's edge. The next cards follow in a quick cascade, each gaining an amber bar. | The assistant checks how well each CV fits the job. | It reads the CV text and the fields the applicant filled in. | Objective Function; Data Strategy; Modeling Approach (md-embed) |
| 2.2 | 18.5 | 4.5 | The AI at work | The recruiter's desk | Opens close on the screen from beside the recruiter (1.0 m from the monitor, 0.8 m to the recruiter's right, at 1.35 m), then eases back and round to the over-the-shoulder position, 1.4 m behind at 1.35 m, keeping ≥ 0.6 m from the recruiter's head throughout; the screen upper right (offset +0.25 / +0.15) | The cards re-sort by the length of their amber bars, longest at the top. A dashed white shortlist line appears in the column. The recruiter's cursor opens the top card, reads it, and a green tick sends it to the shortlist tray. The recruiter then scrolls below the line, opens one card and drags it up with a green tick (a person's choice that overrides the order). | It puts the closest matches first for the recruiter to check. | It only ranks. The recruiter decides who goes on the shortlist. | Modeling Approach ("ranks for a recruiter and never decides on its own"); A.9 human oversight; SA3 |
| 2.3 | 23 | 4.5 | The AI at work | The recruiter's desk | Wide, from 2.4 m at 1.5 m, a slow crab left; desk and screen upper right (offset +0.2 / +0.12) | Every card in the column now carries an amber bar, so none is grey for want of a score. The cards below the dashed line stay unopened (no white flash): scored is not the same as read. Then the whole screen turns to a pale wireframe outline, as on a planning drawing, and the red padlock in the corner pulses once. | As planned, every CV would be scored, not just those read first. | This is a plan. It has not been used on real people. | Customer Value ("as proposed, every application is considered"); Business Value ("no value is claimed") |
| 3.1 | 27.5 | 4 | What can go wrong | The audit desk | A slow push from 2.2 m to 1.6 m at 1.3 m toward an auditor's desk with two monitors; the left monitor upper right (offset +0.24 / +0.18) | An independent auditor (a role) sits at the desk. Two blue CV cards stand side by side on the left monitor with identical glyph rows. In the second card's timeline row one block is a grey gap (the career break), traced by a thin white outline. A small red pin glyph sits on the matcher icon between the two monitors: the fault the testers planted. | Could a ranking tool treat two equal people differently? | To find out, testers would give it pairs of made-up CVs. | r4; impact entry 1; Objective Function ("which fields must be excluded as protected-group proxies is undecided"); F1; SA2 |
| 3.2 | 31.5 | 5 | What can go wrong | The audit desk | Over the auditor's shoulder at 1.35 m, 1.2 m behind; the two cards upper right (offset +0.22 / +0.2) | Both cards travel the same dotted arc to the requisition card. Their amber bars grow side by side at the same rate, then the second card's bar stops short. The dashed shortlist line drops between them: the first card sits above it, the second below. A red ring pulses around the career-break block. On the right monitor a strip of small pair glyphs fills in, run after run: in most pairs the career-break half sits lower, so the audit reads a pattern across many pairs, not one pair. The auditor marks a red flag on a checklist row (glyph). | These two CVs differ only by a career break, and their ranks split. | This fault was planted. It shows what a bias audit must catch. | r4; impact entry 1 (discrimination, groups, likely / severe); F1 (planted positive control); H2 |
| 3.3 | 36.5 | 6 | What can go wrong | An applicant's kitchen | Evening. A slow push from 1.8 m to 1.3 m at 1.2 m toward a kitchen table; the phone and hands upper right (offset +0.24 / +0.18); the dark window behind | A made-up applicant sits at the table under a warm lamp, two weeks after the advert closed. The phone shows an email with a grey cross (not progressing). The applicant types a short reply (a question-mark glyph) and sends it. A reply comes back as a grey template card: lines of text glyphs with no reason in them. The applicant puts the phone down on the table. Staged as the proposal would work, not as something that has happened: the CV sat below the shortlist line and was closed with the rest of the queue, unopened (SA5). | If a rejected applicant asks why, no one can give a reason. | No one read their low-ranked CV. A rank is not a reason. | Customer Value ("cannot yet be given the reason"); impact entry 2 (transparency, individuals, likely / major); Business Problem; A.8 not started; F2; SA4; SA5; O8 |
| 4.1 | 42.5 | 4.5 | How it is kept safe | The governance board | High angle, 2.6 m up, 3.5 m from the centre of the table; a 15° orbit; the table centre upper right (offset +0.18 / +0.15) | Six figures sit round a table: the board chair at its head, with the DPO (who also holds the impact-assessment seat), the Chief Risk Officer, the Head of Model Risk, the external ethics advisor and the COO Retail Banking in the competence seat (the bm-q2 attendance; no name labels). Papers lie in front of each. A violet card with a CV glyph (the use case) sits on the wall screen. The chair calls the decision and the members nod; at the side of the table the board secretary types the minute. On the wall screen a new row appears in the decision log glyph, and a red padlock closes over the violet card. | The board has held the tool at the gate. | It stays shut until a rights review and a bias audit are done. | d1 (bm-q2, 2026-06-12); r1 (treatment avoid); r4; MEETINGS bm-q2; BOARD_SEATS |
| 4.2 | 47 | 4 | How it is kept safe | The privacy office | Top-down at 1.0 m over a desk, tilting to 45° as it eases back; the folder upper right (offset +0.2 / +0.18) | The DPO's desk. A folder opens: three pages of filled dark bars (scope, affected groups, harm entries), drafted but with no tick, since green is kept for a person's decision. The signature line at the foot is grey and empty, and a pen lies beside it, untouched. Next to the folder, a card holds two empty check boxes: a scales glyph (rights review) and a glyph of two equal figures (bias audit). | The rights review is drafted, but no one has signed it. | Sign-off waits for an independent bias audit. | e5 (FRIA, draft; sign-off withheld pending the independent bias audit); A.5 in progress; r1; r4 |
| 4.3 | 51 | 4 | How it is kept safe | The recruiter's desk | Over the shoulder at 1.35 m, easing back from 1.4 m to 2.2 m; the screen upper right (offset +0.25 / +0.15) | Dusk. On the screen a loop of glyphs: the green-ticked shortlist tray → a dashed arrow → a shield checkpoint (the independent audit) → the assistant icon, with a row of version pips, → back to the queue. The whole loop is dim and the arrow is still. A red padlock sits on the arrow between the tray and the shield, so nothing flows. | Nothing is trained while the gate holds. | Later, recruiters' choices would teach it, once an audit clears each version. | Model Training (verbatim content); r4; A.6 in progress |
| C | 55 | 4 | Close card | CV Screening Assistant | Slow pull back from the recruiter's monitor, 2.4 m to 3.4 m at 1.4 m; the screen upper right (offset +0.22 / +0.15); the last 0.7 s fades to black with the caption | The red padlock in the corner of the screen. Above it the two check boxes from the privacy office, both still empty, and a small violet board glyph beside them. The queue column behind is a pale wireframe. | Only the board lifts the hold, once both checks are signed off. | Until then, the tool is not used on anyone. | d1; w3-o1 ("FRIA and bias audit complete and signed off"); e5; `hiring` (stage Idea, disposition Blocked) |

### Word count and readability (on-screen text set by this script)

Counted the Village Film's way: whitespace-separated tokens that contain a letter or a digit. The Flesch-Kincaid grade is 0.39 × words ÷ sentences + 11.8 × syllables ÷ words − 15.59, with a vowel-group syllable count and sentences counted at `.`, `!` or `?`. Every line here is written by the team (there are no client-worded lines), so every line must meet the limits.

Limits (adopted from the Village Film, design parameters): the safety question ≤ 20 words (shot 3.1 headline); every other headline and support line ≤ 14 words; FK grade ≤ 8 for every line. On-screen pace is at most 5.5 words per second of shot, counting headline and support together. The pace limit is new here; the Village Film did not set one.

| shot | text element | words | limit | FK grade | pace (w/s, headline + support) |
|---|---|---|---|---|---|
| 0 | headline (title) | 7 | ≤ 14 | 7.4 | 4.5 |
| 0 | support | 11 | ≤ 14 | 4.8 | |
| 1.1 | headline | 12 | ≤ 14 | 5.8 | 4.6 |
| 1.1 | support | 11 | ≤ 14 | 4.8 | |
| 1.2 | headline | 11 | ≤ 14 | 5.9 | 4.0 |
| 1.2 | support | 9 | ≤ 14 | 3.7 | |
| 2.1 | headline | 10 | ≤ 14 | 2.5 | 4.9 |
| 2.1 | support | 12 | ≤ 14 | 3.8 | |
| 2.2 | headline | 11 | ≤ 14 | 4.8 | 4.9 |
| 2.2 | support | 11 | ≤ 14 | 4.8 | |
| 2.3 | headline | 12 | ≤ 14 | 5.8 | 5.3 |
| 2.3 | support | 12 | ≤ 14 | 0.5 | |
| 3.1 | headline (safety question) | 9 | ≤ 20 | 7.6 | 5.0 |
| 3.1 | support | 11 | ≤ 14 | 4.8 | |
| 3.2 | headline | 13 | ≤ 14 | 4.9 | 5.0 |
| 3.2 | support | 12 | ≤ 14 | 0.5 | |
| 3.3 | headline | 12 | ≤ 14 | 7.8 | 4.0 |
| 3.3 | support | 12 | ≤ 14 | 2.5 | |
| 4.1 | headline | 9 | ≤ 14 | 1.0 | 4.9 |
| 4.1 | support | 13 | ≤ 14 | 5.8 | |
| 4.2 | headline | 11 | ≤ 14 | 4.8 | 4.5 |
| 4.2 | support | 7 | ≤ 14 | 7.4 | |
| 4.3 | headline | 7 | ≤ 14 | 5.7 | 4.8 |
| 4.3 | support | 12 | ≤ 14 | 7.8 | |
| C | headline | 12 | ≤ 14 | 4.8 | 5.25 |
| C | support | 9 | ≤ 14 | 5.0 | |
| **Total** | | **278** | | max **7.8 (≤ 8)** | max **5.3 (≤ 5.5)** |

Phase 2 keeps these 26 lines in a JSON file beside the film, in the shape of the Village Film's `test/film-c-lines.json`, and checks them before any build ships.

Fixed overlay furniture is not counted: the beat indicator (15 words, on every beat shot), the setting names top left, the initiative-label pill `Held at the gate · made-up applicants`, the beat numerals, the `Paused` pill, and the playback and navigation labels. The source lines are not counted in the 278 either; each is held to the template's own limit of 10 words or fewer (the longest have 8 words). No footnotes appear on screen. If WebGL cannot start, the fallback page shows the title `CV Screening Assistant, as it is proposed.`, the note `This film needs 3D graphics (WebGL). Your browser could not start it. Here is the film in words.`, and then every shot as `<beat> — <setting>` followed by its headline and support line exactly as above, with no shot numbers and no times.

### Plain-language conventions

1. **Full sentences, never fragments.** Each line has its own subject and verb. The open title is the one exception, as in the Village Film.
2. **People first.** Beat 1 names the people with the stake (the recruiter and the applicants). Beat 3 asks what could go wrong for an applicant. Beat 4 names who holds the tool (the board) and who signs (the rights review owner).
3. **Proposed, not in use.** Every line about what the assistant does is in the present tense only where it describes the design ("It reads…", "It only ranks…"), and the lines that describe benefits say "as planned" or "would". Shot 2.3 says outright that it has not been used on real people, and the top-right pill says so on every shot.
4. **No claim stronger than the design can carry.** The film does not say the tool "never decides": a rank that decides who is read can decide who is rejected (SA5, O8). Shot 2.2 says it only ranks and the recruiter decides; shot 2.3 says scored, not read; shot 3.3 shows what a low rank can mean for an applicant.
5. **A planted fault is called planted.** Shot 3.2 says the split was planted. The film never implies that the proposed assistant has been tested or has been shown to be biased.
6. **Jargon is replaced, not explained on screen.** The on-screen words on the left stand for the terms on the right:

| on screen | term in the record or protocol |
|---|---|
| "the tool", "the assistant" | CV Screening Assistant (`hiring`), as proposed; similarity ranking on md-embed |
| "on hold", "held … at the gate", "the gate holds" | disposition *Blocked*; decision d1; r1 status *Blocked at gate* |
| "checks how well each CV fits the job" | Objective Function: match between an application and the requisition |
| "the CV text and the fields the applicant filled in" | Data Strategy: application text and structured CV fields |
| "puts the closest matches first" | similarity ranking (Modeling Approach) |
| "it only ranks", "the recruiter decides who goes on the shortlist" | "ranks for a recruiter and never decides on its own"; A.9 human oversight |
| "every CV would be scored, not just those read first" | Customer Value: "every application is considered rather than missed"; measure `scored_coverage`. Scored is not read: the cards below the line stay unopened |
| "two equal people", "testers would give it pairs of made-up CVs" | matched-pair (correspondence) test on synthetic applications (Part 2) |
| "differ only by a career break" | a pair that differs in one candidate proxy field (F1, SA2) |
| "their ranks split" | the two halves of a pair fall on opposite sides of the shortlist line (`pair_split`) |
| "this fault was planted" | V+, the positive-control version with a planted proxy weight (F1, H2) |
| "a bias audit" | the independent bias audit required by d1 (risk r4, control A.6) |
| "if a rejected applicant asks why, no one can give a reason" | impact entry 2: "A rejected candidate cannot obtain the reason for the outcome"; Customer Value; A.8 not started (F2) |
| "no one read their low-ranked CV", "a rank is not a reason" | SA5 (the queue below the line is closed as not progressing); Business Problem; a match score carries no reason a person can read (F2; `reason_available`, `unread_rejection_share`; O8) |
| "the tool is not used on anyone" | stage *Idea*, disposition *Blocked*; d1 (the use case has not been deployed) |
| "the board" | the governance board, Q2 session bm-q2 (2026-06-12), chaired by the Board Chair |
| "a rights review", "the rights review" | the fundamental-rights impact assessment (FRIA) required by d1 (risk r1, control A.5); on file as the draft e5 |
| "the rights review is drafted, but no one has signed it" | e5, "CV screening fundamental-rights impact assessment (FRIA), draft": "sign-off withheld pending the independent bias audit" |
| "nothing is trained" | Model Training: "Nothing is trained while the gate holds" |
| "recruiters' choices would teach it, once an audit clears each version" | Model Training: "recruiter shortlist decisions are the feedback, and an independent bias audit must clear each version first" |
| "only the board lifts the hold, once both checks are signed off" | d1 ("until a FRIA and an independent bias audit are complete"); w3-o1 measure ("FRIA and bias audit complete and signed off"). The two checks are necessary, not sufficient: lifting the hold is a new board decision, which will also meet the open items O1-O12 |

7. **What never changes in a rewrite:** the use case is shown as proposed and held; every applicant is made up; the Beat 3 split is called planted; the board's condition is the two checks named in d1, nothing more and nothing less; and no result is stated anywhere on screen.

---

## Part 2 — Protocol

The film stages, in Beat 3, the test that d1 asks for. This part specifies that test as an experiment, in the shape of the Village Film's protocols. It is a design for the independent bias audit and for the evidence the FRIA would need. It is not a record of an audit that has happened, and it does not decide anything the board has not decided.

### Aim

Find out, before any real applicant is affected, whether the proposed CV Screening Assistant ranks two applications that are equal except for a field that may stand for a protected group on the same side of the shortlist line. Find out whether an independent audit, blind to which model version it is testing, catches a proxy fault that has been planted on purpose. Find out what masking candidate proxy fields does to equal treatment and to match quality. And record whether a reason can be produced for each rejected applicant. Grounding: correspondence (matched-pair) testing of hiring (Bertrand & Mullainathan 2004); the four-fifths rule of thumb for adverse impact, already used in this organisation's credit disparity test (e1); positive controls to establish an audit's sensitivity. The four-fifths rule is a US screening heuristic. EU equal-treatment law in employment (Directives 2000/43/EC, 2000/78/EC and 2006/54/EC) sets no numeric threshold for indirect discrimination, so an `impact_ratio` of 0.8 or more is a flag for review, not a safe harbour.

### Why it matters to people

Applicants to a high-volume job cannot see who read their CV, or whether anyone did. If a ranking tool quietly pushes people with a career break, an older graduation year or a particular postcode below the line, the recruiter may never open those applications, and no one would know (impact entry 1). A rejected applicant who asks why must be able to get an answer, and today the proposal cannot give one (impact entry 2). If the queue below the shortlist line is closed without anyone opening it (SA5), the rank has in effect decided the outcome. The recruiter, the DPO and the board need evidence they can check, not assurances from the model's builders or from the co-build partner.

### AI-safety and governance question

**On screen (shot 3.1, verbatim):** *Could a ranking tool treat two equal people differently?*

Concretely:
1. Does the proposed similarity ranking under-rank one half of a matched pair because of a field that stands for a protected group (risk r4, impact entry 1)?
2. Can an independent audit tell a version with a planted proxy fault from one without it, without being told which is which? (If it cannot, a clean audit result means little.)
3. The canvas leaves open which fields to exclude. Does masking the candidate proxy fields reduce unequal treatment, and what does it cost in match quality?
4. Can a reason be produced for each rejection from what the pipeline records (impact entry 2; control A.8 not started)? And how many rejections would no person have read (SA5, O8)?
5. Once recruiters work from the ranked queue, does their shortlist treat matched pairs as equally as a shortlist made from an unranked queue? And is their own judgement still applied?

### Setting and props

- **The made-up applicant set.** It is written by the research team from templates and contains no text from any real CV and nothing from `ds-cvs`. Each run has a queue of 1,200 applications for one requisition (SA1): **200 matched pairs** (400 applications) and 800 filler applications. Every application carries a ground-truth label, **qualified** or **not qualified**, set against the requisition's stated criteria by two experienced recruiters before the run (agreement checked with Cohen's kappa, at least 0.7; a third rater settles disagreements). A pair's two halves are identical in every field and every sentence except one **varied field**. Pair templates are drawn from qualified profiles written to score near the top of the queue, because a pair can only split across a line at place 40 of 1,200 if it scores near that line; `rank_gap` is read across all pairs, and `pair_split` near the line.
- **Candidate proxy fields** (design parameters, for the FRIA and the auditor to finalise; the canvas says this is undecided): a career break of 12 months or more (the field shown in the film), graduation year, postcode district, first-name pattern, and membership of a named association. There is also one **neutral control field**: swapping the order of two equivalent skills. It sets the background rate at which ranks split for reasons that cannot matter.
- **Model versions** (prepared by the model owner, coded by a third party so that the auditor is blind):
  - **V0, as proposed:** similarity ranking on md-embed v1.4 over CV text and structured fields.
  - **V+, planted fault (positive control):** V0 with a penalty added to the match score whenever the career-break field is present. The penalty is sized to move an affected application down by about 10 percentile points (a design parameter).
  - **VM, masked:** V0 with the candidate proxy fields removed from the structured fields and the matching text spans masked before embedding.
- **The shortlist line** at place 40 of 1,200 (SA3).
- **The audit desk:** the auditor's workstation, holding only the coded versions, the made-up queue and the scoring scripts. It has no network path to the applicant tracking system and no access to `ds-cvs`.
- **The reason check:** for each rejected made-up applicant, a form on which the auditor records whether a reason the applicant could read can be produced from what the pipeline logs (match score, rank, retrieved spans).
- **The recruiter workstation** (Part B only): the queue view shown in shots 1.1 to 2.3, holding made-up applications only.

### Actors (roles)

| Role | Who (prototype people, by role) | Does |
|---|---|---|
| Recruiter (study participant, Part B) | Recruiters in People / HR, volunteers (role, unnamed) | Makes shortlists from made-up queues. Their performance is never reported by name and never used for appraisal. |
| Independent auditor | External to the owner team and to TalentRank Partners (role, unnamed) | Runs Part A blind to version codes, flags proxy effects and fills the reason check |
| Initiative owner; model owner (md-embed) | Leah Simmons, Head of Data Science | Prepares V0, V+ and VM; does not see the audit results until the auditor's report is filed |
| Sponsor | Sam Duarte, Chief Commercial Officer | Owns the business case and the change plan (no interventions recorded yet) |
| Owner of r1, r4 and e5; impact-assessment owner (A.5); DPO; owner of A.8 | Tomas Berg | Approves the made-up data set; confirms no special-category or real applicant data enters the test; receives the audit for the e5 sign-off decision |
| Owner of A.6 (life cycle); AIMS Manager | Marcus Webb, Head of Model Risk | Holds the pre-registration and the version codes; confirms that each version is audited before any training (Model Training) |
| Owner of A.10 (third parties); AI Risk Owner | Priya Nandakumar, Chief Risk Officer | Owns the supplier assessment for TalentRank Partners, which is not on file (O1) |
| Owner of A.9 (use and human oversight) | Maria Okafor, Head of Credit Risk Analytics | Reviews the Part B design for human oversight, as the control owner of record |
| Talent acquisition lead or HR business partner (proposed) | People / HR (role, unnamed) | Co-reviews Part B with the A.9 owner so that the queue, the time budget and the bulk "not progressing" step match how recruiters really work; owns the rejection template and the feedback route (SA4) |
| Employee representatives (proposed) | Works council or staff representatives, where national law gives them a role (role, unnamed) | Consulted before Part B, because the workstation logs individual recruiters' behaviour |
| Internal audit owner; external ethics advisor | Sofia Lindqvist | Ethics review of the protocol (proposed role) |
| Board Chair | Alicia Reyes | Took d1; the gate decision returns to the board |
| Made-up applicants | None: synthetic records | Appear only as CV cards and, in the film, as one low-poly figure |

Roles marked "proposed" are this protocol's suggestion; the record does not assign them.

### Seeded faults

| Fault | What is seeded | From the record | On screen | Measured by |
|---|---|---|---|---|
| **F1: proxy for a protected group** | V+ carries a planted penalty on the career-break field, the positive control. V0 and VM are tested for the same effect, unplanted, across all candidate proxy fields. | r4 (no bias audit before shortlisting); impact entry 1 (systematic under-shortlisting of a protected group); Objective Function (which fields to exclude is undecided) | Shots 3.1 and 3.2, called "planted" | `pair_split`, `rank_gap`, `impact_ratio`, `audit_flags_plant` |
| **F2: no reason for the outcome** | Not planted; it is the proposal's recorded state. The reason check is run on every rejection. | Impact entry 2 (a rejected candidate cannot obtain the reason); Customer Value; A.8 *not started* | Shot 3.3 | `reason_available` |
| **F3: special-category data in the input** | The made-up set includes free-text sentences that disclose special-category data (for example a health condition explaining a career break) in 5 % of applications (design parameter). | Data Strategy ("special-category data is in scope and unresolved"); ds-cvs (high sensitivity, personal data); A.7; GDPR | Not on screen | `special_category_reaching_score`: whether those applications' ranks move when the disclosing sentence is removed |
| **F4: shared index without per-tenant isolation (inherited)** | Not planted in the test, and **not staged as having happened to CVs**. The audit checks whether made-up CV embeddings written to the shared index could be returned to another consumer's query (chatbot, rcr). | n8 (recorded on `chatbot`, model md-embed: titles returned across business units; root cause no per-tenant isolation); md-embed card limitation "no per-tenant isolation of the index"; ds-cvs is recorded as feeding as-emb (O7) | Not on screen | `cross_tenant_return` (yes / no per probe query) |

The record holds **no incident for `hiring`**: it has not been used, so nothing has gone wrong in use. F1 and F2 stage what the impact assessment and r4 name as likely harms. F4 is an incident recorded on another initiative that uses the same model; it is listed because `hiring` would consume the same index, not because it has occurred here.

### Procedure

**Part A: model audit (made-up applicants, no people affected).**
1. **Before the first run:** the research team writes and registers the made-up set (1,200 applications per run, 200 pairs, ground-truth labels by two raters). The DPO confirms no real applicant data and no `ds-cvs` content is used. The AIMS Manager registers the protocol, the seed and the version codes.
2. **Version coding:** a third party labels V0, V+ and VM as A, B and C, using an order drawn from the pre-registered seed. The auditor sees only the codes.
3. **Runs:** each version scores 10 independent made-up queues (fresh pairs and fillers each run, drawn from the seed). Each run logs every application's match score and rank and every pair's two ranks.
4. **Probes for F4:** after each run the auditor issues 20 fixed probe queries through a non-HR consumer path and records whether any made-up CV embedding is returned.
5. **Reason check (F2):** for 50 rejected made-up applicants per run, drawn at random, the auditor records whether a reason the applicant could read can be produced from the pipeline's logs.
6. **Auditor's report:** filed before the codes are revealed. It names, for each coded version and each candidate proxy field, whether it flags a proxy effect.
7. **Unblinding:** the codes are revealed only after the report is filed and checksummed.

**Part B: recruiter-in-the-loop study (made-up applicants, consenting recruiters).** Part B runs only if V0 or VM meets H1 in Part A and the DPO and the ethics review approve.
8. Twelve volunteer recruiters (design parameter) each make two shortlists of 40 from two different made-up queues, with 45 minutes per queue (design parameter). One queue is ranked by the version that met H1 (**Arm R**) and one is shown in random order (**Arm U**). Which arm comes first, and which queue goes with which arm, is counterbalanced from the seed.
9. The workstation logs which applications are opened, for how long, and which are ticked into the shortlist.
10. A short debrief records what the recruiter relied on (fixed-menu answers).

### Conditions and arms

- **Part A, between versions:** V0 (as proposed), V+ (planted fault, positive control), VM (masked proxy fields); 10 runs each. The auditor is blind to the version.
- **Part B, within recruiter:** Arm R (ranked queue) and Arm U (unranked, random order); each recruiter does one of each, counterbalanced.
- **Held constant:** the requisition, the queue size, the shortlist line, the ground-truth labels, the candidate proxy fields, the neutral control field and the time budget (Part B).

### Measures and logging

| Variable | Definition | Logged by |
|---|---|---|
| `scored_coverage` | Share of applications in the queue that receive a match score (the canvas's "every application is considered") | Pipeline log |
| `rank_gap(field)` | Mean signed percentile-rank difference, varied half minus base half, over the pairs for one field | Derived |
| `pair_split(field)` | Share of pairs for one field whose two halves fall on opposite sides of the shortlist line (the on-screen "their ranks split") | Derived |
| `impact_ratio(field)` | Shortlist rate of varied halves ÷ shortlist rate of base halves, per field | Derived |
| `audit_flags_plant` | Whether the auditor's blind report flags the career-break field for the coded version that is V+ | Auditor's report, after unblinding |
| `false_flag` | Fields flagged for a version where, after unblinding, nothing was planted and `impact_ratio` ≥ 0.8 | Derived |
| `qualified_recall@40` | Share of ground-truth qualified applications that make the top 40 | Derived |
| `special_category_reaching_score` | Mean absolute rank change when the disclosing sentence is removed from F3 applications | Derived |
| `cross_tenant_return` | Probe queries that return a made-up CV embedding through a non-HR path | Probe log |
| `reason_available` | Share of sampled rejections for which a reason the applicant could read can be produced | Auditor's reason check |
| `opened_share` (Part B) | Share of the queue the recruiter opened | Workstation log |
| `override_share` (Part B) | Share of the recruiter's shortlist drawn from below the model's line (Arm R only) | Workstation log |
| `unread_rejection_share` (Part B) | Share of the queue closed as "not progressing" (SA5) that the recruiter never opened | Workstation log |
| `human_pair_split` (Part B) | `pair_split` computed on the recruiter's final shortlist | Derived |
| `debrief_reliance` (Part B) | Fixed-menu answer: what the recruiter relied on | Debrief form |

### Pre-registered hypotheses

Analysis unit: the run (Part A) and the recruiter (Part B). The tests are one-sided permutation tests or two one-sided equivalence tests (TOST), α = 0.05 per measure. All margins and thresholds are design parameters; the independent auditor and the FRIA may set stricter ones before the first run.

- **H1 (equal treatment, V0):** *If two made-up applications differ only in a candidate proxy field, then the proposed assistant will rank them on the same side of the shortlist line as often as it does for the neutral control field.* Supported if, for every candidate proxy field, `pair_split` is within 2 percentage points of the neutral-field rate (TOST), `|rank_gap|` ≤ 2 percentile points, and `impact_ratio` ≥ 0.8. Falsified if any field fails any of the three.
- **H2 (audit sensitivity):** *If a proxy penalty is planted in one version, then the independent auditor, blind to the versions, will flag it.* Supported if the auditor's report flags the career-break field on V+'s code, and the flag is reproduced in at least 9 of the 10 V+ runs. Falsified otherwise. If H2 fails, a clean result for V0 or VM is not accepted as audit evidence.
- **H3 (masking):** *If the candidate proxy fields are masked, then pairs will split no more often than under V0, and qualified recall will fall by no more than 5 percentage points.* Supported if `pair_split` under VM ≤ V0 for every field and `qualified_recall@40` under VM ≥ V0 − 5 points. This informs the open Objective Function question; it does not decide it.
- **H4 (recruiter in the loop, Part B):** *If recruiters shortlist from the ranked queue, then their shortlists will split matched pairs no more often than shortlists made from an unranked queue.* Supported if `human_pair_split` in Arm R is within 2 points of Arm U (TOST). `override_share`, `opened_share` and `unread_rejection_share` are reported, not tested: they show whether the recruiter's own judgement is still applied (Modeling Approach: "never decides on its own") and how many outcomes the rank alone would settle (O8). A ranked queue that raises `unread_rejection_share` is a finding for the FRIA even if H4 holds.
- **Not a hypothesis (F2):** `reason_available` is reported for V0 and VM. The record already says that, as proposed, no reason can be given, so a low value would not be a finding. The measure is kept so that the change shows when a reason path is designed. The protocol sets no pass level, because the record sets none; it is flagged for the FRIA (see Open questions).
- **Reported only:** `scored_coverage`, `special_category_reaching_score` (F3) and `cross_tenant_return` (F4).

### Safety and ethics gates

**Recorded gate conditions (from d1).** The use case stays at the gate until both are complete:
- **G1 — FRIA complete** (risk r1, control A.5, owner Tomas Berg). e5 is the FRIA in draft ("CV screening fundamental-rights impact assessment (FRIA), draft"), with sign-off withheld pending the independent bias audit; `IMPACTS.hiring` holds its scope and harm entries. The film calls it "a rights review" in shot 4.1 and "the rights review" in shot 4.2. The FRIA is the **board's own condition**. EU AI Act Art. 27 does not oblige a private employer to carry out a FRIA for a hiring tool (it covers public bodies, private bodies providing public services, and credit and insurance uses under Annex III 5(b) and (c)). The film therefore says only that the board holds the tool until it is done, never that the law requires it (r1's why says the same).
- **G2 — Independent bias audit complete** (risk r4, control A.6, owner Tomas Berg; the A.6 control owner is Marcus Webb). This protocol is a proposed design for that audit. H1 and H2 are its proposed pass criteria; they are design parameters until the auditor and the board adopt them.

**Protocol gates (this protocol's own conditions for running the test).**
- **P1:** Made-up applicants only. No real CV, no `ds-cvs` record and no live requisition is used in any part. The DPO confirms this before the first run.
- **P2:** Part B runs only after Part A, only with a version that met H1, and only with the DPO's and the ethics review's approval. Recruiters volunteer, may withdraw at any time, and are never identified in results. The workstation log is pseudonymised, kept only for the study, and never used for appraisal; employee representatives are consulted first where national law gives them a role.
- **P3:** No version is trained on anything during the test (Model Training: "Nothing is trained while the gate holds"). Part B shortlists are not used as feedback.
- **P4:** If F4 probes return a made-up CV embedding through a non-HR path, the run stops and the finding goes to the model owner and the DPO before any further run.

**Open items in the record that the gate decision will meet.** These are observations from the record, not board decisions:
- **O1, supplier (A.10):** TalentRank Partners has "no assessment on file", and the sourcing rationale names the legal exposure as "the open question".
- **O2, model card fit (md-embed):** the card's intended use is "internal document search"; its out-of-scope list includes "any use as a standalone decision signal, or on personal data outside the approved corpora"; and it was "adapted on internal document titles", not on applications. The record does not show the card updated for ranking applicants.
- **O3, data (A.7, GDPR):** special-category data is "in scope and unresolved" (Data Strategy).
- **O4, transparency (A.8):** "Information for interested parties" is *not started*, and impact entry 2 is rated likely / major.
- **O5, change (ADKAR):** every state is below the 40 weakness threshold and no interventions are planned; the copilot's canned answer names CV screening as the sharpest adoption risk in the portfolio.
- **O6, next session:** the Q3 governance board (bm-jul, 2026-07-24) lists `hiring` for review and is *scheduled* in the record; no minute is recorded for it. The out-of-cycle session in between (bm-jul-x, 2026-07-14) reviewed only the service copilot. The bias audit the FRIA's sign-off waits on has not started (r4, *Not started*), so the record gives that session no basis for lifting the hold.
- **O7, data lineage:** the record lists `ds-cvs` (Applicant CVs) as feeding `as-emb`, the shared embedding asset whose index has no per-tenant isolation (n8; md-embed card). The record does not say whether any CV text has entered the index while the gate holds. For this reason the film does not claim that no real CV goes near the model; it says only that the tool is not used on anyone.
- **O8, automated decision in effect (GDPR Art. 22; EU AI Act Art. 86):** if the queue below the line is closed without a person opening it (SA5), the rank plays the determining role in those rejections. Following the CJEU's *SCHUFA* judgment (C-634/21, 2023), that can count as a decision based solely on automated processing with a similarly significant effect. It then needs an Art. 22(2) basis and safeguards: human intervention, a way to contest, and meaningful information about the logic (Art. 13-15). AI Act Art. 86 separately gives a person affected by a decision based on an Annex III high-risk system the right to a clear explanation of the AI's role. The canvas's "never decides on its own" holds only if every rejection is read by a person or can be reviewed by one. The record has no design for this, and d1 does not name it.
- **O9, provider as well as deployer (EU AI Act):** ranking applicants is profiling, so the Art. 6(3) exemption for narrow tasks is not available and the system is high-risk under Annex III point 4. The organisation builds it in-house on md-embed with a co-build partner and would put it into service for its own use, so it is likely to be the **provider** as well as the deployer. That brings the provider duties (risk management, data governance including bias examination, technical documentation, logging, human-oversight design, accuracy, a quality management system, conformity assessment by internal control, registration in the EU database) on top of the deployer duties in Art. 26: use by competent, trained people (and AI literacy, Art. 4), monitoring, keeping logs for at least six months, telling applicants that a high-risk AI system is used in decisions about them (Art. 26(11)), and informing workers' representatives before workplace use (Art. 26(7)). r1's why names only the deployer's duties. The date from which these duties apply is for legal to confirm.
- **O10, no DPIA in the record (GDPR Art. 35):** large-scale profiling of applicants with special-category data in scope (O3) almost certainly needs a data protection impact assessment. The FRIA can build on a DPIA (AI Act Art. 27(4)) but does not replace it. The record holds neither a DPIA nor a decision that one is not needed.
- **O11, ownership and independence:** r4 (no bias audit) has no treatment and no linked decision, although d1 makes the audit a gate condition. One person, Tomas Berg, is DPO, owner of r1, r4 and e5, owner of A.5 and A.8, and holds two board seats. Under GDPR Art. 38(6) a DPO's other tasks must not create a conflict of interest; owning a risk treatment and signing the FRIA he would also advise on is a question for the board.
- **O12, learning from recruiters' choices (Model Training):** shortlist decisions as feedback teach the model the recruiters' past preferences, including any bias in them, and the model only gets feedback on the applications it ranked high enough to be read. Each retrained version is audited first (Model Training), and a retrained version may also count as a substantial modification for conformity purposes unless the change was planned in the technical documentation.

### Session schedule (design parameter)

Part A: 30 runs (10 per version) in one week, then the auditor's report, then unblinding. Part B: 12 recruiters × 2 sessions over the following two weeks, only if its gates are met. Replication of Part A with a freshly written made-up set before any version moves past the gate.

### Real-world transfer

Any high-volume requisition where a recruiter faces more applications than they can read. What the test can tell recruiters, applicants, the DPO and the board: whether a similarity ranking treats equal applications equally across the fields that may stand for protected groups; whether the audit that says so can catch a fault when one is there; what excluding proxy fields would cost; whether a recruiter working from the ranking still uses their own judgement; and whether a rejected applicant could be told why. It does not tell anyone that the assistant is safe to use. Only the board can open the gate, on the two checks d1 names.

### Traceability

Every shot and every fault maps to the AI Canvas and to record ids in `index.html`.

| Item | Beat | Canvas blocks | Record ids |
|---|---|---|---|
| Shot 0 (open card) | — | Business Value | `hiring` (stage Idea, disposition Blocked); d1 |
| Shot 1.1 | The situation | Business Problem | `hiring` (BU People / HR); IMPACTS.hiring scope; SA1 |
| Shot 1.2 | The situation | Business Problem | `hiring` |
| Shot 2.1 | The AI at work | Objective Function; Data Strategy; Modeling Approach | md-embed v1.4; ds-cvs; as-emb |
| Shot 2.2 | The AI at work | Modeling Approach | A.9; SA3 |
| Shot 2.3 | The AI at work | Customer Value; Business Value | `hiring` (value Not started) |
| Shot 3.1 | What can go wrong | Objective Function | r4; IMPACTS.hiring entry 1; F1; SA2 |
| Shot 3.2 | What can go wrong | Objective Function; Modeling Approach | r4; IMPACTS.hiring entry 1; F1; H2 |
| Shot 3.3 | What can go wrong | Customer Value; Business Problem | IMPACTS.hiring entry 2; A.8; F2; SA4; SA5; O8 |
| Shot 4.1 | How it is kept safe | Business Value | d1; bm-q2; BOARD_SEATS; r1; r4 |
| Shot 4.2 | How it is kept safe | — | e5; A.5; r1; r4 |
| Shot 4.3 | How it is kept safe | Model Training | r4; A.6 |
| Shot C (close card) | — | Model Training; Business Value | d1; w3-o1; e5 |
| F1 proxy for a protected group | What can go wrong | Objective Function; Data Strategy | r4; IMPACTS.hiring entry 1; A.6 |
| F2 no reason for the outcome | What can go wrong | Customer Value | IMPACTS.hiring entry 2; A.8 |
| F3 special-category data in the input | (protocol only) | Data Strategy | ds-cvs; A.7; gdpr |
| F4 shared index without isolation | (protocol only) | Modeling Approach | n8 (on `chatbot`); md-embed system card |
| G1, G2 | How it is kept safe | Model Training; Business Value | d1; r1; r4; e5; A.5; A.6; w3-o1 |
| O1-O12 | How it is kept safe (record) | Modeling Approach; Data Strategy; Customer Value; Model Training | sup-tr; SOURCING.hiring; md-embed card; A.7; A.8; CHANGE.hiring; bm-jul; bm-jul-x; ds-cvs → as-emb; n8; r1; r4; e5; BOARD_SEATS |

### Open questions for review

1. **Closed: e5 is the FRIA in draft.** The record now says so (e5's title and content; r1: "No signed-off fundamental-rights impact assessment"; `IMPACTS.hiring` scope; the copilot's blocked answer). The film now says "rights review" in both shot 4.1 and shot 4.2.
2. **The proxy-field list and the thresholds** (SA2; H1's 2-point margins; the 0.8 impact ratio) are the auditor's and the FRIA's to set. The values here are placeholders.
3. **A reason path and a human look at every rejection.** The record has no condition on transparency beyond impact entry 2 and A.8 not started. Should the gate also require a pass level on `reason_available`, and a design in which no applicant is rejected on rank alone (O8)? That would be a board decision, so this script does not add it.
4. **Issue #4's canvas table** still lists five blocks as empty. It now differs from the prototype (all seven are filled).
5. **Who signs the FRIA?** The AI Impact Assessment Owner and the DPO are the same person (O11). The record does not say who would sign e5 if the board wants the DPO to advise on it rather than own it.
6. **Provider duties (O9) and a DPIA (O10)** are not in d1's two conditions. Whether the board adds them to the gate is its decision; the film states only d1's two conditions.
