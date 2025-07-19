from flask import Flask, request, jsonify, send_from_directory, render_template
import os, uuid, json
from detector.model import detect_human

app = Flask(__name__, static_folder='static', template_folder='templates')

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('data', exist_ok=True)

MAP_DATA_FILE = 'data/map.json'
DETECTION_FILE = 'data/detections.json'
STATUS_FILE = 'data/status.json'
POSITION_FILE = 'data/position.json'

def load_json(path, default=[]):
    if os.path.exists(path):
        with open(path, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return default
    return default

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status')
def get_status():
    return jsonify(load_json(STATUS_FILE, {
        'esp8266': True,
        'esp32cam': True,
        'start': False
    }))

@app.route('/start', methods=['POST'])
def start():
    status = load_json(STATUS_FILE, {})
    status['start'] = True
    save_json(STATUS_FILE, status)
    return jsonify({'status': 'started'})

@app.route('/stop', methods=['POST'])
def stop():
    status = load_json(STATUS_FILE, {})
    status['start'] = False
    status['manual_stop'] = True
    save_json(STATUS_FILE, status)
    return jsonify({'status': 'stopped'})

@app.route('/should_move')
def should_move():
    status = load_json(STATUS_FILE, {})
    return jsonify({'move': status.get('start', False)})

@app.route('/position', methods=['POST'])
def update_position():
    data = request.get_json()
    x, y = data.get('x'), data.get('y')
    if x is None or y is None:
        return jsonify({'error': 'Missing coordinates'}), 400

    prev = load_json(POSITION_FILE, {})
    if prev.get('x') != x or prev.get('y') != y:
        save_json(POSITION_FILE, {'x': x, 'y': y})
        status = load_json(STATUS_FILE, {})
        status['start'] = False
        status['manual_stop'] = False
        save_json(STATUS_FILE, status)
        return jsonify({'action': 'await_image'})

    return jsonify({'action': 'continue'})

@app.route('/upload', methods=['POST'])
def upload_image():
    image = request.files.get('image')

    # Get last known position from position.json
    pos = load_json(POSITION_FILE, {})
    x = pos.get('x')
    y = pos.get('y')

    if not image or x is None or y is None:
        return jsonify({'error': 'Missing image or position data'}), 400

    filename = f"{x}_{y}_{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    image.save(filepath)

    print(f"[SERVER] Received image from ESP32-CAM for position ({x}, {y})")

    is_human = detect_human(filepath)

    # Update map
    map_data = load_json(MAP_DATA_FILE)
    if not any(p['x'] == x and p['y'] == y for p in map_data):
        map_data.append({'x': x, 'y': y, 'visited': True})
    save_json(MAP_DATA_FILE, map_data)

    # Update detections
    detections = load_json(DETECTION_FILE)

    # Remove old entry for this coordinate
    detections = [d for d in detections if not (d['x'] == x and d['y'] == y)]

    # Add updated entry
    detections.append({
        'x': x,
        'y': y,
        'human': is_human,
        'image': f'uploads/{filename}'
    })

    save_json(DETECTION_FILE, detections)


    # Allow robot to move again if not manually stopped
    status = load_json(STATUS_FILE, {})
    if not status.get('manual_stop', False):
        status['start'] = True
    save_json(STATUS_FILE, status)

    return jsonify({'status': 'ok', 'human': is_human})

@app.route('/data/map.json')
def get_map():
    return jsonify(load_json(MAP_DATA_FILE))

@app.route('/data/detections')
def get_detections():
    return jsonify(load_json(DETECTION_FILE))

@app.route('/uploads/<path:filename>')
def serve_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/status/esp8266', methods=['POST'])
def update_esp8266_status():
    incoming = request.get_json(silent=True) or {}
    value = incoming.get('connected', True)
    data = load_json(STATUS_FILE, {})
    data['esp8266'] = value
    save_json(STATUS_FILE, data)
    return jsonify({'status': f'esp8266 set to {value}'})

@app.route('/status/esp32cam', methods=['POST'])
def update_esp32cam_status():
    incoming = request.get_json(silent=True) or {}
    value = incoming.get('connected', True)
    data = load_json(STATUS_FILE, {})
    data['esp32cam'] = value
    save_json(STATUS_FILE, data)
    return jsonify({'status': f'esp32cam set to {value}'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
