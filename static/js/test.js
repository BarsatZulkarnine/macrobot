// static/js/api.js
import { MAP_URL, DETECTIONS_URL } from './config.js';

export async function fetchMap() {
  return await fetch(MAP_URL).then(res => res.json());
}

export async function fetchDetections() {
  return await fetch(DETECTIONS_URL).then(res => res.json());
}
import { UPLOAD_BASE } from './config.js';

export function renderGrid(containerId, gridData) {
  const { grid, gridImages, bounds } = gridData;
  const container = document.getElementById(containerId);
  container.innerHTML = '';

  for (let y = bounds.maxY; y >= bounds.minY; y--) {
    const row = document.createElement('div');
    row.className = 'row';

    for (let x = bounds.minX; x <= bounds.maxX; x++) {
      const key = `${x},${y}`;
      const cell = document.createElement('div');
      cell.className = 'cell';

      if (grid[key] === 'visited') {
        cell.classList.add('visited');
        row.appendChild(cell);
      } else if (grid[key] === 'human') {
          cell.classList.add('human');

        // Create clickable link inside the cell
        const link = document.createElement('a');
        link.href = `${UPLOAD_BASE}${gridImages[key]}`;
        link.target = '_blank';
        link.style.display = 'block';
        link.style.width = '100%';
        link.style.height = '100%';

        // Append link inside cell, not outside
        cell.appendChild(link);
        row.appendChild(cell);
      } else {
        // For empty or unknown cells
        row.appendChild(cell);
      }
    }

    container.appendChild(row);
  }
}
// static/js/config.js
export const MAP_URL = '/data/map.json';
export const DETECTIONS_URL = '/data/detections';
export const UPLOAD_BASE = '/uploads/';
export const REFRESH_INTERVAL = 3000;
// static/js/grid.js
export function buildGrid(map, detections) {
  const knownPoints = new Set();
  const grid = {};
  const gridImages = {};

  map.forEach(p => {
    const key = `${p.x},${p.y}`;
    knownPoints.add(key);
    grid[key] = 'visited';
  });

  detections.forEach(d => {
    const key = `${d.x},${d.y}`;
    if (d.human) {
      grid[key] = 'human';
      gridImages[key] = d.image.split('/').pop();
    }
  });

  return { grid, gridImages, bounds: getBounds(knownPoints) };
}

function getBounds(points) {
  const coords = Array.from(points).map(k => k.split(',').map(Number));
  const xs = coords.map(c => c[0]);
  const ys = coords.map(c => c[1]);
  return {
    minX: Math.min(...xs),
    maxX: Math.max(...xs),
    minY: Math.min(...ys),
    maxY: Math.max(...ys)
  };
}
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
