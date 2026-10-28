/* ---- Risk and harm suggestions on the initiative page: the agent replays the curated, cited RISK_SUGGESTIONS ----
   The selection lives in SUGG, keyed by initiative so one initiative's picks never feed another's mitigations, until
   reload. It never writes to RISKS: nothing enters the register until a person adds it. A suggestion that matches a
   register risk has no checkbox of its own, so the selection holds each risk once: a register risk by its register
   id, any other suggestion by its suggestion id. */
var SUGG=Object.create(null);
function suggOf(init){ return SUGG[init]||(SUGG[init]={selected:{},runs:{}}); }
var RISK_STEPS=["Read the AI Canvas","Search the MIT AI Risk Repository","Match AI incidents","Add AI Index context","Draft suggestions"];
var SOURCE_HOSTS={mit:"airisk.mit.edu",aiid:"incidentdatabase.ai",aiindex:"hai.stanford.edu",licence:"creativecommons.org"};
// The data test's url_ok rule, applied again at render: a fixed prefix rather than a parsed hostname, because parsers
// and browsers read userinfo, ports and backslashes differently.
function sourceUrlOk(url,host){
  var known=Object.keys(SOURCE_HOSTS).some(function(k){ return SOURCE_HOSTS[k]===host; }), head="https://"+host;
  return known&&typeof url==="string"&&url.indexOf(head)===0&&/^(?:[\/?#]\S*)?$/.test(url.slice(head.length));
}
function sourceLink(url,host,text){
  if(!sourceUrlOk(url,host)) return esc(text);
  return '<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">'+esc(text)+
    '<span aria-hidden="true"> ↗</span><span'+SR_ONLY+'> (opens in a new tab)</span></a>';
}
function blockLabel(f){ var b=CANVAS_BLOCKS.filter(function(x){return x.f===f;})[0]; return b?b.l:"AI Canvas"; }
function suggCount(init){ return Object.keys(suggOf(init).selected).length+" selected"; }
function suggLabel(init,id,label){
  return '<span id="sugg-label-'+esc(init)+'-'+esc(id)+'">'+esc(label)+'</span>';
}
function suggPick(init,id,label){
  return '<label style="display:flex;gap:9px;align-items:flex-start;font-weight:600;font-size:13.5px">'+
    '<input type="checkbox" data-pick-risk="'+esc(id)+'" data-pick-init="'+esc(init)+'"'+(suggOf(init).selected[id]?" checked":"")+
    ' style="margin-top:3px">'+suggLabel(init,id,label)+'</label>';
}
function openRisk(init,id,labelId){
  return '<button class="see-all" type="button" data-open="risk:'+esc(id)+'" aria-describedby="sugg-label-'+esc(init)+'-'+esc(labelId)+'"'+
    ' style="margin-top:8px">Open the risk<span aria-hidden="true"> →</span></button>';
}
function suggItem(init,x){
  return '<li class="surface pad" data-sugg="'+esc(x.id)+'" style="margin:0 0 10px">'+
    (x.matchesRisk?'<div style="font-weight:600;font-size:13.5px">'+suggLabel(init,x.id,x.description)+'</div>':suggPick(init,x.id,x.description))+
    '<div class="m-badges">'+(x.matchesRisk?'<span class="pill" data-tone="green">Already in the register</span>':"")+
      '<span class="pill">'+esc(titleCase(x.harm))+'</span>'+
      '<span class="pill">Likelihood: '+esc(titleCase(x.likelihood))+'</span>'+
      '<span class="pill">Severity: '+esc(titleCase(x.severity))+'</span>'+
      '<span class="pill">'+esc(x.lifecycleStage)+'</span></div>'+
    '<p class="muted-note" style="margin:9px 0 0">Raised by the '+esc(blockLabel(x.trigger))+' block. MIT AI Risk Repository: '+
      sourceLink(x.mit.url,SOURCE_HOSTS.mit,x.mit.domain)+', '+esc(x.mit.subdomain)+'.</p>'+
    '<p class="muted-note" style="margin:6px 0 0">AI incidents: '+x.incidents.map(function(n){
      return sourceLink(n.url,SOURCE_HOSTS.aiid,n.title); }).join("; ")+'</p>'+
    (x.matchesRisk?openRisk(init,x.matchesRisk,x.id):"")+
  '</li>';
}
function riskSuggestResult(init){
  var d=RISK_SUGGESTIONS.initiatives[init], ctx=d.context;
  var mine=RISKS.filter(function(r){return r.init===init;});
  var sub='display:block;font-size:13px;margin:14px 0 8px';
  return '<div class="surface pad" style="margin-top:12px">'+
    '<h3 class="sec-title" id="sugg-risks-head-'+esc(init)+'" data-run-head tabindex="-1" style="margin-top:0">Suggested risks and harms</h3>'+
    '<p class="muted-note" style="margin:0 0 12px">These are suggestions. They block nothing, and nothing enters the risk register until a person adds it.</p>'+
    '<blockquote data-sugg-context style="margin:0 0 14px;padding-left:12px;border-left:3px solid var(--hairline);font-size:13px">'+
      '<span class="muted-note">Context from the Stanford AI Index:</span><br>'+esc(ctx.statement)+
      '<br><span class="muted-note">'+sourceLink(ctx.url,SOURCE_HOSTS.aiindex,ctx.edition+", "+ctx.chapter)+'</span></blockquote>'+
    '<h4 id="sugg-list-'+esc(init)+'" style="'+sub+'">Suggested by the agent</h4>'+
    '<ul aria-labelledby="sugg-list-'+esc(init)+'" style="margin:0;padding:0;list-style:none">'+d.suggestions.map(function(x){ return suggItem(init,x); }).join("")+'</ul>'+
    '<h4 id="sugg-reg-'+esc(init)+'" style="'+sub+'">Risks already in the register</h4>'+
    '<ul aria-labelledby="sugg-reg-'+esc(init)+'" style="margin:0;padding:0;list-style:none">'+mine.map(function(r){
      return '<li class="surface pad" data-sugg="'+esc(r.id)+'" style="margin:0 0 10px">'+suggPick(init,r.id,r.description)+openRisk(init,r.id,r.id)+'</li>';
    }).join("")+'</ul>'+
    '<p style="margin:12px 0 2px;font-weight:600"><span data-sugg-count id="sugg-count-'+esc(init)+'" aria-live="polite">'+suggCount(init)+'</span></p>'+
    '<p class="muted-note" style="margin:0 0 14px">Your selection is kept until you reload the page. The next step suggests mitigations for it.</p>'+
    '<h4 style="'+sub+'">Sources and licences</h4>'+
    '<ul data-attribution class="muted-note" style="margin:0;padding-left:18px;font-size:12px">'+RISK_SUGGESTIONS.attribution.map(function(a){
      return '<li>'+sourceLink(a.url,SOURCE_HOSTS[a.key],a.source)+', '+sourceLink(a.licenceUrl,SOURCE_HOSTS.licence,a.licence)+'. Changes: '+esc(a.changes)+'</li>';
    }).join("")+'</ul></div>';
}
function riskSuggestEmpty(init){
  return '<div class="surface" data-sugg-empty style="margin-top:12px"><div class="empty">'+
    '<p tabindex="-1" style="margin:0">The agent has no curated suggestions for this initiative yet, so it has nothing to draft here. You can log a risk yourself.</p>'+
    '<button class="btn-primary" type="button" data-form="risk" data-ctx="initiative:'+esc(init)+'" style="margin-top:10px">Log a risk</button></div></div>';
}
function riskSuggestSection(init){
  var ran=suggOf(init).runs.risks;
  return '<div class="mmd-toolbar">'+
    '<button class="btn-ghost" type="button" id="sugg-risks-btn-'+esc(init)+'" data-suggest-risks="'+esc(init)+'">'+(ran?"Run again":"Suggest risks and harms")+'</button>'+
    '<span class="block-hint">An agent drafts the risks and harms this AI Canvas implies, each cited to a public source. It blocks nothing.</span></div>'+
    '<div id="sugg-risks-'+esc(init)+'">'+(ran?riskSuggestResult(init):"")+'</div>';
}
function suggestRisks(init){
  var host=document.getElementById("sugg-risks-"+init);
  if(!host) return;
  if(!Object.prototype.hasOwnProperty.call(RISK_SUGGESTIONS.initiatives,init)){
    host.innerHTML=riskSuggestEmpty(init);
    host.querySelector("[tabindex]").focus();
    return;
  }
  agentRun("sugg-risks-"+init,RISK_STEPS,function(){
    suggOf(init).runs.risks=true;
    var btn=document.getElementById("sugg-risks-btn-"+init);
    if(btn) btn.textContent="Run again";
    return riskSuggestResult(init);
  });
}
document.addEventListener("click",function(e){
  var el=e.target.closest&&e.target.closest("[data-suggest-risks]");
  if(el) suggestRisks(el.getAttribute("data-suggest-risks"));
});
document.addEventListener("change",function(e){
  var el=e.target.closest&&e.target.closest("[data-pick-risk]");
  if(!el) return;
  var init=el.getAttribute("data-pick-init"), sel=suggOf(init).selected, id=el.getAttribute("data-pick-risk");
  if(el.checked) sel[id]=true; else delete sel[id];
  var c=document.getElementById("sugg-count-"+init);
  if(c) c.textContent=suggCount(init);
});
