from flask import Flask, request, jsonify, send_from_directory, render_template
import os
import uuid
import json
from detector.model import detect_human

app = Flask(__name__, static_folder='static', template_folder='templates')

UPLOAD_FOLDER = 'uploads'
MAP_DATA_FILE = 'data/map.json'
DETECTION_FILE = 'data/detections.json'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('data', exist_ok=True)

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    image = request.files.get('image')
    x = request.form.get('x', type=int)
    y = request.form.get('y', type=int)

    if not image or x is None or y is None:
        return jsonify({'error': 'Missing data'}), 400

    filename = f"{x}_{y}_{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    image.save(filepath)

    # Run human detection (face, torso, etc.)
    is_human = detect_human(filepath)

    # Update map
    map_data = load_json(MAP_DATA_FILE)
    if not any(p['x'] == x and p['y'] == y for p in map_data):
        map_data.append({'x': x, 'y': y, 'visited': True})
        save_json(MAP_DATA_FILE, map_data)

    # Update detections
    detections = load_json(DETECTION_FILE)
    detections.append({
        'x': x, 'y': y,
        'human': is_human,
        'image': filepath
    })
    save_json(DETECTION_FILE, detections)

    return jsonify({'status': 'ok', 'human': is_human})

@app.route('/data/map.json')
def get_map():
    return jsonify(load_json(MAP_DATA_FILE))

@app.route('/data/detections')
def get_detections():
    return jsonify(load_json(DETECTION_FILE))

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/position', methods=['POST'])
def position():
    data = request.get_json()
    if not data or 'x' not in data or 'y' not in data:
        return jsonify({'error': 'Missing x or y in JSON'}), 400

    x = data['x']
    y = data['y']

    # Load existing map data
    map_data = load_json(MAP_DATA_FILE)

    # Check if position exists, if not add it
    if not any(p['x'] == x and p['y'] == y for p in map_data):
        map_data.append({'x': x, 'y': y, 'visited': True})
        save_json(MAP_DATA_FILE, map_data)

    return jsonify({'status': 'ok', 'x': x, 'y': y})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)


