'use strict';

const body = document.body;
const intro = document.querySelector('.fruit-intro');
const squeeze = document.getElementById('squeeze');
const skipPour = intro.querySelector('.skip-pour');
const room = document.getElementById('tree');
const canopy = room.querySelector('.canopy');
const fruits = [...canopy.querySelectorAll('.hanging-fruit')];
const reduced = matchMedia('(prefers-reduced-motion: reduce)');
let resumeVisit = false;

function syncLocation() {
  stopPress();
  const hash = location.hash.slice(1);
  const aliases = {writing:'made', work:'made', 'technical-projects':'made', notes:'made', roots:'about-me',
    hinduism:'about-me', reading:'found', music:'found', 'seventies-california':'found',
    'saanvi-mehra':'about-me', photographs:'credits', sound:'credits'};
  const oldId = hash.startsWith('pick-') ? hash.slice(5) : hash;
  const id = Object.hasOwn(aliases, oldId) ? aliases[oldId] : oldId;
  const target = document.getElementById(id);
  if (!target && id) {
    const entry = [...document.querySelectorAll('.entry-link')].find(link => link.dataset.slug === id);
    if (entry) { location.replace(entry.href); return; }
    const sheet = document.querySelector('.entry-link[data-slug="guthli"]');
    if (sheet && ['uppercase','lowercase','numbers','extended-latin','punctuation-and-symbols',
                  'combining-marks','spaces-and-controls','workshop'].includes(id)) {
      location.replace(sheet.href + '#' + id);
      return;
    }
  }
  if (target && hash !== id) history.replaceState(null, '', '#' + id);
  body.classList.add('garden-ready');
  const reading = Boolean(target && (target.id === 'main' || target.closest('.inside-garden,.footer')));
  body.classList.toggle('unfolded', reading);
  if (target?.matches('details.credits')) target.open = true;
  if (target && hash !== id) target.scrollIntoView({block:'start'});
}

function enter() {
  if (resumeVisit) history.replaceState(null, '', '#tree');
  else history.pushState(null, '', '#tree');
  resumeVisit = false;
  syncLocation();
  room.scrollIntoView({block:'start',behavior:'instant'});
  room.focus({preventScroll:true});
}

const journey = intro.querySelector('.fruit-journey');
const mouth = intro.querySelector('.carton-mouth');
const juice = intro.querySelector('.juice');
const j = juice.getContext('2d');
const spoken = document.getElementById('mango-line');
const firstClause = intro.querySelector('.mango-verse').textContent;
const lastClause = intro.querySelector('.carton-verse p').textContent;
const byline = intro.querySelector('.carton-verse cite').textContent;
let press, frame, drawing;

// The fixed pencil grain keeps the paper still while the pigment flows.
const pencilPaper = document.createElement('canvas');
pencilPaper.width = pencilPaper.height = 96;
const grain = pencilPaper.getContext('2d');
let pencilGrain;
if (grain && j) {
  let seed = 19;
  const random = () => ((seed = seed * 16807 % 2147483647) / 2147483647);
  for (let i = 0; i < 680; i++) {
    const x = random()*96, y = random()*96;
    grain.strokeStyle = i % 3 ? 'rgba(255,248,201,.59)' : 'rgba(188,107,26,.27)';
    grain.lineWidth = .45 + random()*.8;
    grain.beginPath(); grain.moveTo(x,y); grain.lineTo(x+random()*3,y-1-random()*2.5); grain.stroke();
  }
  pencilGrain = j.createPattern(pencilPaper,'repeat');
  pencilGrain?.setTransform(new DOMMatrix().scale(.48));
}
function measurePour() {
  const world = journey.getBoundingClientRect();
  const fruit = squeeze.getBoundingClientRect(), rim = mouth.getBoundingClientRect();
  const width = Math.ceil(fruit.width * .95);
  const left = fruit.left + fruit.width * .48 - width / 2;
  const top = fruit.top + fruit.height * .85;
  const rimY = rim.top + rim.height * .55;
  const height = Math.ceil(rimY - top + 10);
  const ratio = Math.min(devicePixelRatio || 1, 2);
  Object.assign(juice.style, {left:(left-world.left)+'px', top:(top-world.top)+'px', width:width+'px', height:height+'px'});
  juice.width = Math.ceil(width * ratio);
  juice.height = Math.ceil(height * ratio);
  drawing = {width, height, startX:width/2, endX:rim.left+rim.width/2-left,
    depth:rimY-top, lip:rim.width*.36, travel:intro.clientHeight, ratio};
}

function pencilStroke(path,colour,weight) {
  j.strokeStyle=colour; j.lineWidth=weight; j.stroke(path);
}
function wash(path,colour) {
  j.fillStyle=colour; j.fill(path);
  if(pencilGrain){j.fillStyle=pencilGrain;j.fill(path);}
}
function ripple(x,y,span,bow,colour,weight) {
  const line=new Path2D();
  line.moveTo(x,y); line.bezierCurveTo(x+span*.24,y+bow,x+span*.67,y+bow*.72,x+span,y-1);
  pencilStroke(line,colour,weight);
}

function paintFall(x,depth,front,width,time) {
  // A wide sheet at the peel draws down to a narrow thread at the open corner.
  const {endX, lip} = drawing;
  function at(u,across) {
    const taper = Math.pow(1-u,1.7);
    const radius = width*taper + lip*(1-taper);
    const edge = Math.sin(u*16-time*4.8+across*2) + .5*Math.sin(u*39-time*7.1);
    const bend = Math.sin(Math.PI*u)*(3.4*Math.sin(u*9-time*2.8)-5);
    return [x+(endX-x)*u+bend+across*(radius+1.1*edge*taper),depth*u];
  }
  const body=new Path2D();
  body.moveTo(...at(0,-1));
  for(let i=1;i<=24;i++) body.lineTo(...at(front*i/24,-1));
  const bottom=at(front,0);
  body.quadraticCurveTo(bottom[0]-width*.25,bottom[1]+3+(1-front)*9,...at(front,1));
  for(let i=23;i>=0;i--) body.lineTo(...at(front*i/24,1));
  body.closePath();
  const hue=j.createLinearGradient(x-width,0,x+width,0);
  for(const [stop,colour] of [[0,'#dd7c19'],[.15,'#fdab20'],[.34,'#ffcd3a'],[.51,'#ffdc58'],[.75,'#ffc031'],[.89,'#f7a328'],[1,'#db7419']]) hue.addColorStop(stop,colour);
  wash(body,hue);
  j.save(); j.clip(body);
  const pigments=['#fff0a0','#ffe17a','#e8881b','#f8a526','#ffeb8d','#d98829','#ffcf43'];
  for(let i=0;i<58;i++){
    const across=-.99+1.98*((i*37)%59)/58, moving=i%4!==0;
    const first=moving ? ((i*.317+time*(.71+(i%6)*.06))%1.57)-.55 : .008;
    const end=Math.min(front,first+(moving ? .14+(i%9)*.035 : .92));
    const start=Math.max(0,first);
    if(end<=start) continue;
    const pen=new Path2D();pen.moveTo(...at(start,across));
    for(let k=1;k<=9;k++){
      const u=start+(end-start)*k/9;
      pen.lineTo(...at(u,across+.017*Math.sin(10*u+i)));
    }
    pencilStroke(pen,pigments[i%pigments.length],moving ? .55+(i%5)*.51 : .65);
  }
  if(pencilGrain){j.fillStyle=pencilGrain;j.globalAlpha=.56;j.fill(body);}
  j.restore();
  for(const side of [-1,1]){
    const edge=new Path2D();edge.moveTo(...at(.06*front,side));
    for(let i=2;i<=18;i++) edge.lineTo(...at(front*i/18,side));
    pencilStroke(edge,'rgba(154,93,30,.62)',.86);
  }
}

// The crest is one connected silhouette. Its lobes curl at different heights.
// The moving surface marks and spray run independently of the silhouette.
const splashCrest=new Path2D(
  'M-116 3 C-108 -3 -94 -1 -85 -9 C-79 -20 -98 -34 -108 -29 C-115 -25 -117 -32 -111 -37 '+
  'C-98 -45 -83 -30 -77 -26 C-73 -24 -74 -35 -70 -35 C-63 -37 -67 -20 -57 -21 '+
  'C-51 -24 -62 -39 -54 -40 C-43 -39 -51 -25 -41 -20 Q-32 -29 -25 -14 '+
  'Q-15 -17 -8 -9 Q2 -16 8 -9 Q18 -19 27 -15 C33 -15 35 -22 37 -27 '+
  'C43 -36 50 -31 46 -25 Q42 -15 52 -21 C63 -28 60 -42 73 -46 '+
  'C85 -50 91 -41 85 -40 C70 -40 72 -23 76 -23 C83 -23 90 -34 97 -32 '+
  'Q104 -32 96 -26 C86 -18 98 -23 108 -28 C117 -33 127 -31 127 -27 '+
  'C126 -24 117 -27 112 -23 C92 -13 94 -4 116 0 C94 3 79 0 68 5 '+
  'C40 13 26 3 5 7 C-31 13 -39 1 -59 6 C-79 11 -82 2 -116 3Z');
function paintSplash(x,y,radius,time) {
  j.save();j.translate(x,y);j.scale(radius/110,radius/110);
  const hue=j.createLinearGradient(0,-46,0,10);
  hue.addColorStop(0,'#ffe57b');hue.addColorStop(.46,'#ffca42');hue.addColorStop(1,'#f29a24');
  wash(splashCrest,hue);pencilStroke(splashCrest,'#bc7727',.85);
  j.save();j.clip(splashCrest);
  for(let i=0;i<42;i++){
    const side=i%2===0?-1:1, phase=(i*.337+time*.83)%1;
    const dx=side*(11+((i*31)%86)+phase*6), dy=-3-((i*11)%31);
    const mark=new Path2D();mark.moveTo(dx,dy);
    mark.quadraticCurveTo(dx+side*1.5,dy-2,dx+side*(3+i%7),dy-3-i%6);
    pencilStroke(mark,i%3===0?'#e98a23':'#ffec99',.65+i%3*.53);
  }
  j.restore();
  // Short broken contours in the rebound give the froth depth in front of the sheet.
  ripple(-71,-14,21,12,'#fff0a6',1.75);
  ripple(-46,-7,24,8,'#da881f',.8);
  ripple(-25,-8,19,7,'#ffe48b',1.3);
  ripple(17,-4,25,-3,'#ffed9a',1.7);
  ripple(62,-12,19,-8,'#e59424',.85);
  for(let i=0;i<23;i++){
    const t=(time*(.84+(i%5)*.07)+i*.381966)%1, side=i%2===0?-1:1;
    const dx=side*(24+(i*17)%46+t*(27+(i*7)%47)), dy=-4-(21+(i*19)%48)*4*t*(1-t);
    const size=.55+(i%6)*.47;
    j.beginPath();j.ellipse(dx,dy,size,size*(1.3+1.4*Math.abs(1-2*t)),side*(t*2-1)*.65,0,2*Math.PI);
    j.fillStyle=i%3===0?'#ffe293':'#f2a032';j.fill();
    j.strokeStyle='#bd812e';j.lineWidth=.5;j.stroke();
  }
  j.restore();
}

const holdThreshold = 240;
const panStart = 4.4, panEnd = 6.5;
const fadeStart = panEnd + 4, finish = fadeStart + .6;
function bounded(value) { return Math.max(0, Math.min(1, value)); }

function renderPour(age) {
  const {width,height,startX,endX,depth,lip,ratio,travel} = drawing;
  const quiet = reduced.matches;
  const pan = bounded((age-panStart)/(panEnd-panStart));
  const position = quiet ? Number(pan===1) : pan*pan*(3-2*pan);
  journey.style.setProperty('--camera', (-travel*position)+'px');
  if (pan===1 && !intro.classList.contains('quote-finished')) {
    intro.classList.add('quote-finished');
    spoken.textContent = firstClause+' '+lastClause+' '+byline;
  }
  if (age>fadeStart && !quiet) intro.style.opacity = String(1-bounded((age-fadeStart)/(finish-fadeStart)));
  if (!j) return;
  j.setTransform(ratio,0,0,ratio,0,0);
  j.clearRect(0,0,width,height);
  j.lineCap='round'; j.lineJoin='round';
  const front = quiet ? (position ? 1 : .45) : bounded(.015+.23*age+.085*age*age);
  const breadth = width*(.036+.135*(quiet ? .94 : 1-Math.exp(-age*2.8)));
  const time = quiet ? .6 : age;
  paintFall(startX,depth,front,breadth,time);
  if (front>=1) paintSplash(endX,depth,lip*(quiet ? 1.4 : 1.5+.15*Math.sin(time*8)),time);
}

function stopPress() {
  cancelAnimationFrame(frame);
  press = null;
  if (body.classList.contains('entry-playing')) {
    body.classList.remove('entry-playing');
    for (const el of document.querySelectorAll('.inside-garden,.footer,.skip')) el.inert=false;
  }
  squeeze.classList.remove('pressing');
  intro.classList.remove('quote-finished');
  journey.style.removeProperty('--camera');
  intro.style.removeProperty('opacity');
  spoken.textContent = '';
  if (j) { j.resetTransform(); j.clearRect(0,0,juice.width,juice.height); }
}

function latchPour() {
  if (press.latched) return;
  press.latched = true;
  body.classList.add('entry-playing');
  for (const el of document.querySelectorAll('.inside-garden,.footer,.skip')) el.inert=true;
  measurePour();
}

function advancePour(now) {
  if (!press) return;
  const elapsed = Math.max(0,now-press.start);
  if (elapsed>=holdThreshold) latchPour();
  if (elapsed>=finish*1000) { enter(); return; }
  renderPour(elapsed/1000);
  frame=requestAnimationFrame(advancePour);
}

function beginPour(input, immediate = false) {
  if (press || body.classList.contains('unfolded')) return;
  press={input,start:performance.now(),latched:false};
  squeeze.classList.add('pressing');
  spoken.textContent=firstClause;
  if (immediate) latchPour();
  else measurePour();
  advancePour(press.start);
}

function endContact(input) {
  if (!press || press.input!==input || press.latched) return;
  if (performance.now()-press.start>=holdThreshold) latchPour();
  else stopPress();
}
function cancelContact() { if (press && !press.latched) stopPress(); }

squeeze.addEventListener('pointerdown',event=>{
  if (!event.isPrimary || event.button!==0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
  beginPour(event.pointerId);
  squeeze.setPointerCapture(event.pointerId);
});
squeeze.addEventListener('pointerup',event=>endContact(event.pointerId));
squeeze.addEventListener('pointercancel',cancelContact);
squeeze.addEventListener('lostpointercapture',cancelContact);
squeeze.addEventListener('contextmenu',event=>event.preventDefault());
squeeze.addEventListener('dragstart',event=>event.preventDefault());
squeeze.addEventListener('keydown',event=>{
  if (!['Enter',' '].includes(event.key)) return;
  event.preventDefault();
  if (!event.repeat) beginPour(event.key, true);
});
squeeze.addEventListener('keyup',event=>{if (['Enter',' '].includes(event.key)) event.preventDefault();});
squeeze.addEventListener('click',event=>{
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  event.preventDefault();
  if (!event.detail) beginPour('activation', true);
});
squeeze.addEventListener('blur',cancelContact);
window.addEventListener('blur',cancelContact);
document.addEventListener('visibilitychange',()=>{if(document.hidden) cancelContact();});
window.addEventListener('resize',()=>{
  if (press) measurePour();
});
skipPour.addEventListener('click',event=>{event.preventDefault();enter();});
document.addEventListener('keydown',event=>{if (press?.latched && event.key==='Escape') enter();});
function returnToMango() {
  resumeVisit = Boolean(location.hash);
  history.replaceState(history.state, '', location.pathname + location.search);
  syncLocation();
  window.scrollTo({top:0,behavior:'instant'});
  squeeze.focus({preventScroll:true});
}
let backingUp = false;
window.navigation?.addEventListener('navigate', event => {
  backingUp = event.navigationType === 'traverse' && event.destination.sameDocument &&
              event.destination.index < window.navigation.currentEntry.index;
});
window.addEventListener('popstate', () => {
  if (backingUp) returnToMango();
  else syncLocation();
  backingUp = false;
});
window.addEventListener('hashchange',syncLocation);
window.addEventListener('pageshow', event => {
  const activation = window.navigation?.activation;
  const traversal = event.persisted || activation?.navigationType === 'traverse' ||
                    performance.getEntriesByType('navigation')[0]?.type === 'back_forward';
  const from = activation?.from;
  const here = window.navigation?.currentEntry;
  if (traversal && (!from || !here || from.index < 0 || from.index > here.index)) returnToMango();
  else syncLocation();
});

// Prepare the recording during the first gesture, including a squeeze. There
// is no ambient loop; each stroke follows a leaf or branch the visitor moves.
const AudioEngine = window.AudioContext || window.webkitAudioContext;
const samples = new Map();
const takes = {brush: 0, shake: 0};
let audio, lastBrush = -Infinity;
const localPlayer = new Audio();
function sampleURL(gesture, take) { return 'assets/leaves/' + gesture + '-' + (take + 1) + '.mp3?v=foliage'; }
function prepareLeaves() {
  if (!AudioEngine || location.protocol === 'file:') return;
  try {
    if (!audio) audio = new AudioEngine();
    if (audio.state !== 'running') audio.resume().catch(() => {});
    for (const gesture of ['brush','shake']) for (const take of [0,1]) {
      const url = sampleURL(gesture,take);
      if (!samples.has(url)) samples.set(url, fetch(url).then(response => {
        if (!response.ok) throw new Error('Leaf recording unavailable');
        return response.arrayBuffer();
      }).then(bytes => audio.decodeAudioData(bytes)).catch(() => { samples.delete(url); return null; }));
    }
  } catch { /* The native audio player also serves local-file previews. */ }
}
for (const event of ['pointerdown','pointerup','keydown']) {
  document.addEventListener(event, prepareLeaves, {capture:true, once:true});
}
async function rustle(force, pan=0) {
  if (document.hidden) return;
  const now=performance.now(), strength=Math.min(1.5,Math.abs(force));
  const gesture=strength>1.2?'shake':'brush';
  if (now-lastBrush < (gesture==='shake'?190:360)) return;
  lastBrush=now;
  const url=sampleURL(gesture,takes[gesture]);
  takes[gesture]=1-takes[gesture];
  const volume=gesture==='shake'?.85:.38+.2*strength;
  if (!audio || audio.state!=='running' || !samples.has(url)) {
    localPlayer.src=url; localPlayer.volume=volume;
    localPlayer.play().catch(()=>{});
    return;
  }
  const recording=await samples.get(url);
  if (!recording || document.hidden || performance.now()-now>700) return;
  const source=audio.createBufferSource(), gain=audio.createGain();
  source.buffer=recording; source.playbackRate.value=.96+Math.random()*.08;
  gain.gain.value=volume;
  source.connect(gain);
  const side=audio.createStereoPanner?.();
  if(side){side.pan.value=Math.max(-.4,Math.min(.4,pan*.45));gain.connect(side).connect(audio.destination);}
  else gain.connect(audio.destination);
  source.onended=()=>{source.disconnect();gain.disconnect();side?.disconnect();};
  source.start();
}
const vine=makeVine(canopy,rustle);
let start,ignoreClickUntil=0;
canopy.addEventListener('dragstart',event=>event.preventDefault());
canopy.addEventListener('pointerdown',event=>{
  ignoreClickUntil=0;
  start={x:event.clientX,y:event.clientY,id:event.pointerId,dragged:false};
});
canopy.addEventListener('pointermove',event=>{
  if(start?.id===event.pointerId && Math.hypot(event.clientX-start.x,event.clientY-start.y)>10)
    start.dragged=true;

});

window.addEventListener('pointerup',event=>{
  if(start?.id===event.pointerId && start.dragged) ignoreClickUntil=performance.now()+500;
  start=undefined;
  canopy.style.cursor='';
});
window.addEventListener('pointercancel',()=>{start=undefined;});
for (const link of fruits) {
  link.addEventListener('focus',()=>{if(link.matches(':focus-visible')) vine.pluck(link.dataset.stem,.8,false);});
  link.addEventListener('click',event=>{
    if(event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button!==0) return;
    if(event.detail && performance.now()<ignoreClickUntil) {event.preventDefault();return;}
    vine.pluck(link.dataset.stem,.86);
  });
}

syncLocation();
