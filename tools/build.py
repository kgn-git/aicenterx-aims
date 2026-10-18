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

# drop the "Made with Claude Design" badge from the original export
badge = re.search(r'<div id="__claude_design_branding">.*?</div>(?=</body>)', html, re.S)
if not badge:
    sys.exit("design badge not found")
html = html[:badge.start()] + html[badge.end():]

OUT.write_text(html, encoding="utf-8")
print("wrote", OUT, len(html))
