/* Dependency-free interaction layer. No credentials, network requests, or tracking. */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const root = document.documentElement;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const touch = window.matchMedia('(pointer: coarse)');
  const fmt = new Intl.DateTimeFormat('en-US', {year:'numeric', month:'short', day:'numeric', timeZone:'UTC'});
  const dayMs = 86400000;
  const parseDay = (s) => new Date(`${s}T00:00:00Z`);
  const iso = (d) => d.toISOString().slice(0,10);
  const original = window.PROFILE_DATA;
  let data, cells = [], selected = null, focusIndex = 0, paused = reduced.matches, demo = false;
  let hovered = null;
  try { const t = localStorage.getItem('sean-rhythm-theme'); if (t === 'dark' || t === 'light') root.dataset.theme=t; } catch {}
  function setThemeButton() { $('themeButton').setAttribute('aria-label',`Switch to ${root.dataset.theme==='dark'?'light':'dark'} theme`); }
  setThemeButton();
  $('themeButton').addEventListener('click', () => {root.dataset.theme=root.dataset.theme==='dark'?'light':'dark';setThemeButton();try{localStorage.setItem('sean-rhythm-theme',root.dataset.theme);}catch{}});
  function check(d) {
    if (!d || d.schemaVersion!==1 || !['ready','unavailable','demo'].includes(d.status) || !Array.isArray(d.days)) throw new Error('Invalid snapshot');
    const a=parseDay(d.period.from), b=parseDay(d.period.to), n=Math.round((b-a)/dayMs)+1;
    if (Number.isNaN(a.valueOf()) || Number.isNaN(b.valueOf()) || n<1 || n>366) throw new Error('Invalid date range');
    if (d.status==='unavailable') {if(d.days.length || d.totalContributions!==null)throw new Error('Unavailable data includes values');return d;}
    if(d.status==='ready' && (!d.fetchedAt || Number.isNaN(Date.parse(d.fetchedAt))))throw new Error('Invalid sync timestamp');
    if(d.days.length!==n)throw new Error('Incomplete date coverage');
    let sum=0;
    d.days.forEach((r,i)=>{if(r.date!==iso(new Date(+a+i*dayMs)) || !Number.isInteger(r.count) || r.count<0 || !Number.isInteger(r.level) || r.level<0 || r.level>4 || (r.count===0)!==(r.level===0))throw new Error('Invalid daily data');sum+=r.count;});
    if(sum!==d.totalContributions)throw new Error('Inconsistent total');
    return d;
  }
  function countText(row) {return `${row.count.toLocaleString('en-US')} ${row.count===1?'contribution':'contributions'}`;}
  function updateMotion() {
    $('dayGrid').classList.toggle('is-paused',paused || reduced.matches);
    $('motionButton').textContent=reduced.matches?'Reduced motion':paused?'Resume motion':'Pause motion';
    $('motionButton').disabled=reduced.matches;
    $('motionButton').setAttribute('aria-pressed',String(paused || reduced.matches));
    $('replayButton').disabled=reduced.matches || data?.status==='unavailable';
  }
  $('motionButton').addEventListener('click',()=>{paused=!paused;updateMotion();});
  reduced.addEventListener('change',()=>{paused=reduced.matches;updateMotion();});
  $('replayButton').addEventListener('click',()=>{paused=false;updateMotion();const g=$('dayGrid');g.classList.add('no-replay');g.querySelectorAll('.day-cell').forEach(c=>c.classList.remove('day-cell'));void g.offsetWidth;cells.forEach(c=>c.el.classList.add('day-cell'));g.classList.remove('no-replay');});
  function showDetail(row,pin=false) {
    $('detailDate').textContent=fmt.format(parseDay(row.date))+(pin?' · PINNED':'');
    $('detailCount').textContent=countText(row)+(demo?' · demo':'');
    $('clearButton').hidden=!selected;
  }
  function resetDetail() {
    if(selected){showDetail(selected,true);return;}
    $('detailDate').textContent=data.status==='unavailable'?'Awaiting the first snapshot.':'Every day has a story.';
    $('detailCount').textContent=data.status==='unavailable'?'No counts have been estimated.':'Choose a square to read it.';
    $('clearButton').hidden=true;
  }
  function hideTip() {$('tooltip').hidden=true;hovered=null;$('dayGrid').classList.remove('is-inspecting');cells.forEach(c=>c.el.removeAttribute('aria-describedby'));resetDetail();}
  function showTip(row,el) {
    hovered=row.date;$('tooltipDate').textContent=fmt.format(parseDay(row.date));$('tooltipCount').textContent=countText(row);$('tooltipMeta').textContent=demo?'DEMO DATA · NOT YOUR ACTIVITY':'GITHUB CONTRIBUTION CALENDAR';
    const tip=$('tooltip');tip.hidden=false;
    const r=el.getBoundingClientRect(),t=tip.getBoundingClientRect();
    tip.style.left=`${Math.max(12,Math.min(innerWidth-t.width-12,r.left+r.width/2-t.width/2))}px`;
    tip.style.top=`${r.top-t.height-12>=12?r.top-t.height-12:Math.min(innerHeight-t.height-12,r.bottom+12)}px`;
    el.setAttribute('aria-describedby','tooltip');$('dayGrid').classList.add('is-inspecting');
    if(!selected)showDetail(row);
  }
  function pin(row) {
    selected=row;
    cells.forEach(c=>{c.el.classList.toggle('is-selected',c.row.date===row.date);c.el.setAttribute('aria-pressed',String(c.row.date===row.date));});
    showDetail(row,true);
  }
  function clearSelection() {selected=null;cells.forEach(c=>{c.el.classList.remove('is-selected');c.el.setAttribute('aria-pressed','false');});hideTip();}
  $('clearButton').addEventListener('click',clearSelection);
  document.addEventListener('keydown',e=>{if(e.key==='Escape')clearSelection();});
  function focusAt(i) {
    focusIndex=Math.max(0,Math.min(cells.length-1,i));
    cells.forEach((c,j)=>c.el.tabIndex=j===focusIndex?0:-1);
    cells[focusIndex]?.el.focus({preventScroll:true});
    cells[focusIndex]?.el.scrollIntoView({block:'nearest',inline:'nearest',behavior:'instant'});
  }
  function keyNavigation(e,i) {
    const delta={ArrowLeft:-7,ArrowRight:7,ArrowUp:-1,ArrowDown:1};
    if(e.key in delta){e.preventDefault();focusAt(i+delta[e.key]);}
    if(e.key==='Home'){e.preventDefault();focusAt(0);}
    if(e.key==='End'){e.preventDefault();focusAt(cells.length-1);}
  }
  function render(d) {
    data=check(d);demo=data.status==='demo';selected=null;cells=[];hideTip();
    const missing=data.status==='unavailable',rows=data.days;
    $('dataBadge').textContent=demo?'DEMO DATA':missing?'AWAITING SYNC':'GITHUB SNAPSHOT';$('dataBadge').classList.toggle('demo',demo);
    $('period').textContent=`${fmt.format(parseDay(data.period.from))} — ${fmt.format(parseDay(data.period.to))}`;
    const notice=$('dataNotice');notice.hidden=!(demo||missing);
    notice.textContent=demo?'Interaction demo — these are generated sample values, not Sean’s actual contribution history.': 'Your contribution history is not loaded yet. The first successful update workflow will replace this state with real GitHub data.';
    $('demoButton').textContent=demo?'Return to real-data view ↩':'Try interaction demo ↗';
    $('totalValue').textContent=missing?'—':data.totalContributions.toLocaleString('en-US');$('activeValue').textContent=missing?'—':rows.filter(r=>r.count>0).length;
    $('totalLabel').textContent=demo?'demo contributions':'contributions';
    const stamp=data.fetchedAt?new Date(data.fetchedAt):null;
    let source=demo?'SYNTHETIC DEMO · not a GitHub data snapshot':missing?'GitHub contribution calendar · awaiting first sync':`GitHub calendar · synced ${stamp.toISOString().slice(0,16).replace('T',' ')} UTC · final day may be partial`;
    if(!demo && !missing && Date.now()-stamp.valueOf()>dayMs*3)source+=' · snapshot may be stale';
    $('sourceNote').textContent=source;
    $('methodNote').textContent=data.source?.note||'GitHub contribution calendar. This is not a productivity score.';
    $('interactionHint').textContent=missing?'Empty cells = unavailable, not zero':touch.matches?'Swipe to browse · tap a day to pin':'Hover to explore · click to pin';
    const a=parseDay(data.period.from), b=parseDay(data.period.to), dow=(a.getUTCDay()+6)%7;
    const monday=new Date(+a-dow*dayMs), weeks=Math.floor((b-monday)/dayMs/7)+1;
    const grid=$('dayGrid');grid.replaceChildren();$('monthLabels').replaceChildren();$('dayList').replaceChildren();
    grid.style.setProperty('--weeks',weeks);$('monthLabels').style.setProperty('--weeks',weeks);
    const positive=rows.filter(r=>r.count>0);const latest=positive.at(-1)?.date;
    const n=Math.round((b-a)/dayMs)+1;let month='',lastMonthCol=-5;
    for(let i=0;i<n;i++){
      const date=new Date(+a+i*dayMs), col=Math.floor((date-monday)/dayMs/7), r=(date.getUTCDay()+6)%7;
      const monthKey=`${date.getUTCFullYear()}-${date.getUTCMonth()}`;
      if(monthKey!==month){
        if(col-lastMonthCol>=2 && col<weeks-1){const label=document.createElement('span');label.textContent=new Intl.DateTimeFormat('en-US',{month:'short',timeZone:'UTC'}).format(date);label.style.gridColumn=`${col+1} / span 2`;$('monthLabels').append(label);lastMonthCol=col;}month=monthKey;
      }
      const el=document.createElement('button');el.type='button';el.className='day-cell';el.style.gridColumn=col+1;el.style.gridRow=r+1;el.style.setProperty('--col',col);el.dataset.date=iso(date);
      if(missing){el.disabled=true;el.classList.add('is-unknown');el.setAttribute('aria-label',`${fmt.format(date)}: data unavailable`);}
      else{
        const row=rows[i];el.dataset.level=row.level;el.tabIndex=-1;el.setAttribute('aria-label',`${fmt.format(date)}: ${countText(row)}${demo?' (demo data)':''}`);el.setAttribute('aria-pressed','false');
        if(row.date===latest)el.classList.add('is-latest');
        el.addEventListener('pointerenter',e=>{if(e.pointerType!=='touch')showTip(row,el);});el.addEventListener('pointerleave',hideTip);
        el.addEventListener('focus',()=>{focusIndex=i;showTip(row,el);});el.addEventListener('blur',hideTip);
        el.addEventListener('click',()=>{pin(row);showTip(row,el);});el.addEventListener('keydown',e=>keyNavigation(e,i));
        cells.push({row,el});
        const line=document.createElement('div'),dateLabel=document.createElement('span'),value=document.createElement('span');dateLabel.textContent=row.date;value.textContent=countText(row);line.append(dateLabel,value);$('dayList').append(line);
      }
      grid.append(el);
    }
    // A single tab stop; keyboard arrows navigate all 365 days without a tab trap.
    if(cells.length){focusIndex=cells.length-1;cells[focusIndex].el.tabIndex=0;}
    resetDetail();updateMotion();
    requestAnimationFrame(()=>{const wrap=$('calendarWrap');wrap.scrollLeft=Math.max(0,wrap.scrollWidth-wrap.clientWidth);document.body.dataset.ready='true';});
  }
  $('demoButton').addEventListener('click',()=>render(demo?original:window.PROFILE_DEMO));
  $('calendarWrap').addEventListener('scroll',hideTip,{passive:true});
  window.addEventListener('resize',hideTip,{passive:true});window.addEventListener('scroll',hideTip,{passive:true});
  try{render(original);}catch(e){$('dataNotice').hidden=false;$('dataNotice').textContent='The data file could not be validated. No contribution counts are shown. Regenerate the snapshot before publishing.';console.error(e);document.body.dataset.ready='error';}
})();
