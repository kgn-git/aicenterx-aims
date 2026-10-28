/* ---- Mitigation suggestions for the risks selected in the risk result: the agent replays MITIGATION_SUGGESTIONS ----
   SUGG[init].runs.mitigations lists the risks the last run covered. The result shows those that are still selected,
   so unticking removes a risk's mitigations at once, and a risk ticked since then waits for the next run. Nothing here
   writes to RISKS or CONTROLS: no control or treatment changes until a person acts. */
var LICENCE_HOSTS={mit:SOURCE_HOSTS.licence,eurlex:SOURCE_HOSTS.eurlex};
var MITIGATION_SOURCE_KEYS=["mit","aiid","eurlex"];
var MITIGATION_STEPS=["Read the selected risks","Check the register's treatments","Match the controls","Search mitigation sources","Draft mitigations"];
function controlOf(key){ return CONTROLS.filter(function(c){return c.key===key;})[0]; }
function hasMitigations(rid){ return Object.prototype.hasOwnProperty.call(MITIGATION_SUGGESTIONS.risks,rid); }
function recordLink(id){
  var d=DECISIONS.filter(function(x){return x.id===id;})[0], e=EVIDENCE.filter(function(x){return x.id===id;})[0];
  var style=' style="text-align:left"';
  if(d) return '<button class="see-all" type="button" data-open="decision:'+esc(id)+'"'+style+'>Decision: '+esc(d.summary)+'</button>';
  return e?'<button class="see-all" type="button" data-open="evidence:'+esc(id)+'"'+style+'>Evidence: '+esc(e.title)+'</button>':esc(id);
}
function gapRow(c,what){
  if(!c||c.closure==="implemented") return "";
  return '<div data-gap style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:8px">'+
    '<span class="pill" data-tone="amber">Gap<span'+SR_ONLY+'>:</span></span><span class="muted-note">Control '+esc(c.key)+' is '+
    esc(titleCase(c.closure).toLowerCase())+', so this '+what+' has no working control yet. Control owner:</span>'+
    (PEOPLE[c.owner]?personChip(PEOPLE[c.owner]):esc(c.owner))+'</div>';
}
function controlButton(c){
  return '<button class="see-all" type="button" data-open="control:'+esc(c.key)+'" style="text-align:left">'+esc(c.key)+' '+esc(c.objective)+'</button>'+
    ' <span class="pill" data-tone="'+(c.closure==="implemented"?"green":"amber")+'">'+esc(titleCase(c.closure))+'</span>';
}
function inRegister(init,r){
  var c=controlOf(r.controlKey), t=r.treatment;
  return '<div class="surface pad" data-in-register style="margin:0 0 8px;border-left:3px solid var(--hairline)">'+
    '<div class="m-badges" style="margin-top:0"><span class="pill">'+(t?'Treatment in the register: '+esc(titleCase(t.strategy)):'No treatment in the register')+'</span></div>'+
    (t?'<p class="muted-note" style="margin:8px 0 0">Treatment owner:</p>'+(PEOPLE[t.owner]?personChip(PEOPLE[t.owner]):esc(t.owner))
      :'<div data-gap style="margin-top:8px"><span class="pill" data-tone="red">Gap<span'+SR_ONLY+'>:</span></span> <span class="muted-note">No treatment recorded.</span></div>')+
    (c?'<div style="margin-top:8px">'+controlButton(c)+'</div>':'')+(t?gapRow(c,"treatment"):'')+
    '<button class="see-all" type="button" data-open="risk:'+esc(r.id)+'" aria-describedby="sugg-mitig-risk-'+esc(init)+'-'+esc(r.id)+'"'+
      ' style="margin-top:8px">Open the risk<span aria-hidden="true"> →</span></button></div>';
}
function mitigationItem(m){
  var c=controlOf(m.controlKey);
  return '<div class="surface pad" data-mitig="'+esc(m.id)+'" style="margin:0 0 8px">'+
    '<b style="display:block;font-size:13px">'+esc(m.description)+'</b>'+
    '<div class="m-badges"><span class="pill">'+esc(titleCase(m.strategy))+'</span><span class="pill">'+esc(m.lifecycleStage)+'</span></div>'+
    (c?'<div style="margin-top:8px">'+controlButton(c)+'</div>':'')+
    '<p class="muted-note" style="margin:8px 0 0">Why this control: '+esc(m.why)+'</p>'+
    '<p class="muted-note" style="margin:6px 0 0">MIT AI Risk Mitigation Taxonomy (draft): '+anySourceLink("https://airisk.mit.edu/ai-risk-mitigations",m.mit,MITIGATION_SOURCE_KEYS)+'</p>'+
    '<p class="muted-note" style="margin:6px 0 2px">Sources:</p><ul class="muted-note" style="margin:0;padding-left:18px">'+m.sources.map(function(s){
      return '<li>'+(s.record?recordLink(s.record):anySourceLink(s.url,s.title,MITIGATION_SOURCE_KEYS))+'</li>'; }).join("")+'</ul>'+
    gapRow(c,"mitigation")+'</div>';
}
function riskLabel(init,rid){
  var r=RISKS.filter(function(x){return x.id===rid;})[0];
  if(r) return r.description;
  var s=RISK_SUGGESTIONS.initiatives[init].suggestions.filter(function(x){return x.id===rid;})[0];
  return s?s.description:rid;
}
function mitigationNone(init){
  return '<div class="surface" data-mitig-none data-run-state="none" style="margin-top:12px"><div class="empty">'+
    '<p tabindex="-1" data-run-head style="margin:0">You have not selected any risks yet. Select risks in the risk suggestions to get mitigations. This blocks nothing.</p>'+
    '<button class="btn-ghost" type="button" data-mitig-goto="'+esc(init)+'" style="margin-top:10px">Go to the risk suggestions</button></div></div>';
}
function mitigationState(init){
  var s=suggOf(init), covered=s.runs.mitigations||[];
  return {shown:covered.filter(function(r){ return s.selected[r]; }),
          fresh:Object.keys(s.selected).filter(function(r){ return covered.indexOf(r)<0&&hasMitigations(r); })};
}
function freshNote(init){
  var n=mitigationState(init).fresh.length;
  if(!suggOf(init).runs.mitigations||!n) return "";
  return 'You selected '+n+' risk'+(n===1?'':'s')+' after the last run. Suggest mitigations again to add '+(n===1?'its':'their')+' mitigations.';
}
function mitigationResult(init){
  var st=mitigationState(init);
  if(!st.shown.length&&!st.fresh.length) return mitigationNone(init);
  return '<div class="surface pad" data-run-state="'+esc((suggOf(init).runs.mitigations||[]).join(" "))+'" style="margin-top:12px">'+
    '<h4 class="sec-title" id="sugg-mitig-head-'+esc(init)+'" data-run-head tabindex="-1" style="margin-top:0">Suggested mitigations</h4>'+
    '<p class="muted-note" style="margin:0 0 12px">These are suggestions. They block nothing, and no control or treatment changes until a person acts.</p>'+
    (st.shown.length?'':'<p class="muted-note" data-mitig-empty>No mitigations to show for your current selection yet. Suggest mitigations again to get them.</p>')+
    st.shown.map(function(rid){
      var r=RISKS.filter(function(x){return x.id===rid;})[0];
      return '<section data-mitig-risk="'+esc(rid)+'" style="margin:0 0 14px">'+
        '<h5 id="sugg-mitig-risk-'+esc(init)+'-'+esc(rid)+'" style="font-size:14.5px;margin:0 0 8px">'+esc(riskLabel(init,rid))+'</h5>'+
        (r?inRegister(init,r):'')+'<p class="muted-note" style="margin:0 0 6px">Suggested by the agent:</p>'+
        MITIGATION_SUGGESTIONS.risks[rid].map(mitigationItem).join("")+'</section>';
    }).join("")+
    '<h5 style="font-size:13px;margin:14px 0 8px">Sources and licences for mitigations</h5>'+
    '<ul data-attribution class="muted-note" style="margin:0;padding-left:18px;font-size:12px">'+MITIGATION_SUGGESTIONS.attribution.map(function(a){
      return '<li>'+sourceLink(a.url,SOURCE_HOSTS[a.key],a.source)+', '+sourceLink(a.licenceUrl,LICENCE_HOSTS[a.key],a.licence)+'. Changes: '+esc(a.changes)+'</li>';
    }).join("")+'</ul></div>';
}
function mitigationSection(init){
  var ran=suggOf(init).runs.mitigations;
  return '<h3 class="sec-title" style="margin:18px 0 0">Mitigations</h3>'+
    '<div class="mmd-toolbar" style="margin-top:8px">'+
    '<button class="btn-ghost" type="button" id="sugg-mitig-btn-'+esc(init)+'" data-suggest-mitigations="'+esc(init)+'">'+(ran?"Suggest mitigations again":"Suggest mitigations")+'</button>'+
    '<span class="block-hint">An agent suggests mitigations for the risks you selected, mapped to the controls you already run. It blocks nothing.</span></div>'+
    '<p class="muted-note" data-mitig-fresh id="sugg-mitig-fresh-'+esc(init)+'" aria-live="polite" style="margin:6px 0 0">'+freshNote(init)+'</p>'+
    '<div id="sugg-mitig-'+esc(init)+'">'+(ran?mitigationResult(init):"")+'</div>';
}
RISK_RESULT_PARTS.push(mitigationSection);
function suggestMitigations(init){
  var host=document.getElementById("sugg-mitig-"+init), s=suggOf(init);
  if(!host||host.hasAttribute("data-run-busy")) return;
  var picked=Object.keys(s.selected).filter(hasMitigations);
  if(!picked.length){
    host.innerHTML=mitigationNone(init);
    host.querySelector("[data-run-head]").focus();
    return;
  }
  agentRun("sugg-mitig-"+init,MITIGATION_STEPS,function(){
    s.runs.mitigations=picked;
    var btn=document.getElementById("sugg-mitig-btn-"+init), note=document.getElementById("sugg-mitig-fresh-"+init);
    if(btn) btn.textContent="Suggest mitigations again";
    if(note) note.textContent=freshNote(init);
    return mitigationResult(init);
  });
}
SELECTION_HOOKS.push(function(init){
  var host=document.getElementById("sugg-mitig-"+init), note=document.getElementById("sugg-mitig-fresh-"+init), text=freshNote(init);
  if(note&&note.textContent!==text) note.textContent=text;
  if(!host||host.hasAttribute("data-run-busy")) return;
  if(suggOf(init).runs.mitigations) host.innerHTML=mitigationResult(init);
  else if(host.querySelector("[data-mitig-none]")&&Object.keys(suggOf(init).selected).length) host.innerHTML="";
});
document.addEventListener("click",function(e){
  var el=e.target.closest&&e.target.closest("[data-suggest-mitigations],[data-mitig-goto]");
  if(!el) return;
  if(el.hasAttribute("data-mitig-goto")){
    var list=document.getElementById("sugg-risks-"+el.getAttribute("data-mitig-goto")), box=list&&list.querySelector("[data-pick-risk]");
    if(box) box.focus();
    return;
  }
  suggestMitigations(el.getAttribute("data-suggest-mitigations"));
});
