// static/js/api.js
import { MAP_URL, DETECTIONS_URL } from './config.js';

export async function fetchMap() {
  return await fetch(MAP_URL).then(res => res.json());
}

export async function fetchDetections() {
  return await fetch(DETECTIONS_URL).then(res => res.json());
}
