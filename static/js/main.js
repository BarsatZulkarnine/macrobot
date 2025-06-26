// static/js/main.js
import { fetchMap, fetchDetections } from './api.js';
import { buildGrid } from './grid.js';
import { renderGrid } from './render.js';
import { REFRESH_INTERVAL } from './config.js';

async function update() {
  const [map, detections] = await Promise.all([fetchMap(), fetchDetections()]);
  const gridData = buildGrid(map, detections);
  renderGrid('map-container', gridData);
}

update();
setInterval(update, REFRESH_INTERVAL);
