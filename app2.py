from flask import Flask, request, jsonify, send_from_directory, render_template
import os, uuid, json, time
from detector.model import detect_human_simple

app = Flask(__name__, static_folder='static', template_folder='templates')

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('data', exist_ok=True)

# Simplified data files
ROBOT_STATE_FILE = 'data/robot_state.json'
MAP_DATA_FILE = 'data/map_data.json'

def load_json(path, default=None):
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

def get_robot_state():
    """Get current robot state with defaults"""
    return load_json(ROBOT_STATE_FILE, {
        'current_x': 0,
        'current_y': 0,
        'is_running': False,
        'waiting_for_image': False,
        'last_update': time.time()
    })

def save_robot_state(state):
    """Save robot state"""
    state['last_update'] = time.time()
    save_json(ROBOT_STATE_FILE, state)

def get_map_data():
    """Get map data with defaults"""
    return load_json(MAP_DATA_FILE, {
        'visited_positions': [],  # [{'x': 0, 'y': 0, 'human_detected': False, 'image_path': '...', 'timestamp': ...}]
        'exploration_stack': []   # DFS stack for positions to explore
    })

def save_map_data(data):
    """Save map data"""
    save_json(MAP_DATA_FILE, data)

@app.route('/')
def index():
    return render_template('index.html')

# ===================== MAIN ROBOT ENDPOINTS =====================

@app.route('/robot/status', methods=['GET'])
def get_robot_status():
    """Get current robot status - main endpoint for robot to check what to do"""
    state = get_robot_state()
    map_data = get_map_data()
    
    # Check if robot has been at current position and needs image
    current_pos = (state['current_x'], state['current_y'])
    position_explored = any(
        pos['x'] == current_pos[0] and pos['y'] == current_pos[1] 
        for pos in map_data['visited_positions']
    )
    
    response = {
        'current_position': {'x': state['current_x'], 'y': state['current_y']},
        'is_running': state['is_running'],
        'needs_image': state['is_running'] and not position_explored,
        'waiting_for_image': state['waiting_for_image'],
        'next_move': None
    }
    
    # If running and current position is explored, suggest next move
    if state['is_running'] and position_explored and not state['waiting_for_image']:
        if map_data['exploration_stack']:
            next_pos = map_data['exploration_stack'][-1]  # DFS - take from top
            response['next_move'] = next_pos
        else:
            # No more positions to explore
            response['exploration_complete'] = True
    
    return jsonify(response)

@app.route('/robot/start', methods=['POST'])
def start_exploration():
    """Start the exploration process"""
    state = get_robot_state()
    state['is_running'] = True
    state['waiting_for_image'] = False
    save_robot_state(state)
    
    # Initialize exploration stack with adjacent positions from (0,0)
    map_data = get_map_data()
    if not map_data['exploration_stack']:
        # Add initial adjacent positions to explore (DFS)
        initial_positions = [
            {'x': 1, 'y': 0},
            {'x': 0, 'y': 1},
            {'x': -1, 'y': 0},
            {'x': 0, 'y': -1}
        ]
        map_data['exploration_stack'] = initial_positions
        save_map_data(map_data)
    
    return jsonify({'status': 'exploration_started'})

@app.route('/robot/stop', methods=['POST'])
def stop_exploration():
    """Stop the exploration process"""
    state = get_robot_state()
    state['is_running'] = False
    state['waiting_for_image'] = False
    save_robot_state(state)
    return jsonify({'status': 'exploration_stopped'})

@app.route('/robot/position', methods=['POST'])
def update_position():
    """Update robot's current position"""
    data = request.get_json()
    x, y = data.get('x'), data.get('y')
    
    if x is None or y is None:
        return jsonify({'error': 'Missing x or y coordinates'}), 400
    
    state = get_robot_state()
    state['current_x'] = x
    state['current_y'] = y
    state['waiting_for_image'] = True  # Robot should take image at new position
    save_robot_state(state)
    
    print(f"[ROBOT] Moved to position ({x}, {y}) - waiting for image")
    return jsonify({'status': 'position_updated', 'action': 'take_image'})

@app.route('/robot/image', methods=['POST'])
def process_image():
    """Process uploaded image from current position"""
    # Handle image upload
    if 'image' in request.files:
        image = request.files['image']
    else:
        image = request.stream
    
    state = get_robot_state()
    x, y = state['current_x'], state['current_y']
    
    if not image:
        return jsonify({'error': 'No image provided'}), 400
    
    # Save image
    filename = f"pos_{x}_{y}_{uuid.uuid4().hex[:8]}.jpg"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    if hasattr(image, 'save'):
        image.save(filepath)
    else:
        with open(filepath, 'wb') as f:
            f.write(image.read())
    
    print(f"[ROBOT] Image received for position ({x}, {y})")
    
    # Detect human
    human_detected = detect_human_simple(filepath)
    
    # Update map data
    map_data = get_map_data()
    
    # Remove current position from visited if exists and add updated entry
    map_data['visited_positions'] = [
        pos for pos in map_data['visited_positions'] 
        if not (pos['x'] == x and pos['y'] == y)
    ]
    
    map_data['visited_positions'].append({
        'x': x,
        'y': y,
        'human_detected': human_detected,
        'image_path': f'uploads/{filename}',
        'timestamp': time.time()
    })
    
    # Add new adjacent positions to exploration stack (DFS)
    adjacent_positions = [
        {'x': x + 1, 'y': y},
        {'x': x - 1, 'y': y},
        {'x': x, 'y': y + 1},
        {'x': x, 'y': y - 1}
    ]
    
    for pos in adjacent_positions:
        # Check if position already visited or in stack
        already_visited = any(
            v['x'] == pos['x'] and v['y'] == pos['y'] 
            for v in map_data['visited_positions']
        )
        already_in_stack = any(
            s['x'] == pos['x'] and s['y'] == pos['y'] 
            for s in map_data['exploration_stack']
        )
        
        if not already_visited and not already_in_stack:
            map_data['exploration_stack'].append(pos)
    
    save_map_data(map_data)
    
    # Update robot state
    state['waiting_for_image'] = False
    save_robot_state(state)
    
    return jsonify({
        'status': 'image_processed',
        'human_detected': human_detected,
        'new_positions_added': len([p for p in adjacent_positions if not any(
            v['x'] == p['x'] and v['y'] == p['y'] for v in map_data['visited_positions']
        )])
    })

@app.route('/robot/next_move', methods=['GET'])
def get_next_move():
    """Get next position to move to (DFS)"""
    state = get_robot_state()
    
    if not state['is_running']:
        return jsonify({'error': 'Robot not running'}), 400
    
    map_data = get_map_data()
    
    if not map_data['exploration_stack']:
        return jsonify({'exploration_complete': True, 'next_move': None})
    
    # Get next position from stack (DFS - LIFO)
    next_position = map_data['exploration_stack'].pop()
    save_map_data(map_data)
    
    return jsonify({
        'next_move': next_position,
        'remaining_positions': len(map_data['exploration_stack'])
    })

# ===================== DATA ENDPOINTS =====================

@app.route('/data/map', methods=['GET'])
def get_map():
    """Get map data for visualization"""
    return jsonify(get_map_data())

@app.route('/data/robot', methods=['GET'])
def get_robot_data():
    """Get robot state for monitoring"""
    return jsonify(get_robot_state())

@app.route('/uploads/<path:filename>')
def serve_image(filename):
    """Serve uploaded images"""
    return send_from_directory(UPLOAD_FOLDER, filename)

# ===================== UTILITY ENDPOINTS =====================

@app.route('/reset', methods=['POST'])
def reset_all():
    """Reset all data (for testing)"""
    # Reset robot state
    initial_state = {
        'current_x': 0,
        'current_y': 0,
        'is_running': False,
        'waiting_for_image': False,
        'last_update': time.time()
    }
    save_robot_state(initial_state)
    
    # Reset map data
    initial_map = {
        'visited_positions': [],
        'exploration_stack': []
    }
    save_map_data(initial_map)
    
    return jsonify({'status': 'all_data_reset'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)