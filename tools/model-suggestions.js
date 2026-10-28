/* ---- Suggested model approaches, a simulation: the agent replays the curated MODEL_SUGGESTIONS ----
   Nothing is computed or looked up. The candidates do not depend on the selection; only which of their raised and
   lowered risks are shown, and which controls need evidence, follow the selection and the mitigations shown. Nothing
   here changes the AI Canvas's modelling approach. */
var MODEL_STEPS=["Read the AI Canvas objective","Read the selected risks","Match benchmark dimensions","Check the controls behind the mitigations","Draft model candidates"];
var BENCH_PAGE="Periodic%20Table%20of%20AI%20Benchmarks.html";
var BENCH_DIMS={G:"General capability",S:"Security / safety",F:"Fairness / bias",X:"Sector specific",R:"Regulatory"};
// The link is built from a known dataset and a plain number only, the same rule the benchmarks page applies to its hash.
function benchLink(b){
  var label=b.name+" ("+b.dataset+" #"+b.no+", "+(BENCH_DIMS[b.dim]||b.dim)+")";
  if(!/^(s445|s100)$/.test(b.dataset)||!/^(0|[1-9]\d{0,2})$/.test(String(b.no))) return esc(label);
  return '<a href="'+BENCH_PAGE+'#'+b.dataset+'-'+b.no+'" target="_blank" rel="noopener noreferrer">'+esc(label)+
    '<span aria-hidden="true"> ↗</span><span'+SR_ONLY+'> (opens in a new tab)</span></a>';
}
function modelSource(s){
  if(s.prototype) return '<span class="muted-note">written for this prototype</span>';
  return s.record?recordLink(s.record):anySourceLink(s.url,s.title,["eurlex"]);
}
function criterion(c){ return esc(c.text)+' <span class="muted-note">Source:</span> '+modelSource(c.source); }
function riskNames(init,ids){
  var sel=suggOf(init).selected, shown=ids.filter(function(r){ return sel[r]; });
  return shown.length?shown.map(function(r){ return esc(riskLabel(init,r)); }).join("; "):'<span class="muted-note">none of your selected risks</span>';
}
function modelItem(init,c){
  return '<div class="surface pad" data-model="'+esc(c.id)+'" style="margin:0 0 8px">'+
    '<b style="display:block;font-size:13.5px">'+esc(c.name)+'</b>'+
    '<p class="muted-note" style="margin:6px 0 0">'+esc(c.fit)+'</p>'+
    '<p style="margin:8px 0 0;font-size:13px" data-model-raises>Raises: '+riskNames(init,c.raises)+'</p>'+
    '<p style="margin:4px 0 0;font-size:13px" data-model-lowers>Lowers: '+riskNames(init,c.lowers)+'</p>'+
    '<p class="muted-note" style="margin:8px 0 2px">Benchmarks:</p>'+(c.benchmarks.length?'<ul class="muted-note" style="margin:0;padding-left:18px">'+
      c.benchmarks.map(function(b){ return '<li>'+benchLink(b)+'</li>'; }).join("")+'</ul>':'<p class="muted-note" style="margin:0">None in the benchmarks table.</p>')+
    (c.criteria.length?'<p class="muted-note" style="margin:8px 0 2px">Criteria:</p><ul class="muted-note" style="margin:0;padding-left:18px">'+
      c.criteria.map(function(x){ return '<li>'+criterion(x)+'</li>'; }).join("")+'</ul>':'')+
    '<p class="muted-note" style="margin:8px 0 0">What the table lacks: '+esc(c.gaps)+'</p></div>';
}
function modelControls(init){
  var ctrl=MODEL_SUGGESTIONS.initiatives[init].controls, keys=[];
  mitigationState(init).shown.forEach(function(rid){ MITIGATION_SUGGESTIONS.risks[rid].forEach(function(m){ if(keys.indexOf(m.controlKey)<0) keys.push(m.controlKey); }); });
  if(!keys.length) return '<p class="muted-note" data-model-controls-none>Suggest mitigations for your selected risks to see which controls to evidence here.</p>';
  return '<ul style="margin:0;padding:0;list-style:none">'+keys.map(function(k){
    var ev=ctrl[k]||{}, c=controlOf(k);
    return '<li class="surface pad" data-model-control="'+esc(k)+'" style="margin:0 0 8px">'+(c?controlButton(c):esc(k))+
      '<p class="muted-note" style="margin:6px 0 0">'+(ev.benchmark?'Benchmark: '+benchLink(ev.benchmark):ev.criterion?'Criterion: '+criterion(ev.criterion):'')+'</p></li>';
  }).join("")+'</ul>';
}
function modelNone(init){
  return '<div class="surface" data-model-none data-run-state="none" style="margin-top:12px"><div class="empty">'+
    '<p tabindex="-1" data-run-head style="margin:0">You have not selected any risks yet. Select risks in the risk suggestions to get model suggestions. This blocks nothing.</p>'+
    '<button class="btn-ghost" type="button" data-model-goto="'+esc(init)+'" style="margin-top:10px">Go to the risk suggestions</button></div></div>';
}
function modelResult(init){
  return '<div class="surface pad" data-run-state="models" style="margin-top:12px">'+
    '<h4 class="sec-title" id="sugg-model-head-'+esc(init)+'" data-run-head tabindex="-1" style="margin-top:0">Suggested model approaches</h4>'+
    '<p class="muted-note" style="margin:0 0 12px">These are suggestions. They block nothing, and the AI Canvas\'s modelling approach is unchanged.</p>'+
    MODEL_SUGGESTIONS.initiatives[init].candidates.map(function(c){ return modelItem(init,c); }).join("")+
    '<h5 style="font-size:13px;margin:14px 0 8px">Evidence for the controls behind your mitigations</h5>'+modelControls(init)+'</div>';
}
function modelSection(init){
  if(!Object.prototype.hasOwnProperty.call(MODEL_SUGGESTIONS.initiatives,init)) return "";
  var ran=suggOf(init).runs.models;
  return '<h3 class="sec-title" style="margin:18px 0 0">Models</h3>'+
    '<div class="mmd-toolbar" style="margin-top:8px">'+
    '<button class="btn-ghost" type="button" id="sugg-model-btn-'+esc(init)+'" data-suggest-models="'+esc(init)+'">'+(ran?"Suggest models again":"Suggest models")+'</button>'+
    '<span class="block-hint">An agent suggests model approaches for this AI Canvas and your selected risks, with the benchmarks or criteria that would show they fit. It blocks nothing.</span></div>'+
    '<div id="sugg-model-'+esc(init)+'">'+(ran?modelResult(init):"")+'</div>';
}
RISK_RESULT_PARTS.push(modelSection);
function suggestModels(init){
  var host=document.getElementById("sugg-model-"+init);
  if(!host||host.hasAttribute("data-run-busy")) return;
  if(!Object.keys(suggOf(init).selected).length){
    host.innerHTML=modelNone(init);
    host.querySelector("[data-run-head]").focus();
    return;
  }
  agentRun("sugg-model-"+init,MODEL_STEPS,function(){
    suggOf(init).runs.models=true;
    var btn=document.getElementById("sugg-model-btn-"+init);
    if(btn) btn.textContent="Suggest models again";
    return modelResult(init);
  });
}
SELECTION_HOOKS.push(function(init){
  var host=document.getElementById("sugg-model-"+init);
  if(!host||host.hasAttribute("data-run-busy")) return;
  if(suggOf(init).runs.models) host.innerHTML=modelResult(init);
  else if(host.querySelector("[data-model-none]")&&Object.keys(suggOf(init).selected).length) host.innerHTML="";
});
document.addEventListener("click",function(e){
  var el=e.target.closest&&e.target.closest("[data-suggest-models],[data-model-goto]");
  if(!el) return;
  if(el.hasAttribute("data-model-goto")){
    var list=document.getElementById("sugg-risks-"+el.getAttribute("data-model-goto")), box=list&&list.querySelector("[data-pick-risk]");
    if(box) box.focus();
    return;
  }
  suggestModels(el.getAttribute("data-suggest-models"));
});
