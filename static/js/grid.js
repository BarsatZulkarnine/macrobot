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
  grid[key] = d.human ? 'human' : 'visited';  // Mark visited if not human
  gridImages[key] = d.image.split('/').pop(); // Always store image
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
