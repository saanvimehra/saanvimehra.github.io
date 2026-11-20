'use strict';

const credits = document.querySelector('.credits');
if (credits) {
  let hoverTimer, preview = false;
  function closeCredits() {
    clearTimeout(hoverTimer);
    preview = false;
    credits.open = false;
  }
  credits.addEventListener('pointerenter', event => {
    clearTimeout(hoverTimer);
    if (event.pointerType === 'mouse' && !credits.open) {
      hoverTimer = setTimeout(() => {preview = true; credits.open = true;}, 150);
    }
  });
  credits.addEventListener('pointerleave', () => {
    clearTimeout(hoverTimer);
    if (preview && !credits.contains(document.activeElement)) hoverTimer = setTimeout(closeCredits, 220);
  });
  credits.querySelector('summary').addEventListener('click', event => {
    clearTimeout(hoverTimer);
    if (preview) {event.preventDefault(); preview = false;}
  });
  document.addEventListener('pointerdown', event => {
    if (credits.open && !credits.contains(event.target)) closeCredits();
  });
  document.addEventListener('keydown', event => {
    if (credits.open && event.key === 'Escape') {
      const hadFocus = credits.contains(document.activeElement);
      closeCredits();
      if (hadFocus) credits.querySelector('summary').focus({preventScroll:true});
    }
  });
}

// Measure the current row before each switch so a second click can reverse mid-motion.
document.querySelector('.bio-list')?.addEventListener('click', event => {
  const target = event.target.closest('.bio-fold > summary,.bio-brief');
  if (!target || event.defaultPrevented || event.target.closest('a,button,.gloss-card')) return;
  const fromBrief = target.classList.contains('bio-brief');
  if (fromBrief && !window.getSelection()?.isCollapsed) return;
  event.preventDefault();
  const row = target.closest('li');
  const fold = row.querySelector('.bio-fold');
  const start = row.getBoundingClientRect().height;
  row.getAnimations().forEach(animation => animation.cancel());
  fold.open = !fold.open;
  if (fromBrief) fold.querySelector('summary').focus({preventScroll:true});
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  // Clip at the moving bottom edge while leaving room for the Venn and its focus ring.
  const clipPath = 'inset(-24px -24px 0 -24px)';
  const end = row.getBoundingClientRect().height;
  row.animate([{height:start+'px', clipPath}, {height:end+'px', clipPath}],
              {duration:380, easing:'cubic-bezier(.32,0,.18,1)'});
  const incoming = row.querySelector(fold.open ? '.bio-full' : '.bio-brief');
  incoming.getAnimations().forEach(animation => animation.cancel());
  incoming.animate([{opacity:.45}, {opacity:1}], {duration:220, easing:'ease-out'});
});

function setupGlosses() {
  let open, pinned = false, closeTimer;
  const position = () => {
    if (!open) return;
    const {button, card} = open;
    const bounds = button.getBoundingClientRect();
    const width = card.offsetWidth, height = card.offsetHeight;
    const left = Math.min(innerWidth - width - 12, Math.max(12, bounds.left + (bounds.width - width) / 2));
    const above = bounds.top - height - 9;
    card.style.left = left + 'px';
    card.style.top = Math.max(12, above >= 12 ? above : Math.min(bounds.bottom + 9, innerHeight - height - 12)) + 'px';
  };
  function close() {
    clearTimeout(closeTimer);
    if (!open) return;
    open.card.hidden = true;
    open.button.setAttribute('aria-expanded', 'false');
    open = null;
    pinned = false;
  }
  function show(gloss) {
    clearTimeout(closeTimer);
    if (open === gloss) return;
    close();
    open = gloss;
    gloss.card.hidden = false;
    gloss.button.setAttribute('aria-expanded', 'true');
    position();
  }
  for (const wrap of document.querySelectorAll('.gloss')) {
    const link = wrap.querySelector('.gloss-link'), card = wrap.querySelector('.gloss-card');
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = link.textContent;
    button.className = 'gloss-trigger';
    button.setAttribute('aria-controls', card.id);
    button.setAttribute('aria-expanded', 'false');
    link.replaceWith(button);
    const gloss = {wrap, button, card};
    wrap.addEventListener('pointerenter', e => { if (e.pointerType === 'mouse') show(gloss); });
    wrap.addEventListener('pointerleave', () => {
      if (open === gloss && !pinned && !wrap.contains(document.activeElement))
        closeTimer = setTimeout(close, 170);
    });
    button.addEventListener('focus', () => { if (button.matches(':focus-visible')) show(gloss); });
    button.addEventListener('click', () => {
      if (open === gloss && pinned) close();
      else { show(gloss); pinned = true; }
    });
    wrap.addEventListener('focusout', e => { if (open === gloss && !wrap.contains(e.relatedTarget)) close(); });
  }
  document.addEventListener('pointerdown', e => { if (open && !open.wrap.contains(e.target)) close(); });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && open) {
      if (open.card.contains(document.activeElement)) open.button.focus({preventScroll:true});
      close();
    }
  });
  window.addEventListener('scroll', position, {passive:true});
  window.addEventListener('resize', position);
}
if (document.querySelector('.gloss')) setupGlosses();
