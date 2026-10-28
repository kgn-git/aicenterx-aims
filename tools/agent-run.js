/* ---- agentRun: the simulated agent's visible run, shared by the risk, mitigation and model suggesters ----
   It owns only the run: the steps, the busy guard, the skip control and reduced motion. The result, and where it
   goes, belong to onDone, which looks its host up again because navigation can replace the page mid-run. */
// Five steps plus one beat on the finished list stay inside the 2.5 s the run is allowed.
var AGENT_STEP_MS=360;
function agentStep(li,state){
  li.setAttribute("data-state",state);
  li.firstChild.textContent=state==="done"?"✓":state==="active"?"…":"○";
}
function agentRun(host,steps,onDone){
  if(host.hasAttribute("data-run-busy")) return false;
  host.setAttribute("data-run-busy","");
  host.innerHTML='<div class="surface pad" style="margin-top:12px">'+
    '<ol aria-live="polite" style="margin:0 0 10px;padding:0;list-style:none;font-size:13px">'+steps.map(function(s,i){
      return '<li data-step="'+i+'" data-state="pending" style="margin:3px 0"><span aria-hidden="true" style="display:inline-block;width:18px">○</span>'+esc(s)+'</li>';
    }).join("")+'</ol>'+
    '<button class="btn-ghost" type="button" data-run-skip>Show all now</button></div>';
  var items=host.querySelectorAll("[data-step]"), next=0, timer=null, ended=false;
  function finish(){
    if(ended) return;
    ended=true; clearInterval(timer);
    for(;next<items.length;next++) agentStep(items[next],"done");
    host.removeAttribute("data-run-busy");
    onDone();
  }
  var skip=host.querySelector("[data-run-skip]");
  skip.addEventListener("click",finish);
  skip.focus();
  if(window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches){ finish(); return true; }
  agentStep(items[0],"active");
  timer=setInterval(function(){
    if(!host.isConnected||next===items.length) return finish();
    agentStep(items[next++],"done");
    if(next<items.length) agentStep(items[next],"active");
  },AGENT_STEP_MS);
  return true;
}
