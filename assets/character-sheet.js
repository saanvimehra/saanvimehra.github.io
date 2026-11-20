'use strict';
const sheet = document.querySelector('.character-sheet');
const reach = sheet.querySelector('#char-reach');
const output = sheet.querySelector('output');
reach.addEventListener('input', () => {
  sheet.style.setProperty('--reach', reach.value);
  output.value = reach.value + '%';
});
sheet.querySelector('.char-range').hidden = false;
