async function updateStatus() {
  try {
    const res = await fetch('/status');
    const status = await res.json();

    document.getElementById('esp8266-status').textContent = `ESP8266: ${status.esp8266 ? 'Connected' : 'Disconnected'}`;
    document.getElementById('esp32cam-status').textContent = `ESP32-CAM: ${status.esp32cam ? 'Connected' : 'Disconnected'}`;

    document.getElementById('esp8266-status').className = `px-2 py-1 rounded text-white ${status.esp8266 ? 'bg-green-500' : 'bg-red-500'}`;
    document.getElementById('esp32cam-status').className = `px-2 py-1 rounded text-white ${status.esp32cam ? 'bg-green-500' : 'bg-red-500'}`;
  } catch (e) {
    console.error("Failed to get status", e);
  }
}

document.getElementById('start-btn').addEventListener('click', async () => {
  await fetch('/start', { method: 'POST' });
  updateStatus();
});

document.getElementById('stop-btn').addEventListener('click', async () => {
  await fetch('/stop', { method: 'POST' });
  updateStatus();
});

setInterval(updateStatus, 2000);
updateStatus();
