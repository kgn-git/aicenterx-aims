"""Rebuild index.html from the original prototype (backup/) plus the landing page in why.css and why.js.

Usage: python tools/build.py   then   python tools/verify.py   (needs: pip install playwright)
"""
import json, re, sys
from pathlib import Path

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
    '''    answer:"Five initiatives have an AI Canvas and **all five are complete** — retail credit, fraud triage, the service copilot, CV screening and demand forecasting. **Churn propensity, document intelligence and dynamic pricing** have none started, so they are named, not defined. A complete canvas does not clear the gate: the **CV screening assistant** is fully defined and still held.",
    cites:[["canvas","fraud"],["canvas","hiring"],["initiative","hiring"]],
    follow:["Why is CV screening held at the gate?","Which initiatives have no canvas at all?"] },''')

# Integration (issue #1): each initiative with a standalone film links to it right after its AI Canvas.
# Hrefs are relative to index.html with spaces URL-encoded, opened in a new tab like "AI benchmarks".
sub('''function pageInitiative(id){''',
    '''var FILMS={
  rcr:"simulation/credit-scoring/Retail%20Credit%20Risk%20Scoring.html",
  chatbot:"simulation/service-copilot/Customer%20Service%20Copilot.html",
  hiring:"simulation/cv-screening/CV%20Screening%20Assistant.html",
  fraud:"simulation/fraud-triage/Fraud%20Triage%20Model.html",
  forecast:"simulation/demand-forecasting/Demand%20Forecasting.html"};
function filmLink(id){
  var href=FILMS[id]; if(!href) return "";
  return '<div class="mmd-toolbar" data-film="'+esc(id)+'">'+
    '<a class="btn-ghost" href="'+esc(href)+'" target="_blank" rel="noopener">Watch the simulation'+
      '<span aria-label="opens in a new tab">\u2197</span></a>'+
    '<span class="block-hint">A short film of this canvas in use: the situation, the AI at work, what can go wrong and how it is kept safe.</span></div>';
}
function pageInitiative(id){''')
sub("""    '<div><h2 class="sec-title" id="s-canvas">AI Canvas</h2>'+canvasSection(id)+'</div>'+""",
    """    '<div><h2 class="sec-title" id="s-canvas">AI Canvas</h2>'+canvasSection(id)+filmLink(id)+'</div>'+""")

# drop the "Made with Claude Design" badge from the original export
badge = re.search(r'<div id="__claude_design_branding">.*?</div>(?=</body>)', html, re.S)
if not badge:
    sys.exit("design badge not found")
html = html[:badge.start()] + html[badge.end():]

OUT.write_text(html, encoding="utf-8")
print("wrote", OUT, len(html))
