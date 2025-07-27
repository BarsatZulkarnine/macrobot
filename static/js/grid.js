export function buildGrid(mapData, robotData) {
  const grid = {};
  const gridImages = {};
  const allPositions = new Set();
  
  // Add visited positions from map data
  mapData.visited_positions.forEach(pos => {
    const key = `${pos.x},${pos.y}`;
    allPositions.add(key);
    
    // Set cell type based on human detection
    grid[key] = pos.human_detected ? 'human' : 'visited';
    
    // Extract just the filename from image path
    if (pos.image_path) {
      gridImages[key] = pos.image_path.replace('uploads/', '');
    }
  });
  
  // Add exploration stack positions (planned but not visited)
  mapData.exploration_stack.forEach(pos => {
    const key = `${pos.x},${pos.y}`;
    if (!grid[key]) { // Only if not already visited
      allPositions.add(key);
      grid[key] = 'planned';
    }
  });
  
  // Add current robot position
  if (robotData.current_x !== undefined && robotData.current_y !== undefined) {
    const robotKey = `${robotData.current_x},${robotData.current_y}`;
    allPositions.add(robotKey);
    
    // If robot is at unvisited position, mark as current
    if (!grid[robotKey] || grid[robotKey] === 'planned') {
      grid[robotKey] = 'current';
    } else {
      // Robot is at visited position, add special marker
      grid[robotKey] = grid[robotKey] + ' current';
    }
  }
  
  return { 
    grid, 
    gridImages, 
    bounds: getBounds(allPositions),
    robotData,
    mapData
  };
}

function getBounds(positions) {
  if (positions.size === 0) {
    return { minX: -2, maxX: 2, minY: -2, maxY: 2 }; // Default view
  }
  
  const coords = Array.from(positions).map(k => k.split(',').map(Number));
  const xs = coords.map(c => c[0]);
  const ys = coords.map(c => c[1]);
  
  // Add padding around the grid
  const padding = 1;
  return {
    minX: Math.min(...xs) - padding,
    maxX: Math.max(...xs) + padding,
    minY: Math.min(...ys) - padding,
    maxY: Math.max(...ys) + padding
  };
}