/* ---- Why AI Center X: the standalone landing page (#/why), the default route ----
   Figures and footnotes come from sourced.md; nothing on this page is illustrative data. */
function whyNote(n){ return '<sup><a href="#/why#src-'+n+'" aria-label="Source '+n+'">'+n+'</a></sup>'; }
function whyVenn(){
  function circle(c,href,cx,cy,label,lx,ly,name){
    return '<a href="'+href+'" data-c="'+c+'" aria-label="'+name+'">'+
      '<circle cx="'+cx+'" cy="'+cy+'" r="140" />'+
      '<text class="lbl" x="'+lx+'" y="'+ly+'">'+label+'</text></a>';
  }
  return '<figure class="why-venn">'+
    '<svg viewBox="0 0 500 432" role="group" aria-label="Three overlapping circles, innovation, governance and change, meeting at AI Center X, the AI management system">'+
      circle("val","#/why#why-innovation",160,140,"Innovation",107,130,"Innovation: what happens without governance")+
      circle("gov","#/why#why-governance",340,140,"Governance",398,130,"Governance: what happens without innovation")+
      circle("arch","#/why#why-change",250,288,"Change",250,392,"Change: what happens when it is left out")+
      '<g class="pill" aria-hidden="true"><rect x="155" y="152" width="190" height="72" rx="36" />'+
        '<text class="t1" x="250" y="187">AI Center X</text><text class="t2" x="250" y="210">AIMS</text></g>'+
    '</svg>'+
    '<figcaption>Select a circle to see what happens when it works alone.</figcaption></figure>';
}
function pageWhy(){
  var themeLabel=document.documentElement.getAttribute("data-theme")==="boardroom"?"Midnight":"Boardroom";
  return ''+
  '<div class="why-bar" aria-hidden="true"><span></span><span></span><span></span></div>'+
  '<header class="why-wrap why-top">'+
    '<a class="why-brand" href="#/why">AI Center X</a>'+
    '<div class="why-top-r">'+
      '<button class="btn-ghost" type="button" data-theme-toggle data-theme-label>'+themeLabel+'</button>'+
      '<a class="btn-primary" href="#/home">Open the prototype</a>'+
    '</div>'+
  '</header>'+
  '<main class="why-landing-main" id="why-main">'+
    '<section class="why-wrap why-hero" aria-labelledby="why-h1">'+
      '<div>'+
        '<p class="why-stat"><b>56% of CEOs</b> report no significant financial benefit from AI yet.'+whyNote(1)+'</p>'+
        '<h1 id="why-h1">Innovation, governance and change: better together</h1>'+
        '<p class="why-lede">In many organisations, AI innovation, AI governance and the change that makes AI stick are three separate efforts, with three teams and three backlogs. '+
          'Pilots stall at the risk review, controls arrive after launch, and new tools meet unchanged ways of working. '+
          '<strong>AI Center X brings the three into one AI management system</strong>, so every initiative carries its case, its risks and its change plan in one record, from idea to production.</p>'+
        '<div class="why-ctas"><a class="btn-primary" href="#/home">Open the prototype</a>'+
          '<a class="btn-ghost" href="#/ontology">See how the records connect</a></div>'+
      '</div>'+
      whyVenn()+
    '</section>'+

    '<section class="why-wrap why-sec" aria-labelledby="why-gap">'+
      '<h2 id="why-gap">The returns go to the organisations that join them up</h2>'+
      '<p class="why-intro">Most organisations are still waiting for AI to pay off. The ones that see returns have done more than buy technology.</p>'+
      '<div class="why-figs">'+
        '<div class="why-fig" data-c="val"><p class="n">75%</p>'+
          '<p class="d">of AI high performers have <b>fundamentally redesigned workflows</b>, against about 25% of other organisations.'+whyNote(2)+'</p></div>'+
        '<div class="why-fig" data-c="gov"><p class="n">3×</p>'+
          '<p class="d">CEOs with strong AI foundations are <b>three times as likely</b> to report meaningful financial returns. The foundations are responsible AI and risk processes, a clear AI roadmap, enabling technology and an enabling culture.'+whyNote(1)+'</p></div>'+
        '<div class="why-fig" data-c="arch"><p class="n">70%</p>'+
          '<p class="d">of the work in an AI transformation is <b>people and processes</b>. Technology is 20% and algorithms 10%.'+whyNote(3)+'</p></div>'+
      '</div>'+
    '</section>'+

    '<section class="why-wrap why-sec" aria-labelledby="why-stall">'+
      '<h2 id="why-stall">On its own, each circle stalls</h2>'+
      '<p class="why-intro">Each effort is necessary, and none of them is enough. Here is what happens when one runs without the other two, and where the prototype covers it.</p>'+
      '<div class="why-alone">'+
        '<article class="why-lens" id="why-innovation" data-c="val" tabindex="-1">'+
          '<h3>Innovation without governance</h3>'+
          '<p>Pilots move fast, then stop at the first risk review, because nobody recorded the data, the model or the impact along the way. Promising use cases never reach production.</p>'+
          '<p class="why-in">In the prototype: <a href="#/portfolio">Portfolio</a>, <a href="#/register/canvas">AI Canvases</a>, <a href="#/lifecycle">Lifecycle</a>, <a href="#/architecture">Architecture</a></p>'+
        '</article>'+
        '<article class="why-lens" id="why-governance" data-c="gov" tabindex="-1">'+
          '<h3>Governance without innovation</h3>'+
          '<p>Policies and gates exist, but they meet initiatives late, as a checkpoint to pass rather than a route to production. The board decides without the evidence in front of it.</p>'+
          '<p class="why-in">In the prototype: <a href="#/register/risk">Risk</a>, <a href="#/register/impact">Impact assessments</a>, <a href="#/register/control">Controls</a>, <a href="#/register/evidence">Evidence</a>, <a href="#/boardroom">Board Room</a></p>'+
        '</article>'+
        '<article class="why-lens" id="why-change" data-c="arch" tabindex="-1">'+
          '<h3>Change left out</h3>'+
          '<p>The tool ships, but the work around it stays the same. With 70% of the effort in people and processes,'+whyNote(3)+' this is where most of the value is lost.</p>'+
          '<p class="why-in">In the prototype: <a href="#/register/change">Change management</a>, <a href="#/waves">Delivery waves</a>, <a href="#/people">People</a></p>'+
        '</article>'+
      '</div>'+
      '<div class="why-together">'+
        '<h3>Together: one AI management system</h3>'+
        '<div><p>AI Center X is an <strong>AI management system (AIMS)</strong>, the kind ISO/IEC 42001 describes. The use case, its risks and controls, the evidence behind them, the board’s decisions and the change programme are linked records of the same initiative, not documents in three places.</p>'+
          '<p>Open any initiative and you can follow it to who owns it, what it is exposed to, what treats that exposure, what proves the treatment works, and who has to change how they work.</p></div>'+
      '</div>'+
    '</section>'+

    '<section class="why-wrap why-sec why-close" aria-labelledby="why-go">'+
      '<div><h2 id="why-go">From AI idea to governed production</h2>'+
        '<p>The prototype walks one illustrative portfolio through the whole journey: initiatives from idea to run, the risks and controls they carry, and the board sessions that decide on them.</p></div>'+
      '<div class="why-ctas" style="margin-top:0"><a class="btn-primary" href="#/home">Open the prototype</a>'+
        '<a class="btn-ghost" href="#/copilot">Ask the copilot</a></div>'+
    '</section>'+

    '<section class="why-wrap why-sec why-sources" id="why-sources" aria-labelledby="why-src">'+
      '<h2 id="why-src">Sources</h2>'+
      '<ol>'+
        '<li id="src-1">PwC, <cite>29th Global CEO Survey</cite>, January 2026, a survey of 4,454 CEOs in 95 countries. Source of the 56% and 3× figures. '+
          '<a href="https://www.pwc.com/gx/en/news-room/press-releases/2026/pwc-2026-global-ceo-survey.html" target="_blank" rel="noopener noreferrer">Press release</a>.</li>'+
        '<li id="src-2">McKinsey, <cite>The State of AI</cite>, August 2026, 1,719 respondents in 97 countries. Source of the 75% figure. '+
          '<a href="https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai" target="_blank" rel="noopener noreferrer">The state of AI</a>.</li>'+
        '<li id="src-3">BCG, <cite>How Agents Are Accelerating the Next Wave of AI Value Creation</cite>, December 2025. Source of the 70% figure, from BCG’s 10-20-70 rule. '+
          '<a href="https://www.bcg.com/publications/2025/agents-accelerate-next-wave-of-ai-value-creation" target="_blank" rel="noopener noreferrer">BCG article</a>.</li>'+
      '</ol>'+
    '</section>'+
  '</main>'+
  '<footer class="why-wrap why-foot">A concept prototype. The figures on this page come from the sources above; the initiatives, people and records inside the prototype are illustrative.</footer>';
}

