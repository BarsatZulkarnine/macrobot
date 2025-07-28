from flask import Flask, request, jsonify, send_from_directory, render_template
import os, uuid, json, time, traceback
from detector.model import detect_human_simple
import logging
from werkzeug.serving import WSGIRequestHandler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', template_folder='templates')

UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('data', exist_ok=True)

# Simplified data files
ROBOT_STATE_FILE = 'data/robot_state.json'
MAP_DATA_FILE = 'data/map_data.json'

def load_json(path, default=None):
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading {path}: {e}")
    return default if default is not None else {}

def save_json(path, data):
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        logger.error(f"Error saving {path}: {e}")

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

# Error handler for all exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {str(e)}")
    logger.error(traceback.format_exc())
    return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

# Error handler for 413 (Request Entity Too Large)
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large'}), 413

@app.route('/')
def index():
    return render_template('index.html')

# ===================== MAIN ROBOT ENDPOINTS =====================

@app.route('/robot/status', methods=['GET'])
def get_robot_status():
    """Get current robot status - main endpoint for robot to check what to do"""
    try:
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
        
        logger.info(f"Status check - Position: ({state['current_x']}, {state['current_y']}), Running: {state['is_running']}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in get_robot_status: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Failed to get status', 'message': str(e)}), 500

@app.route('/robot/start', methods=['POST'])
def start_exploration():
    """Start the exploration process"""
    try:
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
        
        logger.info("Exploration started")
        return jsonify({'status': 'exploration_started'})
        
    except Exception as e:
        logger.error(f"Error in start_exploration: {str(e)}")
        return jsonify({'error': 'Failed to start exploration', 'message': str(e)}), 500

@app.route('/robot/stop', methods=['POST'])
def stop_exploration():
    """Stop the exploration process"""
    try:
        state = get_robot_state()
        state['is_running'] = False
        state['waiting_for_image'] = False
        save_robot_state(state)
        logger.info("Exploration stopped")
        return jsonify({'status': 'exploration_stopped'})
        
    except Exception as e:
        logger.error(f"Error in stop_exploration: {str(e)}")
        return jsonify({'error': 'Failed to stop exploration', 'message': str(e)}), 500

@app.route('/robot/position', methods=['POST'])
def update_position():
    """Update robot's current position"""
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json(silent =True) 
        else:
            data = request.form.to_dict()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        x = data.get('x')
        y = data.get('y')
        
        # Convert to int if they're strings
        try:
            x = int(x) if x is not None else None
            y = int(y) if y is not None else None
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid x or y coordinates'}), 400
        
        if x is None or y is None:
            return jsonify({'error': 'Missing x or y coordinates'}), 400
        
        state = get_robot_state()
        state['current_x'] = x
        state['current_y'] = y
        state['waiting_for_image'] = True  # Robot should take image at new position
        save_robot_state(state)
        
        logger.info(f"Position updated to ({x}, {y}) - waiting for image")
        return jsonify({'status': 'position_updated', 'action': 'take_image'})
        
    except Exception as e:
        logger.error(f"Error in update_position: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Failed to update position', 'message': str(e)}), 500

@app.route('/robot/image', methods=['POST'])
def process_image():
    """Process uploaded image from current position"""
    try:
        state = get_robot_state()
        x, y = state['current_x'], state['current_y']
        
        logger.info(f"Processing image for position ({x}, {y})")
        
        # Handle different types of image uploads
        image_data = None
        filename = f"pos_{x}_{y}_{uuid.uuid4().hex[:8]}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Check if it's a file upload
        if 'image' in request.files:
            image = request.files['image']
            if image.filename != '':
                image.save(filepath)
                image_data = True
        # Check if it's raw image data in request body
        elif request.content_type and 'image' in request.content_type.lower():
            with open(filepath, 'wb') as f:
                f.write(request.data)
            image_data = True
        # Check if data is in request.data
        elif request.data:
            with open(filepath, 'wb') as f:
                f.write(request.data)
            image_data = True
        
        if not image_data:
            logger.error("No image data received")
            return jsonify({'error': 'No image provided'}), 400
        
        # Verify file was created and has data
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            logger.error(f"Image file not created or empty: {filepath}")
            return jsonify({'error': 'Failed to save image'}), 500
        
        logger.info(f"Image saved: {filepath} ({os.path.getsize(filepath)} bytes)")
        
        # Detect human with error handling
        try:
            human_detected = detect_human_simple(filepath)
            logger.info(f"Human detection result: {human_detected}")
        except Exception as e:
            logger.error(f"Human detection failed: {str(e)}")
            human_detected = False  # Default to False if detection fails
        
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
        
        new_positions_count = 0
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
                new_positions_count += 1
        
        save_map_data(map_data)
        
        # Update robot state
        state['waiting_for_image'] = False
        save_robot_state(state)
        
        logger.info(f"Image processed successfully. Human detected: {human_detected}, New positions: {new_positions_count}")
        
        return jsonify({
            'status': 'image_processed',
            'human_detected': human_detected,
            'new_positions_added': new_positions_count
        })
        
    except Exception as e:
        logger.error(f"Error in process_image: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Failed to process image', 'message': str(e)}), 500

@app.route('/robot/next_move', methods=['GET'])
def get_next_move():
    """Get next position to move to (DFS)"""
    try:
        state = get_robot_state()
        
        if not state['is_running']:
            return jsonify({'error': 'Robot not running'}), 400
        
        map_data = get_map_data()
        
        if not map_data['exploration_stack']:
            return jsonify({'exploration_complete': True, 'next_move': None})
        
        # Get next position from stack (DFS - LIFO)
        next_position = map_data['exploration_stack'].pop()
        save_map_data(map_data)
        
        logger.info(f"Next move: ({next_position['x']}, {next_position['y']})")
        
        return jsonify({
            'next_move': next_position,
            'remaining_positions': len(map_data['exploration_stack'])
        })
        
    except Exception as e:
        logger.error(f"Error in get_next_move: {str(e)}")
        return jsonify({'error': 'Failed to get next move', 'message': str(e)}), 500

# ===================== DATA ENDPOINTS =====================

@app.route('/data/map', methods=['GET'])
def get_map():
    """Get map data for visualization"""
    try:
        return jsonify(get_map_data())
    except Exception as e:
        logger.error(f"Error in get_map: {str(e)}")
        return jsonify({'error': 'Failed to get map data', 'message': str(e)}), 500

@app.route('/data/robot', methods=['GET'])
def get_robot_data():
    """Get robot state for monitoring"""
    try:
        return jsonify(get_robot_state())
    except Exception as e:
        logger.error(f"Error in get_robot_data: {str(e)}")
        return jsonify({'error': 'Failed to get robot data', 'message': str(e)}), 500

@app.route('/uploads/<path:filename>')
def serve_image(filename):
    """Serve uploaded images"""
    try:
        return send_from_directory(UPLOAD_FOLDER, filename)
    except Exception as e:
        logger.error(f"Error serving image {filename}: {str(e)}")
        return jsonify({'error': 'File not found'}), 404

# ===================== UTILITY ENDPOINTS =====================

@app.route('/reset', methods=['POST'])
def reset_all():
    """Reset all data (for testing)"""
    try:
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
        
        logger.info("All data reset")
        return jsonify({'status': 'all_data_reset'})
        
    except Exception as e:
        logger.error(f"Error in reset_all: {str(e)}")
        return jsonify({'error': 'Failed to reset data', 'message': str(e)}), 500

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': time.time()})

# Custom request handler to increase timeout
class CustomRequestHandler(WSGIRequestHandler):
    timeout = 60  # 60 seconds timeout

if __name__ == '__main__':
    logger.info("Starting Flask server...")
    logger.info(f"Server will run on http://0.0.0.0:8000")
    
    # Use custom request handler with longer timeout
    app.run(
        host='0.0.0.0', 
        port=8000, 
        debug=False,  # Set to False in production
        threaded=True,  # Enable threading for concurrent requests
        request_handler=CustomRequestHandler
    )