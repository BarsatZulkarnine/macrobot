
// static/js/render.js
import { UPLOAD_BASE } from './config.js';

export function renderGrid(containerId, gridData) {
  const { grid, gridImages, bounds, robotData, mapData } = gridData;
  const container = document.getElementById(containerId);
  
  // Clear and rebuild
  container.innerHTML = '';
  
  // Add status info
  const statusDiv = document.createElement('div');
  statusDiv.className = 'status-info';
  statusDiv.innerHTML = `
    <div class="robot-status">
      <strong>Robot Status:</strong> 
      <span class="${robotData.is_running ? 'running' : 'stopped'}">
        ${robotData.is_running ? '🤖 EXPLORING' : '⏹️ STOPPED'}
      </span>
      | Position: (${robotData.current_x}, ${robotData.current_y})
      | Visited: ${mapData.visited_positions.length}
      | Planned: ${mapData.exploration_stack.length}
    </div>
    <div class="legend">
      <span class="legend-item"><div class="legend-color visited"></div> Visited</span>
      <span class="legend-item"><div class="legend-color human"></div> Human Detected</span>
      <span class="legend-item"><div class="legend-color planned"></div> Planned</span>
      <span class="legend-item"><div class="legend-color current"></div> Robot</span>
    </div>
  `;
  container.appendChild(statusDiv);
  
  // Create grid container
  const gridContainer = document.createElement('div');
  gridContainer.className = 'grid-container';
  
  // Render grid rows (top to bottom)
  for (let y = bounds.maxY; y >= bounds.minY; y--) {
    const row = document.createElement('div');
    row.className = 'grid-row';
    
    for (let x = bounds.minX; x <= bounds.maxX; x++) {
      const key = `${x},${y}`;
      const cell = document.createElement('div');
      cell.className = 'grid-cell';
      cell.setAttribute('data-coord', `(${x},${y})`);
      
      // Add coordinate display for reference
      const coordLabel = document.createElement('div');
      coordLabel.className = 'coord-label';
      coordLabel.textContent = `${x},${y}`;
      cell.appendChild(coordLabel);
      
      if (grid[key]) {
        // Apply cell classes
        const classes = grid[key].split(' ');
        classes.forEach(cls => cell.classList.add(cls));
        
        // Add click handler for images
        if (gridImages[key]) {
          cell.style.cursor = 'pointer';
          cell.title = `Click to view image at (${x}, ${y})`;
          
          const imageIcon = document.createElement('div');
          imageIcon.className = 'image-icon';
          imageIcon.textContent = '📷';
          cell.appendChild(imageIcon);
          
          cell.addEventListener('click', () => {
            window.open(`${UPLOAD_BASE}${gridImages[key]}`, '_blank');
          });
        }
        
        // Add human detection indicator
        if (classes.includes('human')) {
          const humanIcon = document.createElement('div');
          humanIcon.className = 'human-icon';
          humanIcon.textContent = '👤';
          cell.appendChild(humanIcon);
        }
        
        // Add robot indicator
        if (classes.includes('current')) {
          const robotIcon = document.createElement('div');
          robotIcon.className = 'robot-icon';
          robotIcon.textContent = '🤖';
          cell.appendChild(robotIcon);
        }
      } else {
        cell.classList.add('empty');
      }
      
      row.appendChild(cell);
    }
    gridContainer.appendChild(row);
  }
  
  container.appendChild(gridContainer);
}
