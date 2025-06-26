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
