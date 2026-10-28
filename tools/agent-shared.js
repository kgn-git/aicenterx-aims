/* ---- What the suggesters on the initiative page share: the selection, and how they cite external sources ----
   SUGG[init] = {selected, runs} lives until reload, keyed by initiative so one initiative's picks never feed another's
   suggestions. Whoever changes the selection calls selectionChanged(init), and each suggester that reads it registers
   in SELECTION_HOOKS, so none depends on another's event listener or load order. Every host a citation may link to is
   declared once, in SOURCE_HOSTS. */
var SR_ONLY=' style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap"';
var SUGG=Object.create(null);
function suggOf(init){ return SUGG[init]||(SUGG[init]={selected:{},runs:{}}); }
var SELECTION_HOOKS=[];
function selectionChanged(init){ SELECTION_HOOKS.forEach(function(f){ f(init); }); }
var SOURCE_HOSTS={mit:"airisk.mit.edu",aiid:"incidentdatabase.ai",aiindex:"hai.stanford.edu",eurlex:"eur-lex.europa.eu",licence:"creativecommons.org"};
// The data tests' url_ok rule, applied again at render: a fixed prefix rather than a parsed hostname, because parsers
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
function anySourceLink(url,text){
  var host=Object.keys(SOURCE_HOSTS).map(function(k){ return SOURCE_HOSTS[k]; }).filter(function(h){ return sourceUrlOk(url,h); })[0];
  return host?sourceLink(url,host,text):esc(text);
}
