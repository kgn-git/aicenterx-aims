/* ---- agentRun: the simulated agent's visible run, reused by every suggester on the initiative page ----
   It owns the run and its ending: the steps, the busy guard, the skip control, reduced motion, and painting the
   result. onDone records the caller's state and returns the result's HTML; its first [data-run-head], with
   tabindex="-1", takes focus, and anything but a string paints nothing. The result's first [data-run-state] names the
   state it was drawn from. Navigation can rebuild the page mid-run, so the result goes to whichever element now has
   hostId, unless that element, or anything inside it, is running a newer run, or it already shows a result drawn from
   the same state. Focus moves to the result only if it was on the skip control or nowhere. */
// The whole run, including one beat on the finished list, fits inside the 2.5 s it is allowed for any step count.
var AGENT_RUN_MS=2160;
function agentStep(li,state){
  li.setAttribute("data-state",state);
  li.firstChild.textContent=state==="done"?"✓":state==="active"?"…":"○";
  li.lastChild.textContent=state==="done"?" (done)":state==="active"?" (in progress)":" (to do)";
}
// A state stamp, not the markup: a rebuilt page the user has since ticked or focused differs in markup, not in state.
function runStateOf(html){ var t=document.createElement("template"); t.innerHTML=html; var s=t.content.querySelector("[data-run-state]"); return s&&s.getAttribute("data-run-state"); }
function showsState(el,state){ var s=el.querySelector("[data-run-state]"); return state!==null&&!!s&&s.getAttribute("data-run-state")===state; }
function agentRun(hostId,steps,onDone){
  var host=document.getElementById(hostId);
  if(!host||host.hasAttribute("data-run-busy")) return false;
  host.setAttribute("data-run-busy","");
  host.innerHTML='<div class="surface pad" style="margin-top:12px">'+
    '<p role="status"'+SR_ONLY+'></p>'+
    '<ol style="margin:0 0 10px;padding:0;list-style:none;font-size:13px">'+steps.map(function(s){
      return '<li data-step data-state="pending" style="margin:3px 0"><span aria-hidden="true" style="display:inline-block;width:18px">○</span>'+
        esc(s)+'<span'+SR_ONLY+'> (to do)</span></li>';
    }).join("")+'</ol>'+
    '<button class="btn-ghost" type="button" data-run-skip>Show all now</button></div>';
  var items=host.querySelectorAll("[data-step]"), status=host.querySelector("[role=status]"), next=0, timer=null, ended=false;
  function announce(){ if(!ended) status.textContent="Step "+(next+1)+" of "+items.length+": "+steps[next]; }
  function activate(){ agentStep(items[next],"active"); announce(); }
  function finish(){
    if(ended) return;
    ended=true; clearInterval(timer);
    for(;next<items.length;next++) agentStep(items[next],"done");
    var active=document.activeElement, mine=active===skip||!active||active===document.body;
    skip.remove();
    host.removeAttribute("data-run-busy");
    var html=onDone(), now=document.getElementById(hostId);
    if(typeof html!=="string"||!now||now.hasAttribute("data-run-busy")) return;
    if(now!==host&&(now.querySelector("[data-run-busy]")||showsState(now,runStateOf(html)))) return;
    now.innerHTML=html;
    var head=now.querySelector("[data-run-head]");
    if(now===host&&mine&&head) head.focus();
  }
  var skip=host.querySelector("[data-run-skip]");
  skip.addEventListener("click",finish);
  skip.focus();
  if(!items.length||(window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches)){ finish(); return true; }
  // A live region filled in the task that creates it is often not announced, so the first step waits a beat.
  agentStep(items[0],"active");
  setTimeout(announce,100);
  timer=setInterval(function(){
    if(!host.isConnected||next===items.length) return finish();
    agentStep(items[next++],"done");
    if(next<items.length) activate();
  },AGENT_RUN_MS/(items.length+1));
  return true;
}
