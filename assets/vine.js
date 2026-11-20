// The drawing is a set of connected pen strokes in a 720 × 560 sketchbook.
// Each leaf pivots on its petiole. Each twig carries its children with it.
function makeVine(canopy, onBrush) {
  const canvas=canopy.querySelector('canvas'), ctx=canvas.getContext('2d');
  if (!ctx) return {pluck() {}};
  const W=720,H=560, nodes=[], leaves=[], byName=new Map();
  const reduce=matchMedia('(prefers-reduced-motion:reduce)');
  let seed=37, frame=0, last=0, scale=1, lastHit=null, lastTime=0;
  const random=()=>{seed=seed*16807%2147483647;return seed/2147483647;};
  function at(n,t) {
    const u=1-t, c=n.curve;
    return [0,1].map(j=>u*u*u*n.base[j]+3*u*u*t*c[j]+3*u*t*t*c[2+j]+t*t*t*c[4+j]);
  }
  function stem(name,parent,t,curve,width) {
    const p=byName.get(parent), base=p?at(p,t):[288,529];
    const n={name,base,curve,width,angle:0,speed:0,children:[],leaves:[],samples:[],parent:p};
    if(p)p.children.push(n);
    nodes.push(n);byName.set(name,n);return n;
  }
  stem('trunk',null,0,[316,497,291,431,344,363],6.5);
  stem('leader','trunk',.98,[381,319,323,265,382,191],3.6);
  stem('crest','leader',.96,[409,155,400,84,492,64],2.3);
  stem('curl','crest',.86,[482,55,491,26,518,40],1.05);
  stem('left','trunk',.78,[276,375,234,327,170,313],4);
  stem('left-low','left',.72,[176,305,111,352,72,335],1.7);
  stem('western','left',.57,[218,281,185,254,110,238],2.4);
  stem('upper-left','leader',.49,[324,245,261,202,205,174],2.8);
  stem('upper-tip','upper-left',.83,[211,156,196,115,159,125],1.25);
  stem('right','leader',.23,[420,305,482,280,538,221],3.3);
  stem('east','right',.89,[568,185,586,150,660,152],1.95);
  stem('lower-right','trunk',.95,[395,374,448,398,539,360],2.9);
  stem('east-tip','lower-right',.75,[540,366,587,373,619,334],1.4);
  stem('alphonso','left-low',.34,[150,327,140,332,141,346],.95);
  stem('safeda','east',.66,[604,160,610,158,610,181],1);
  stem('langra','western',.76,[129,248,118,245,118,262],1);
  stem('dasheri','leader',.86,[377,210,395,208,393,230],1.1);
  const fruitLinks=new Map([...canopy.querySelectorAll('[data-stem]')].map(a=>[a.dataset.stem,a]));
  function cluster(n,t,count,angle,length) {
    const base=at(n,t);
    for(let i=0;i<count;i++){
      const l={parent:n,base,rotation:angle+(i-(count-1)/2)*.53+(random()-.5)*.33,
        length:length*(.72+random()*.51),width:3.3+random()*3.8,bow:(random()-.38)*13,
        tone:random(),angle:0,speed:0,k:80+random()*45};
      n.leaves.push(l);leaves.push(l);
    }
  }
  for(const [name,t,count,angle,len] of [
    ['left-low',.97,4,2.84,45],['left-low',.57,3,2.05,40],['western',.98,4,2.95,51],
    ['western',.58,3,1.68,41],['left',.55,2,2.4,37],['upper-tip',.98,4,2.7,46],
    ['upper-tip',.49,2,1.72,44],['upper-left',.71,3,2.76,36],['leader',.8,3,2.33,39],
    ['crest',.38,3,2.73,39],['crest',.99,4,.18,46],['curl',.98,3,.14,34],
    ['east',.97,4,.32,43],['east',.52,3,.98,40],['right',.82,3,.50,39],
    ['right',.47,2,1.23,44],['east-tip',.95,4,.23,48],['east-tip',.42,3,.86,38],
    ['lower-right',.66,2,.92,39],['trunk',.48,2,2.58,32]
  ]) cluster(byName.get(name),t,count,angle,len);
  function project(x,y) {
    const m=ctx.getTransform();
    return [(m.a*x+m.c*y+m.e)/scale,(m.b*x+m.d*y+m.f)/scale];
  }
  function drawLeaf(l) {
    ctx.save();ctx.translate(...l.base);ctx.rotate(l.rotation+l.angle);
    const L=l.length,B=l.bow,D=l.width;
    ctx.beginPath();ctx.moveTo(0,0);ctx.quadraticCurveTo(3,0,8,B*.12);ctx.stroke();
    ctx.beginPath();ctx.moveTo(6,B*.10);
    ctx.bezierCurveTo(L*.27,-D*1.15,L*.67,B-D*1.3,L,B);
    ctx.bezierCurveTo(L*.72,B+D*.26,L*.41,D*1.64,6,B*.1);
    ctx.fillStyle=l.tone>.65?'rgba(117,131,85,.24)':'rgba(141,145,100,.10)';ctx.fill();ctx.stroke();
    ctx.beginPath();ctx.moveTo(6,B*.1);ctx.quadraticCurveTo(L*.52,B*.13,L*.94,B*.92);ctx.stroke();
    ctx.save();ctx.globalAlpha=.48;ctx.lineWidth=.48;
    for(let i=1;i<=3;i++){
      const t=.22+i*.13;ctx.beginPath();ctx.moveTo(L*t,B*t*t);
      ctx.quadraticCurveTo(L*(t+.04),B*t*t-D*.58,L*(t+.10),B*t*t-D*.76);ctx.stroke();
    }
    ctx.restore();l.from=project(4,0);l.to=project(L,B);ctx.restore();
  }
  function drawNode(n) {
    ctx.save();ctx.translate(...n.base);ctx.rotate(n.angle);ctx.translate(-n.base[0],-n.base[1]);
    const c=n.curve;
    ctx.strokeStyle=ink;ctx.lineWidth=n.width*.48;ctx.beginPath();ctx.moveTo(...n.base);ctx.bezierCurveTo(...c);ctx.stroke();
    if(n.width>1.4){
      ctx.save();ctx.lineWidth=.58;ctx.globalAlpha=.67;ctx.beginPath();ctx.moveTo(n.base[0]-n.width,n.base[1]);
      ctx.bezierCurveTo(c[0]-n.width*1.08,c[1]+1,c[2]-n.width*.47,c[3],c[4],c[5]);ctx.stroke();ctx.restore();
    }
    n.samples=Array.from({length:11},(_,i)=>project(...at(n,i/10)));
    for(const child of n.children)drawNode(child);
    ctx.strokeStyle=leafInk;ctx.lineWidth=.87;
    for(const l of n.leaves) drawLeaf(l);
    const link=fruitLinks.get(n.name);
    if(link){
      const tip=n.samples[10];link.style.left=tip[0]/W*100+'%';link.style.top=tip[1]/H*100+'%';
      link.style.setProperty('--bend',n.angle*.85+'rad');
    }
    ctx.restore();
  }
  const ink='#514d36', leafInk='#4f593b';
  function draw(){
    const r=canopy.getBoundingClientRect();if(!r.width)return;
    const w=Math.round(r.width*Math.min(devicePixelRatio||1,2));
    if(canvas.width!==w || canvas.height!==Math.round(w*H/W)){canvas.width=w;canvas.height=Math.round(w*H/W);}
    scale=w/W;ctx.setTransform(scale,0,0,scale,0,0);ctx.clearRect(0,0,W,H);
    ctx.lineCap='round';ctx.lineJoin='round';drawNode(nodes[0]);
  }
  function tick(now) {
    const dt=Math.min((now-last)/1000,.025);last=now;let moving=false;
    for(const part of [...nodes,...leaves]){
      part.speed+=(-part.angle*(part.k||47)-part.speed*(part.k?6.3:6.7))*dt;
      part.angle+=part.speed*dt;
      if(Math.abs(part.angle)+Math.abs(part.speed)>.003) moving=true;
      else {part.angle=0;part.speed=0;}
    }
    draw();frame=moving&&!document.hidden?requestAnimationFrame(tick):0;
  }
  function nudge(part,force,sound=true) {
    if(!part)return;
    if(sound)onBrush(force,2*(part.from || part.base)[0]/W-1);
    if(reduce.matches)return;
    part.speed=Math.max(-4,Math.min(4,part.speed+force*(part.k?2.8:1.35)));
    if(part.parent && part.parent!==nodes[0]) part.parent.speed+=force*(part.k?.22:.095);
    if(!frame){last=performance.now();frame=requestAnimationFrame(tick);}
  }
  function distance(x,y,a,b) {
    const dx=b[0]-a[0],dy=b[1]-a[1];
    const t=Math.max(0,Math.min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy||1)));
    return Math.hypot(x-a[0]-t*dx,y-a[1]-t*dy);
  }
  let prevX;
  function brush(e) {
    const r=canopy.getBoundingClientRect(),x=(e.clientX-r.left)*W/r.width,y=(e.clientY-r.top)*H/r.height;
    const dir=Math.sign(x-(prevX??x))||1;prevX=x;let hit=null,best=12;
    for(const l of leaves){if(!l.from)continue;const d=distance(x,y,l.from,l.to);if(d<best){hit=l;best=d;}}
    if(!hit)for(const n of nodes)for(let i=1;i<n.samples.length;i++){const d=distance(x,y,n.samples[i-1],n.samples[i]);if(d<best){hit=n;best=d;}}
    canopy.style.cursor=hit?'grab':'';
    if(hit && (hit!==lastHit || performance.now()-lastTime>160)){nudge(hit,dir);lastTime=performance.now();}
    lastHit=hit;
  }
  canopy.addEventListener('pointermove',brush);canopy.addEventListener('pointerdown',brush);
  canopy.addEventListener('pointerleave',()=>{lastHit=null;prevX=undefined;});
  canvas.hidden=false;canopy.querySelector('.vine-still').hidden=true;
  new ResizeObserver(draw).observe(canopy);
  draw();
  return {pluck(name,force=.9,sound=true){nudge(byName.get(name),force,sound);}};
}
