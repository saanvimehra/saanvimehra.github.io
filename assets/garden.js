'use strict';

function preference(key) {
  try { return localStorage.getItem(key); } catch { return null; }
}
function remember(key, value) {
  try { localStorage.setItem(key, value); } catch { /* The page also works without storage. */ }
}
function setupPreference(id, key, value, css, labels) {
  const control = document.getElementById(id);
  function apply(active) {
    document.documentElement.classList.toggle(css, active);
    control.textContent = labels[active ? 1 : 0];
  }
  apply(preference(key) === value);
  control.hidden = false;
  control.addEventListener('click', () => {
    const active = !document.documentElement.classList.contains(css);
    apply(active);
    remember(key, active ? value : 'default');
  });
}
setupPreference('theme', 'mode', 'dark', 'night', ['Night', 'Day']);
if (document.querySelector('.prose')) {
  setupPreference('font', 'reading-font', 'serif', 'serif-reading', ['Serif reading', 'Sans reading']);
}

function startClock(bar) {
  const buttons = [...bar.querySelectorAll('[data-zone]')];
  const output = bar.querySelector('time');
  const dial = bar.querySelector('.dial');
  let formatter;
  function tick() {
    const now = new Date();
    const parts = Object.fromEntries(formatter.formatToParts(now).map(p => [p.type,p.value]));
    output.textContent = [parts.hour,parts.minute,parts.second].join(':');
    output.dateTime = now.toISOString();
    dial.style.setProperty('--hour', (Number(parts.hour) % 12 * 30 + Number(parts.minute) / 2) + 'deg');
    dial.style.setProperty('--minute', (Number(parts.minute) * 6 + Number(parts.second) / 10) + 'deg');
  }
  function select(button) {
    for (const other of buttons) other.setAttribute('aria-pressed', String(other === button));
    formatter = new Intl.DateTimeFormat('en-GB', {timeZone:button.dataset.zone, hour:'2-digit',
      minute:'2-digit', second:'2-digit', hourCycle:'h23'});
    output.setAttribute('aria-label', 'Local time in ' + button.textContent);
    tick();
  }
  buttons.forEach(button => button.addEventListener('click', () => {
    select(button);
    remember('garden-city', button.dataset.zone);
  }));
  select(buttons.find(b => b.dataset.zone === preference('garden-city')) || buttons[0]);
  bar.hidden = false;
  setInterval(() => { if (!document.hidden) tick(); }, 1000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) tick(); });
}
const clock = document.querySelector('.time-bar');
if (clock) startClock(clock);

function startGraph(container) {
  const notes = JSON.parse(document.getElementById('graph-data').textContent);
  const byId = new Map(notes.map(note => [note.slug, note]));
  if (!notes.length) {
    container.textContent = 'No public notes yet.';
    return;
  }
  const picker = document.createElement('select');
  picker.id = 'graph-picker';
  for (const note of notes) picker.add(new Option(note.title, note.slug));
  const label = document.createElement('label');
  label.htmlFor = picker.id;
  label.textContent = 'Start with';
  const toolbar = document.createElement('div');
  toolbar.className = 'graph-toolbar';
  toolbar.append(label, picker);
  const canvas = document.createElement('div');
  canvas.className = 'graph-canvas';
  canvas.setAttribute('role','group');
  const detail = document.createElement('div');
  detail.className = 'graph-detail';
  container.append(toolbar,canvas,detail);
  function node(note, x, y, centre) {
    const link = document.createElement('a');
    link.className = 'graph-node' + (centre ? ' centre' : '');
    link.href = centre ? note.url : '#' + note.slug;
    link.textContent = note.title;
    link.setAttribute('aria-label', (centre ? 'Read ' : 'Explore links to ') + note.title);
    link.style.setProperty('--nx', x + '%');
    link.style.setProperty('--ny', y + '%');
    canvas.append(link);
    return link;
  }
  function draw(moveFocus = false) {
    const note = byId.get(location.hash.slice(1)) || byId.get('dharma-and-karma') || notes[0];
    picker.value = note.slug;
    canvas.setAttribute('aria-label','Notes connected to ' + note.title);
    const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
    svg.setAttribute('viewBox','0 0 100 100');
    svg.setAttribute('preserveAspectRatio','none');
    svg.setAttribute('aria-hidden','true');
    canvas.replaceChildren(svg);
    const centre = node(note,50,50,true);
    const count = note.neighbours.length;
    canvas.style.minHeight = Math.max(320, Math.ceil(count / 2) * 100) + 'px';
    note.neighbours.forEach((id,i) => {
      const left = i % 2 === 0;
      const sideCount = left ? Math.ceil(count / 2) : Math.floor(count / 2);
      const x = left ? 17 : 83;
      const y = 100 * (Math.floor(i / 2) + 1) / (sideCount + 1);
      const path = document.createElementNS(svg.namespaceURI,'path');
      path.setAttribute('d', 'M50 50 Q' + (left ? 32 : 68) + ' 50 ' + x + ' ' + y);
      svg.append(path);
      node(byId.get(id),x,y,false);
    });
    const open = document.createElement('a');
    open.href = note.url; open.className = 'open-note'; open.textContent = 'Read this note';
    detail.replaceChildren(note.branch + ' · ' + count + (count === 1 ? ' connection' : ' connections'), open);
    if (moveFocus) centre.focus({preventScroll:true});
  }
  picker.addEventListener('change', () => { location.hash = picker.value; });
  window.addEventListener('hashchange', () => draw(document.activeElement !== picker));
  draw();
}
const graph = document.getElementById('graph');
if (graph) startGraph(graph);
