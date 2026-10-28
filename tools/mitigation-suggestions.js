/* ---- Mitigation suggestions for the risks selected in the risk result: the agent replays MITIGATION_SUGGESTIONS ----
   SUGG[init].runs.mitigations lists the risks the last run covered. The result shows those that are still selected,
   so unticking removes a risk's mitigations at once, and a risk ticked since then waits for the next run. Nothing here
   writes to RISKS or CONTROLS: no control or treatment changes until a person acts. */
SOURCE_HOSTS.eurlex="eur-lex.europa.eu";
var LICENCE_HOSTS={mit:SOURCE_HOSTS.licence,eurlex:SOURCE_HOSTS.eurlex};
var MITIGATION_STEPS=["Read the selected risks","Check the register's treatments","Match the controls","Search mitigation sources","Draft mitigations"];
function controlOf(key){ return CONTROLS.filter(function(c){return c.key===key;})[0]; }
function anySourceLink(url,title){
  var host=["mit","aiid","eurlex"].map(function(k){return SOURCE_HOSTS[k];}).filter(function(h){return sourceUrlOk(url,h);})[0];
  return host?sourceLink(url,host,title):esc(title);
}
function recordLink(id){
  var d=DECISIONS.filter(function(x){return x.id===id;})[0], e=EVIDENCE.filter(function(x){return x.id===id;})[0];
  if(d) return '<button class="see-all" type="button" data-open="decision:'+esc(id)+'">Decision: '+esc(d.summary)+'</button>';
  return e?'<button class="see-all" type="button" data-open="evidence:'+esc(id)+'">Evidence: '+esc(e.title)+'</button>':"";
}
function controlGap(c){
  if(!c||c.closure==="implemented") return "";
  return '<div data-gap style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:8px">'+
    '<span class="pill" data-tone="amber">Gap</span><span class="muted-note">Control '+esc(c.key)+' is '+esc(titleCase(c.closure).toLowerCase())+'. Control owner:</span>'+
    (PEOPLE[c.owner]?personChip(PEOPLE[c.owner]):esc(c.owner))+'</div>';
}
function controlButton(c){
  return '<button class="see-all" type="button" data-open="control:'+esc(c.key)+'">'+esc(c.key)+' '+esc(c.objective)+'</button>'+
    ' <span class="pill" data-tone="'+(c.closure==="implemented"?"green":"amber")+'">'+esc(titleCase(c.closure))+'</span>';
}
function inRegister(r){
  var c=controlOf(r.controlKey), t=r.treatment;
  return '<div class="surface pad" data-in-register style="margin:0 0 8px">'+
    '<div class="m-badges" style="margin-top:0"><span class="pill">In the register</span>'+
      (t?'<span class="pill">'+esc(titleCase(t.strategy))+'</span>':'')+'</div>'+
    (t?'<p class="muted-note" style="margin:8px 0 0">Treatment owner:</p>'+(PEOPLE[t.owner]?personChip(PEOPLE[t.owner]):esc(t.owner))
      :'<div data-gap style="margin-top:8px"><span class="pill" data-tone="red">Gap</span> <span class="muted-note">No treatment recorded.</span></div>')+
    (t&&c?'<div style="margin-top:8px">'+controlButton(c)+'</div>'+controlGap(c):'')+
    '<button class="see-all" type="button" data-open="risk:'+esc(r.id)+'" style="margin-top:8px">Open the risk<span aria-hidden="true"> →</span></button></div>';
}
function mitigationItem(m){
  var c=controlOf(m.controlKey);
  return '<div class="surface pad" data-mitig="'+esc(m.id)+'" style="margin:0 0 8px">'+
    '<b style="display:block;font-size:13.5px">'+esc(m.description)+'</b>'+
    '<div class="m-badges"><span class="pill">'+esc(titleCase(m.strategy))+'</span><span class="pill">'+esc(m.lifecycleStage)+'</span></div>'+
    (c?'<div style="margin-top:8px">'+controlButton(c)+'</div>':'')+
    '<p class="muted-note" style="margin:8px 0 0">Why this control: '+esc(m.why)+'</p>'+
    '<p class="muted-note" style="margin:6px 0 0">MIT AI Risk Mitigation Taxonomy (draft): '+anySourceLink("https://airisk.mit.edu/ai-risk-mitigations",m.mit)+'</p>'+
    '<div class="muted-note" style="margin:6px 0 0">Sources: '+m.sources.map(function(s){
      return s.record?recordLink(s.record):anySourceLink(s.url,s.title); }).join("; ")+'</div>'+
    controlGap(c)+'</div>';
}
function riskLabel(init,rid){
  var r=RISKS.filter(function(x){return x.id===rid;})[0];
  if(r) return r.description;
  var s=RISK_SUGGESTIONS.initiatives[init].suggestions.filter(function(x){return x.id===rid;})[0];
  return s?s.description:rid;
}
function mitigationNone(init){
  return '<div class="surface" data-mitig-none style="margin-top:12px"><div class="empty">'+
    '<p tabindex="-1" style="margin:0">Select risks above to get mitigations. This blocks nothing.</p>'+
    '<button class="btn-ghost" type="button" data-mitig-goto="'+esc(init)+'" style="margin-top:10px">Go to the risk suggestions</button></div></div>';
}
function mitigationResult(init){
  var s=suggOf(init), covered=s.runs.mitigations||[];
  var shown=covered.filter(function(r){ return s.selected[r]; });
  var fresh=Object.keys(s.selected).filter(function(r){ return covered.indexOf(r)<0&&Object.prototype.hasOwnProperty.call(MITIGATION_SUGGESTIONS.risks,r); });
  if(!shown.length&&!fresh.length) return mitigationNone(init);
  return '<div class="surface pad" style="margin-top:12px">'+
    '<h3 class="sec-title" id="sugg-mitig-head-'+esc(init)+'" data-run-head tabindex="-1" style="margin-top:0">Suggested mitigations</h3>'+
    '<p class="muted-note" style="margin:0 0 12px">These are suggestions. They block nothing, and no control or treatment changes until a person acts.</p>'+
    shown.map(function(rid){
      var r=RISKS.filter(function(x){return x.id===rid;})[0];
      return '<section data-mitig-risk="'+esc(rid)+'" style="margin:0 0 14px"><h4 style="font-size:13px;margin:0 0 8px">'+esc(riskLabel(init,rid))+'</h4>'+
        (r?inRegister(r):'')+MITIGATION_SUGGESTIONS.risks[rid].map(mitigationItem).join("")+'</section>';
    }).join("")+
    (fresh.length?'<p class="muted-note" data-mitig-fresh>Suggest mitigations again to add them for '+fresh.length+' new risk'+(fresh.length===1?'':'s')+'.</p>':'')+
    '<h4 style="font-size:13px;margin:14px 0 8px">Sources and licences</h4>'+
    '<ul data-attribution class="muted-note" style="margin:0;padding-left:18px;font-size:12px">'+MITIGATION_SUGGESTIONS.attribution.map(function(a){
      return '<li>'+sourceLink(a.url,SOURCE_HOSTS[a.key],a.source)+', '+sourceLink(a.licenceUrl,LICENCE_HOSTS[a.key],a.licence)+'. Changes: '+esc(a.changes)+'</li>';
    }).join("")+'</ul></div>';
}
function mitigationSection(init){
  var ran=suggOf(init).runs.mitigations;
  return '<div class="mmd-toolbar" style="margin-top:14px">'+
    '<button class="btn-ghost" type="button" id="sugg-mitig-btn-'+esc(init)+'" data-suggest-mitigations="'+esc(init)+'">'+(ran?"Suggest mitigations again":"Suggest mitigations")+'</button>'+
    '<span class="block-hint">An agent suggests treatments for the risks you selected, mapped to the controls you already run. It blocks nothing.</span></div>'+
    '<div id="sugg-mitig-'+esc(init)+'">'+(ran?mitigationResult(init):"")+'</div>';
}
function suggestMitigations(init){
  var host=document.getElementById("sugg-mitig-"+init), s=suggOf(init);
  if(!host) return;
  var picked=Object.keys(s.selected).filter(function(r){ return Object.prototype.hasOwnProperty.call(MITIGATION_SUGGESTIONS.risks,r); });
  if(!picked.length){
    host.innerHTML=mitigationNone(init);
    host.querySelector("[tabindex]").focus();
    return;
  }
  agentRun("sugg-mitig-"+init,MITIGATION_STEPS,function(){
    s.runs.mitigations=picked;
    var btn=document.getElementById("sugg-mitig-btn-"+init);
    if(btn) btn.textContent="Suggest mitigations again";
    return mitigationResult(init);
  });
}
document.addEventListener("click",function(e){
  var el=e.target.closest&&e.target.closest("[data-suggest-mitigations],[data-mitig-goto]");
  if(!el) return;
  if(el.hasAttribute("data-mitig-goto")){
    var box=document.querySelector("#sugg-risks-"+el.getAttribute("data-mitig-goto")+" [data-pick-risk]");
    if(box) box.focus();
    return;
  }
  suggestMitigations(el.getAttribute("data-suggest-mitigations"));
});
document.addEventListener("change",function(e){
  var el=e.target.closest&&e.target.closest("[data-pick-risk]");
  if(!el) return;
  var init=el.getAttribute("data-pick-init"), host=document.getElementById("sugg-mitig-"+init);
  if(host&&suggOf(init).runs.mitigations&&!host.hasAttribute("data-run-busy")) host.innerHTML=mitigationResult(init);
});
