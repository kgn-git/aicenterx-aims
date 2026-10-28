"""Rebuild index.html from the original prototype (backup/) plus the landing page in why.css and why.js.

Usage: python tools/build.py   then   python tools/verify.py   (needs: pip install playwright)
"""
import json, re, sys
from pathlib import Path

from inline_json import script_literal

SCRATCH = Path(__file__).resolve().parent
ROOT = SCRATCH.parent
SRC = ROOT / "backup" / "AI Center X prototype.html"
OUT = ROOT / "index.html"

bundle = SRC.read_text(encoding="utf-8")
m = re.search(r'<script type="__bundler/template">(.*?)</script>', bundle, re.S)
html = json.loads(m.group(1))
manifest = json.loads(re.search(r'<script type="__bundler/manifest">(.*?)</script>', bundle, re.S).group(1))
assert manifest == {}, "bundle carries assets; unpacking to plain HTML would lose them"

def sub(old, new, count=1):
    global html
    n = html.count(old)
    if n != count:
        sys.exit(f"expected {count} of {old[:70]!r}, found {n}")
    html = html.replace(old, new)

# The canvas agent's scripts, injected in this order: the shared run first, then each suggester that calls it.
AGENT_JS = ("agent-run.js", "risk-suggestions.js")

def data_js(name):
    return script_literal(json.loads((SCRATCH / "data" / f"{name}.json").read_text(encoding="utf-8")))

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..700'
         '&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap">\n')

# head: title, fonts, landing styles
sub("<title>AI Center X — Ontology prototype v4 (P1.2)</title>",
    "<title>AI Center X — prototype v5 with homepage</title>\n" + FONTS)
sub("</head>", (SCRATCH / "why.css").read_text(encoding="utf-8") + "</head>")

# body: landing container, brand links home
sub('<a class="skip-link" href="#main">Skip to content</a>',
    '<a class="skip-link" id="skip-link" href="#main">Skip to content</a>\n<div class="landing" id="landing" hidden></div>')
sub('<span class="hdr-brand-mark">AI Center X</span>',
    '<a class="hdr-brand-mark" href="#/why" style="text-decoration:none">AI Center X</a>')

# script: page, nav entry, default route, landing mode, theme sync
sub("function pageHome(){", (SCRATCH / "why.js").read_text(encoding="utf-8") + "function pageHome(){")
sub('{label:"Overview",accent:"gov",items:[\n    {label:"Home",route:"#/home"},',
    '{label:"Overview",accent:"gov",items:[\n    {label:"Why AI Center X",route:"#/why"},\n    {label:"Home",route:"#/home"},')
# Technology: the benchmarks table is a standalone page next to index.html, opened in a new tab
sub('''    {label:"Data sources",route:"#/register/datasource",count:function(){return DATASOURCES.length;}}]},''',
    '''    {label:"Data sources",route:"#/register/datasource",count:function(){return DATASOURCES.length;}},
    {label:"AI benchmarks",href:"Periodic%20Table%20of%20AI%20Benchmarks.html"}]},''')
sub('''        var attr = it.form ? 'data-form="'+esc(it.form)+'"' : 'data-nav="'+esc(it.route)+'"';
        return '<li><a class="nav-link" '+attr+' role="button" tabindex="0">'+esc(it.label)+
          (c!=null?'<span class="nav-count">'+c+'</span>':"")+'</a></li>'; }).join("")''',
    '''        if(it.href) return '<li><a class="nav-link" href="'+esc(it.href)+'" target="_blank" rel="noopener">'+esc(it.label)+
          '<span class="nav-count" aria-label="opens in a new tab">\\u2197</span></a></li>';
        var attr = it.form ? 'data-form="'+esc(it.form)+'"' : 'data-nav="'+esc(it.route)+'"';
        return '<li><a class="nav-link" '+attr+' role="button" tabindex="0">'+esc(it.label)+
          (c!=null?'<span class="nav-count">'+c+'</span>':"")+'</a></li>'; }).join("")''')
sub('''  var raw=(location.hash||"#/home").replace(/^#\\//,"");
  var bits=raw.split("#"), path=bits[0], section=bits[1];
  var parts=path.split("/");''',
    '''  var raw=(location.hash||"#/why").replace(/^#\\//,"");
  var bits=raw.split("#"), path=bits[0], section=bits[1];
  var parts=path.split("/");
  // The landing page stands outside the shell: no header, sidebar or crumbs.
  var landing=document.getElementById("landing"), isWhy=parts[0]==="why";
  document.body.classList.toggle("is-landing",isWhy);
  landing.hidden=!isWhy;
  document.getElementById("skip-link").setAttribute("href",isWhy?"#/why#why-main":"#main");
  if(isWhy){
    landing.innerHTML=pageWhy();
    markActive();
    var tw=section&&document.getElementById(section);
    if(tw){ tw.classList.add("is-lit"); if(tw.scrollIntoView) tw.scrollIntoView({behavior:"smooth",block:"start"}); if(tw.focus) tw.focus({preventScroll:true}); }
    else { try{ window.scrollTo(0,0); }catch(_){} }
    return;
  }
  landing.innerHTML="";''')
sub('''  themeBtn.textContent=dark?"Midnight":"Boardroom";
});''',
    '''  themeBtn.textContent=dark?"Midnight":"Boardroom";
  document.querySelectorAll("[data-theme-label]").forEach(function(b){ b.textContent=dark?"Midnight":"Boardroom"; });
});''')
sub('''document.addEventListener("click",function(e){
  var el;
  if((el=e.target.closest("[data-mmd-edit]''',
    '''document.addEventListener("click",function(e){
  var el;
  if((el=e.target.closest("[data-theme-toggle]"))){ themeBtn.click(); return; }
  if((el=e.target.closest("[data-mmd-edit]''')

# data: complete the AI Canvas for fraud triage (none in the export), CV screening and demand
# forecasting, each block derived from that initiative's own records (summary, risks, incidents,
# decisions, evidence, impacts, model and system card, data sources, supplier). Open issues stay
# open in the wording: hiring is still held at the gate, forecast residency is still unresolved.
sub('''  chatbot:{init:"chatbot",businessProblem:''',
    '''  fraud:{init:"fraud",businessProblem:"Analysts cannot look at every card payment as it happens, so fraud is found only after the money has gone.",
    businessValue:"Fraud stopped at the point of payment, with analyst time spent only on the borderline alerts that need judgement.",
    objectiveFunction:"Probability that a card transaction is fraudulent, predicted from transaction, channel and account-history features.",
    modelingApproach:"Gradient-boosted trees scoring each payment in real time inside a 150 ms budget; a tuned threshold ranks borderline scores into the human review queue.",
    modelTraining:"Every reviewer block-or-release decision returns as a label; thresholds are re-tuned quarterly, and the calibration window does not yet capture seasonal traffic shifts.",
    customerValue:"Fewer fraudulent charges reach the statement, and no payment is blocked on the model's word alone: a person reviews every block.",
    dataStrategy:"Card transaction stream and core banking account history into the shared customer feature store, labelled with 24 months of confirmed fraud outcomes."},
  chatbot:{init:"chatbot",businessProblem:''')
sub('''    businessValue:"",objectiveFunction:"",modelingApproach:"",modelTraining:"",
    customerValue:"",dataStrategy:"Application text and structured CV fields; special-category data is in scope and unresolved."},''',
    '''    businessValue:"Recruiter time moves from first-pass reading to a reviewable shortlist; no value is claimed while the use case is held at the gate.",
    objectiveFunction:"Match between an application and the requisition, scored from CV text and structured CV fields; which fields must be excluded as protected-group proxies is undecided.",
    modelingApproach:"Similarity ranking on the shared document embedding model, co-built with TalentRank Partners; it ranks for a recruiter and never decides on its own.",
    modelTraining:"Nothing is trained while the gate holds; as proposed, recruiter shortlist decisions are the feedback, and an independent bias audit must clear each version first.",
    customerValue:"As proposed, every application is considered rather than missed, but a rejected candidate cannot yet be given the reason for the outcome.",
    dataStrategy:"Application text and structured CV fields; special-category data is in scope and unresolved."},''')
sub('''    businessValue:"Lower carrying cost and fewer stock-outs against the same working capital.",
    objectiveFunction:"",modelingApproach:"",modelTraining:"",customerValue:"",dataStrategy:""}''',
    '''    businessValue:"Lower carrying cost and fewer stock-outs against the same working capital.",
    objectiveFunction:"Regional demand for each planning cycle, predicted from ERP demand history; any further features the vendor ensemble uses are not visible to us.",
    modelingApproach:"Bought as SaaS: ForecastCloud AI's time-series ensemble behind a connector, evaluated as a black box because its weights cannot be inspected.",
    modelTraining:"Retraining happens on the vendor's side and is not visible to us; a planner reviews every forecast before it enters the cycle, and actual demand is the only check we hold.",
    customerValue:"Stock sits in the region where customers buy it, and a planner, not the vendor, answers for every move.",
    dataStrategy:"ERP demand history leaves through the ForecastCloud connector; no personal data, but the residency clause is unresolved, which holds the pilot."}''')
# the copilot's canned canvas answer described the incomplete canvases; restate it from the data
sub('''    answer:"Four initiatives have an AI Canvas started and **two are complete** — retail credit scoring and the service copilot. The **CV screening assistant** has only its business problem answered, which is part of why it is held: an initiative with an incomplete canvas has been named, not defined.",
    cites:[["canvas","rcr"],["canvas","hiring"],["initiative","hiring"]],
    follow:["What is missing from the CV screening canvas?","Which initiatives have no canvas at all?"] },''',
    '''    answer:"**All eight initiatives have a complete AI Canvas**, so every one is defined, not merely named. Completeness does not mean the same maturity: **churn propensity** describes a model in production, **document intelligence** a vendor stack still in review, and **dynamic pricing** a proposal with nothing built and its open questions written down. A complete canvas does not clear the gate either: the **CV screening assistant** is fully defined and still held.",
    cites:[["canvas","pricing"],["canvas","docai"],["canvas","hiring"],["initiative","hiring"]],
    follow:["Why is CV screening held at the gate?","What is high risk, and why?"] },''')

# Record consistency (critique round). Each fix keeps the existing ids and edits as little text as it can.
# 1. Retail credit runs ONE operating model (GDPR Art. 22, EU AI Act high-risk): the model scores in session,
#    clear approvals issue automatically, every decline or borderline score is confirmed by an underwriter with
#    reason codes before the applicant is told, and a contested decline returns to an underwriter. n4 stays the
#    gap: the reasons never reached the servicing channel.
sub('''summary:"Applicant contested an automated decline with no explanation available"''',
    '''summary:"Applicant contested an underwriter-confirmed decline with no explanation available"''')
sub('''scope:"Automated credit decisioning for retail applicants, with a human override path."''',
    '''scope:"Retail credit decisioning: clear approvals are issued automatically; every decline or borderline score is confirmed by an underwriter, with reason codes, before the applicant is told; a contested decline returns to an underwriter."''')
sub('''    intendedUse:"Score retail credit applications to support, never replace, an underwriter decision.",''',
    '''    intendedUse:"Score retail credit applications in session: clear approvals are issued automatically, and every decline or borderline score goes to an underwriter, who decides.",''')
sub('''    oversight:"Every decline above the threshold is reviewable by an underwriter, with reason codes."},''',
    '''    oversight:"An underwriter confirms every decline and borderline score, with reason codes, before the applicant is told; a contested decline returns to an underwriter."},''')
sub(r'''  CAL --> DEC{{Underwriter review}}\n  DEC -->|decision| CORE[Core banking decision]\n''',
    r'''  CAL -->|clear approval| AUTO[Automatic approval]\n  CAL -->|decline or borderline| DEC{{Underwriter review}}\n  AUTO --> CORE[Core banking decision]\n  DEC -->|confirmed + reason codes| CORE\n''')
sub('''    customerValue:"A same-session answer with reason codes the servicing channel can actually read back.",''',
    '''    customerValue:"A same-session answer; a decline is confirmed by an underwriter and carries reason codes the servicing channel can actually read back.",''')
# 2. The fair-lending test that flagged the cohort (e1) is filed before the board acted on it (d2, bm-q2, 12 June).
sub('''title:"Fair-lending disparity test, Q2",owner:"maria",controlKey:"A.5",capturedAt:"2026-06-18",dueAt:"2026-09-18",''',
    '''title:"Fair-lending disparity test, Q2",owner:"maria",controlKey:"A.5",capturedAt:"2026-06-05",dueAt:"2026-09-05",''')
# 3. The copilot's July security incidents (n5, n8) came after the pilot-scope sign-off (d5). The impact owner
#    re-opens the assessment at an out-of-cycle session (d6); the Q3 board, which could not have been held on
#    10 July with n8 raised on 11 July, moves to 24 July with its agenda unchanged.
sub('''summary:"Impact assessment signed off for the pilot scope only; re-assessment required before scale."}''',
    '''summary:"Impact assessment signed off for the pilot scope only; re-assessment required before scale."},
  {id:"d6",kind:"aiia-trigger",subject:"aiia",init:"chatbot",by:"tomas",at:"2026-07-14",meeting:"bm-jul-x",summary:"The prompt-injection and cross-unit retrieval incidents trigger a re-assessment of the pilot impact assessment; the pilot stays in the supervised cohort and no agents join until it is signed off again."}''')
sub('''  {id:"bm-jul",title:"Q3 governance board",date:"2026-07-10",status:"scheduled",chair:"alicia",''',
    '''  {id:"bm-jul-x",title:"Out-of-cycle board session",date:"2026-07-14",status:"held",chair:"alicia",
   present:["board-chair","aims-manager","ai-risk-owner","impact-assessment-owner","internal-audit-owner","data-privacy-owner"],
   reviewed:["chatbot"],minute:"Copilot security incidents reviewed. Pilot impact assessment re-opened; the pilot stays in the supervised cohort until it is re-assessed.",clause:"Cl.6.1.4 / Cl.8.4 AI impact assessment"},
  {id:"bm-jul",title:"Q3 governance board",date:"2026-07-24",status:"scheduled",chair:"alicia",''')
sub('''  chatbot:{init:"chatbot",status:"signed-off",scope:"Front-line service assistance in the supervised pilot cohort only.",
    entries:[{harm:"misinformation",affected:"individuals",likelihood:"possible",magnitude:"moderate",description:"A customer acts on an ungrounded answer given as fact."}]}''',
    '''  chatbot:{init:"chatbot",status:"in-progress",scope:"Front-line service assistance in the supervised pilot cohort only; signed off for the pilot, re-opened after the July security incidents.",
    entries:[{harm:"misinformation",affected:"individuals",likelihood:"possible",magnitude:"moderate",description:"A customer acts on an ungrounded answer given as fact."},
             {harm:"security",affected:"individuals",likelihood:"possible",magnitude:"major",description:"Text a customer pastes into a chat steers the assistant or exposes its instructions to the agent."},
             {harm:"privacy",affected:"groups",likelihood:"possible",magnitude:"moderate",description:"Document titles from other business units are shown to agents who have no need to see them."}]}''')
sub('''      [["signed off",1],["in progress",2],["harm categories",HARMS.length]]]; },''',
    '''      [["signed off",ONTOLOGY.impact.all().filter(function(m){return m.status==="signed-off";}).length],["in progress",ONTOLOGY.impact.all().filter(function(m){return m.status==="in-progress";}).length],["harm categories",HARMS.length]]]; },''')
sub('''    answer:"Three sessions have been held and one is scheduled for **10 July**. The **Q2 governance board** on 12 June is where three of the five decisions on the log were taken — it sat 7 of 8 seats, so it was quorate and properly constituted. The **AI Lifecycle / Technical Owner** seat is unfilled, which is a quorum-counting seat rather than a mandatory one.",
    cites:[["meeting","bm-q2"],["meeting","bm-jul"],["decision","d1"]],''',
    '''    answer:"Four sessions have been held and one is scheduled for **24 July**. The **Q2 governance board** on 12 June is where three of the six decisions on the log were taken — it sat 7 of 8 seats, so it was quorate and properly constituted. An **out-of-cycle session** on 14 July re-opened the service copilot's impact assessment after two security incidents. The **AI Lifecycle / Technical Owner** seat is unfilled, which is a quorum-counting seat rather than a mandatory one.",
    cites:[["meeting","bm-q2"],["meeting","bm-jul-x"],["decision","d6"],["meeting","bm-jul"]],''')
# 4. e5 IS the fundamental-rights impact assessment (FRIA) the board required in d1, in draft.
sub('''title:"CV screening impact assessment (draft)",owner:"tomas",controlKey:"A.5",capturedAt:"2026-06-28",dueAt:"2026-07-31",content:"Scope, affected groups and harm entries drafted; sign-off withheld pending the bias audit."}''',
    '''title:"CV screening fundamental-rights impact assessment (FRIA), draft",owner:"tomas",controlKey:"A.5",capturedAt:"2026-06-28",dueAt:"2026-07-31",content:"The FRIA the board required at the gate: scope, affected groups and harm entries drafted; sign-off withheld pending the independent bias audit."}''')
sub('''  hiring:{init:"hiring",status:"in-progress",scope:"Shortlisting support for external hiring across all requisitions in People / HR.",''',
    '''  hiring:{init:"hiring",status:"in-progress",scope:"Fundamental-rights impact assessment (FRIA) required by the board: shortlisting support for external hiring across all requisitions in People / HR.",''')
sub('''description:"No fundamental-rights impact assessment on a high-risk hiring use case",''',
    '''description:"No signed-off fundamental-rights impact assessment on a high-risk hiring use case",''')
sub('''   why:"EU AI Act Annex III high-risk employment use — deploying without a FRIA is a gate-blocking legal exposure."},''',
    '''   why:"EU AI Act Annex III high-risk employment use. The board made a signed-off FRIA a gate condition, so deploying without one breaches that decision and leaves the deployer's high-risk duties unevidenced."},''')
sub('''fundamental-rights exposure with no assessment on file, and retail''',
    '''fundamental-rights exposure whose assessment is still an unsigned draft, and retail''')
sub('''The draft assessment exists; sign-off is withheld pending the audit.",''',
    '''The fundamental-rights assessment is on file as a draft; sign-off is withheld pending the audit.",''')
# 5. Document intelligence: DocuParse residency is confirmed (supplier record); what holds the pilot is extraction quality.
sub('''summary:"OCR + extraction for back-office documents; assessing data residency before pilot."''',
    '''summary:"OCR + extraction for back-office documents; vendor data residency confirmed, extraction errors under review before pilot."''')
# 6. The last three AI Canvases, each block derived from that initiative's own records. Pricing has
#    nothing built, so its canvas is written as a proposal and its open questions stay open.
sub('''dataStrategy:"ERP demand history leaves through the ForecastCloud connector; no personal data, but the residency clause is unresolved, which holds the pilot."}''',
    '''dataStrategy:"ERP demand history leaves through the ForecastCloud connector; no personal data, but the residency clause is unresolved, which holds the pilot."},
  churn:{init:"churn",businessProblem:"Customers leave without warning, and retention offers go to everyone or to no one, so the budget lands on customers who would have stayed.",
    businessValue:"Retention spend goes to the customers most likely to leave, and the model has to pay for itself: lift over random targeting is the measure.",
    objectiveFunction:"Propensity that a customer leaves, predicted from behavioural features in the customer feature store, drawn from the CRM profile and web clickstream.",
    modelingApproach:"A logistic baseline built in-house on the shared customer feature store; it ranks customers for a campaign and never sets a price, credit or service level.",
    modelTraining:"Trained on 18 months of behaviour and reviewed quarterly against lift; the score leans on tenure, so new customers are under-ranked, and a campaign owner approves every audience before send.",
    customerValue:"Customers likely to leave hear from us before they go, and the score never changes the price, credit or service anyone receives.",
    dataStrategy:"CRM customer profile and web clickstream into the shared customer feature store, which also feeds credit and fraud; both sources are personal data, so this is profiling for marketing under GDPR."},
  docai:{init:"docai",businessProblem:"Back-office staff rekey fields from scanned documents by hand, which is slow and lets typing errors into the record.",
    businessValue:"Faster document intake with less rekeying, measured as the share of documents extracted without it; the value is modelled, not yet realised.",
    objectiveFunction:"Field-level extraction accuracy against the back-office record, measured on a 500-document sample; the vendor's own features are not visible to us.",
    modelingApproach:"Bought as SaaS: DocuParse's OCR and layout model behind the document ingest pipeline, evaluated as a black box; a vendor page-limit default once silently truncated multi-page contracts.",
    modelTraining:"The vendor trains its model, and we cannot see on what; a back-office checker confirms every extraction before it enters the record, and those corrections are our accuracy check.",
    customerValue:"Documents are processed sooner, and no extracted field reaches a record of decision until a person has checked it, so an error can still be challenged.",
    dataStrategy:"Scanned back-office documents from the scanning bureau into the document ingest pipeline and on to DocuParse, with residency confirmed; scans can name people, so GDPR applies."},
  pricing:{init:"pricing",businessProblem:"Proposed: prices are reviewed by hand and too rarely to follow demand. Which products and channels are in scope is not yet decided.",
    businessValue:"Proposed: margin from prices that follow demand. No value is modelled yet; intake and a first risk screen come first.",
    objectiveFunction:"Proposed: the margin earned at a price, predicted from demand signals; which signals, and whether any of them are personal, is open until intake.",
    modelingApproach:"Not chosen. Recorded as in-house by default until the first screen; whether the model sets prices or recommends them to a pricing owner is the first design question.",
    modelTraining:"Nothing is built or trained. As proposed, a pricing owner approves every price change and its outcome feeds back; the gate decides whether that holds.",
    customerValue:"Open question: a price that follows demand must stay explainable and must not differ by who the customer is; the risk screen has to test that before anything is built.",
    dataStrategy:"No data source is registered yet. Intake must name the demand data, where it comes from and whether it is personal, before the first risk screen."}''')
# 7. The canvas register band read "0 have no canvas started at all" in amber once every canvas was complete.
sub('''    return ["val","amber",complete+"/"+INITIATIVES.length,"<strong>initiatives are defined</strong>, not merely named — a complete AI Canvas answers all seven blocks. "+
      (INITIATIVES.length-ONTOLOGY.canvas.all().length)+" have no canvas started at all.",''',
    '''    var notStarted=INITIATIVES.length-ONTOLOGY.canvas.all().length;
    return ["val",complete===INITIATIVES.length?"green":"amber",complete+"/"+INITIATIVES.length,"<strong>initiatives are defined</strong>, not merely named — a complete AI Canvas answers all seven blocks. "+
      (notStarted?notStarted+" have no canvas started at all.":"Every initiative has its canvas; a complete one still does not clear the gate."),''')

# Integration (issue #1): each initiative with a standalone film links to it right after its AI Canvas.
# Hrefs are relative to index.html with spaces URL-encoded, opened in a new tab like "AI benchmarks".
sub('''function pageInitiative(id){''',
    '''var FILMS={
  rcr:"simulation/credit-scoring/Retail%20Credit%20Risk%20Scoring.html",
  chatbot:"simulation/service-copilot/Customer%20Service%20Copilot.html",
  hiring:"simulation/cv-screening/CV%20Screening%20Assistant.html",
  fraud:"simulation/fraud-triage/Fraud%20Triage%20Model.html",
  forecast:"simulation/demand-forecasting/Demand%20Forecasting.html",
  churn:"simulation/churn-propensity/Churn%20Propensity.html",
  docai:"simulation/document-intelligence/Document%20Intelligence.html",
  pricing:"simulation/dynamic-pricing/Dynamic%20Pricing.html"};
function filmLink(id){
  var href=FILMS[id]; if(!href) return "";
  return '<div class="mmd-toolbar" data-film="'+esc(id)+'">'+
    '<a class="btn-ghost" href="'+esc(href)+'" target="_blank" rel="noopener">Watch the simulation'+
      '<span aria-label="opens in a new tab">\u2197</span></a>'+
    '<span class="block-hint">A short film of this canvas in use: the situation, the AI at work, what can go wrong and how it is kept safe.</span></div>';
}
function filmButton(id){
  var href=FILMS[id]; if(!href) return '<span class="muted-note">—</span>';
  return '<a class="btn-ghost" data-film-link href="'+esc(href)+'" target="_blank" rel="noopener" style="white-space:nowrap">Watch'+
    '<span aria-label="the simulation, opens in a new tab"> ↗</span></a>';
}
function pageInitiative(id){''')
sub("""    '<div><h2 class="sec-title" id="s-canvas">AI Canvas</h2>'+canvasSection(id)+'</div>'+""",
    """    '<div><h2 class="sec-title" id="s-canvas">AI Canvas</h2>'+canvasSection(id)+filmLink(id)+riskSuggestSection(id)+'</div>'+""")
# The canvas agent replays curated, cited output; its data lives in tools/data so tests can read it as JSON.
sub("function pageInitiative(id){",
    "var RISK_SUGGESTIONS=" + data_js("risk_suggestions") + ";\n" +
    "".join((SCRATCH / f).read_text(encoding="utf-8") for f in AGENT_JS) +
    "function pageInitiative(id){")
# The AI Canvases register gets a "Simulation" column with the same film link.
sub('''        {h:"Business problem",f:function(c){return esc(c.businessProblem||"—");}}],''',
    '''        {h:"Business problem",f:function(c){return esc(c.businessProblem||"—");}},
        {h:"Simulation",f:function(c){return filmButton(c.init);}}],''')
# A film link inside a register row opens the film only; the row must not also open the canvas.
sub('''document.addEventListener("click",function(e){
  var el;
  if((el=e.target.closest("[data-theme-toggle]"))){''',
    '''document.addEventListener("click",function(e){
  var el;
  if(e.target.closest("[data-film-link]")) return;
  if((el=e.target.closest("[data-theme-toggle]"))){''')

# drop the "Made with Claude Design" badge from the original export
badge = re.search(r'<div id="__claude_design_branding">.*?</div>(?=</body>)', html, re.S)
if not badge:
    sys.exit("design badge not found")
html = html[:badge.start()] + html[badge.end():]

OUT.write_text(html, encoding="utf-8")
print("wrote", OUT, len(html))
