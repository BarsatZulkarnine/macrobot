// static/js/api.js
import { MAP_URL, ROBOT_URL } from './config.js';

export async function fetchMapData() {
  try {
    const response = await fetch(MAP_URL);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch map data:', error);
    return { visited_positions: [], exploration_stack: [] };
  }
}

export async function fetchRobotData() {
  try {
    const response = await fetch(ROBOT_URL);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch robot data:', error);
    return { current_x: 0, current_y: 0, is_running: false };
  }
}