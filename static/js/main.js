// static/js/main.js
import { fetchMapData, fetchRobotData } from './api.js';
import { buildGrid } from './grid.js';
import { renderGrid } from './render.js';
import { REFRESH_INTERVAL } from './config.js';

let updateCount = 0;

async function update() {
  try {
    updateCount++;
    console.log(`Update ${updateCount}: Fetching data...`);
    
    const [mapData, robotData] = await Promise.all([
      fetchMapData(),
      fetchRobotData()
    ]);
    
    console.log('Map data:', mapData);
    console.log('Robot data:', robotData);
    
    const gridData = buildGrid(mapData, robotData);
    renderGrid('map-container', gridData);
    
    // Update page title with status
    document.title = `Robot Explorer - ${robotData.is_running ? 'Running' : 'Stopped'} - (${robotData.current_x},${robotData.current_y})`;
    
  } catch (error) {
    console.error('Update failed:', error);
    
    // Show error message
    const container = document.getElementById('map-container');
    if (container) {
      container.innerHTML = `
        <div class="error-message">
          <h3>⚠️ Connection Error</h3>
          <p>Failed to fetch robot data. Retrying...</p>
          <p>Error: ${error.message}</p>
        </div>
      `;
    }
  }
}

// Start updates
console.log('Starting robot monitor...');
update(); // Initial update
setInterval(update, REFRESH_INTERVAL);

// Add manual refresh button
document.addEventListener('DOMContentLoaded', () => {
  const refreshBtn = document.createElement('button');
  refreshBtn.textContent = '🔄 Refresh';
  refreshBtn.className = 'refresh-btn';
  refreshBtn.onclick = update;
  
  const container = document.getElementById('map-container');
  if (container && container.parentNode) {
    container.parentNode.insertBefore(refreshBtn, container);
  }
});