'use strict';
const specimen = document.querySelector('.type-lab');
const words = specimen.querySelector('#type-words');
const slider = specimen.querySelector('#type-reach');
const readout = specimen.querySelector('#type-value');
const axis = specimen.querySelector('.type-axis');
function showReach() {
  words.style.fontVariationSettings = '"SERF" ' + slider.value;
  readout.value = slider.value + '%';
}
specimen.querySelector('#type-faces').addEventListener('change', event => {
  const face = event.target.value;
  words.dataset.face = face;
  axis.hidden = face !== 'guthli';
});
slider.addEventListener('input', showReach);
showReach();
specimen.querySelector('.type-controls').hidden = false;
