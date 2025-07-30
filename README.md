# Robot Exploration System

A Flask-based web server that coordinates ESP8266 and ESP32-CAM devices for autonomous robot exploration with human detection capabilities and robust obstacle handling.

## Overview

This system implements a Depth-First Search (DFS) exploration algorithm where:
- **ESP8266** controls robot movement and navigation with obstacle avoidance
- **ESP32-CAM** captures images at each position for human detection
- **Flask Server** coordinates the exploration, processes images, and handles blocked positions
- **Web Interface** provides real-time monitoring and mapping visualization

## System Architecture

```
┌─────────────────┐    WiFi     ┌─────────────────┐
│   ESP8266       │◄───────────►│  Flask Server   │
│ (Robot Control) │             │   (app2.py)     │
│ + Ultrasonic    │             │ + Human AI      │
│ + Motors        │             │ + Map Data      │
└─────────────────┘             └─────────────────┘
                                         ▲
                                    WiFi │
                                         ▼
┌─────────────────┐             ┌─────────────────┐
│   ESP32-CAM     │◄───────────►│  Web Interface  │
│ (Camera Module) │             │   (Dashboard)   │
│ + AI Detection  │             │ + Live Status   │
└─────────────────┘             └─────────────────┘
```

## Step-by-Step Process Flow

### Phase 1: System Initialization
```
1. Flask Server starts → Creates data directories → Loads previous state
2. ESP8266 boots → Connects to WiFi → Tests server connectivity
3. ESP32-CAM boots → Initializes camera → Connects to WiFi
4. ESP8266 sends initial position (0,0) → Server receives → Marks as current
5. ESP8266 requests exploration start → Server initializes DFS stack
```

### Phase 2: Exploration Cycle
```
┌─────────────────────────────────────────────────────────────────┐
│                    MAIN EXPLORATION LOOP                        │
└─────────────────────────────────────────────────────────────────┘

ESP8266 → Server: GET /robot/status
                  ↓
Server Response: {
  "is_running": true,
  "needs_image": true,  // If position not explored
  "next_move": {"x": 1, "y": 0}  // If position explored
}
                  ↓
┌─────────────────────────────────────────────────────────────────┐
│ Branch A: NEEDS IMAGE (Current position not explored)           │
└─────────────────────────────────────────────────────────────────┘

ESP8266: "Need to take image at current position"
         ↓
ESP32-CAM → Server: GET /robot/status (checks every 3 seconds)
                    ↓
Server: "needs_image": true for position (x,y)
        ↓
ESP32-CAM: Captures image → Waits 2 seconds for robot stability
           ↓
ESP32-CAM → Server: POST /robot/image + JPEG data
                    ↓
Server: 1. Saves image as pos_x_y_uuid.jpg
        2. Runs human detection AI
        3. Updates map: adds position to visited_positions
        4. Finds adjacent positions (x±1, y±1)
        5. Adds unvisited positions to exploration_stack
        6. Sets waiting_for_image = false
        ↓
Server Response: {
  "status": "image_processed",
  "human_detected": true/false,
  "new_positions_added": 2
}

┌─────────────────────────────────────────────────────────────────┐
│ Branch B: NEXT MOVE (Current position explored)                 │
└─────────────────────────────────────────────────────────────────┘

ESP8266: "Position explored, need next target"
         ↓
Server: 1. Pops position from exploration_stack (DFS - LIFO)
        2. Checks if position is blocked → skips if blocked
        3. Returns next valid position
        ↓
ESP8266: Receives target (targetX, targetY)
         Sets robotState = MOVING_TO_TARGET
         ↓
ESP8266 Movement Process:
1. Calculate path: deltaX = targetX - currentX, deltaY = targetY - currentY
2. If deltaX ≠ 0: Turn to face EAST/WEST → Check obstacle → Move
3. If deltaY ≠ 0: Turn to face NORTH/SOUTH → Check obstacle → Move
4. Update currentX, currentY after successful move
5. Send position update to server
```

### Phase 3: Obstacle Handling
```
┌─────────────────────────────────────────────────────────────────┐
│                    OBSTACLE ENCOUNTERED                         │
└─────────────────────────────────────────────────────────────────┘

ESP8266: Ultrasonic sensor detects obstacle < 15cm
         ↓
ESP8266: robotState = HANDLING_OBSTACLE
         consecutiveObstacles++
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Retry Strategy (consecutiveObstacles < MAX_RETRIES)             │
└─────────────────────────────────────────────────────────────────┘

ESP8266: 1. Back up one cell
         2. Try turning right and checking each direction
         3. If clear path found → Move forward one cell
         4. Update position and continue to target
         ↓
Success: robotState = MOVING_TO_TARGET, consecutiveObstacles = 0
Failure: Try again with delay

┌─────────────────────────────────────────────────────────────────┐
│ Max Retries Reached (Position Permanently Blocked)              │
└─────────────────────────────────────────────────────────────────┘

ESP8266 → Server: POST /robot/blocked_position {"x": targetX, "y": targetY}
                  ↓
Server: 1. Remove position from exploration_stack
        2. Add to visited_positions with blocked=true
        3. Add to blocked_positions list
        4. Filter future exploration to skip blocked positions
        ↓
ESP8266: Reset consecutiveObstacles = 0
         robotState = CHECKING_STATUS
         Request new target (non-blocked position)
```

### Phase 4: Data Flow Examples

#### Successful Movement Example:
```
Time    Device      Action                          Data
0:00    ESP8266     Boot, connect WiFi              → Position (0,0)
0:05    ESP8266     → POST /robot/position          {"x":0,"y":0}
0:06    Server      Update robot state              waiting_for_image=true
0:07    ESP32-CAM   → GET /robot/status             needs_image=true
0:08    ESP32-CAM   Capture image                   → 45KB JPEG
0:10    ESP32-CAM   → POST /robot/image             Binary image data
0:12    Server      Process image + AI detection    human_detected=false
0:13    Server      Add adjacent positions          stack=[{1,0},{0,1},{-1,0},{0,-1}]
0:14    ESP8266     → GET /robot/status             next_move={1,0}
0:15    ESP8266     Turn EAST, move forward         currentX=1, currentY=0
0:18    ESP8266     → POST /robot/position          {"x":1,"y":0}
0:19    ESP32-CAM   → GET /robot/status             needs_image=true
...     (Repeat cycle)
```

#### Obstacle Encounter Example:
```
Time    Device      Action                          Data
2:30    ESP8266     Moving to target (2,0)          Obstacle detected at (2,0)
2:31    ESP8266     robotState = HANDLING_OBSTACLE   consecutiveObstacles=1
2:32    ESP8266     Back up, try right turn         No clear path
2:35    ESP8266     Try again                       consecutiveObstacles=2
2:38    ESP8266     Try again                       consecutiveObstacles=3
2:40    ESP8266     → POST /robot/blocked_position   {"x":2,"y":0,"blocked":true}
2:41    Server      Remove (2,0) from stack         Mark as permanently blocked
2:42    ESP8266     → GET /robot/status             next_move={1,1} (alternative)
2:43    ESP8266     Move to alternative target      Continue exploration
```

## Features

- **Autonomous Navigation**: DFS-based exploration with intelligent pathfinding
- **Obstacle Avoidance**: Multi-strategy obstacle handling with fallback mechanisms
- **Human Detection**: AI-powered human detection in captured images
- **Real-time Monitoring**: Web dashboard with live status and mapping
- **Robust Error Handling**: Comprehensive error recovery and retry mechanisms
- **Data Persistence**: JSON-based state management with blocked position tracking
- **RESTful API**: Clean API for robot communication with obstacle reporting
- **Blocked Position Management**: Automatic filtering of permanently blocked areas

## Prerequisites

### Software Requirements
- Python 3.7+
- Flask
- OpenCV (for human detection)
- ESP8266/ESP32 Arduino IDE setup

### Hardware Requirements
- ESP8266 (NodeMCU/Wemos D1 Mini)
- ESP32-CAM module
- Robot chassis with motors
- Ultrasonic sensor (HC-SR04)
- Motor driver (L298N or similar)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd robot-exploration-system
   ```

2. **Install Python dependencies**
   ```bash
   python3 -m venv myenv
   source myenv/bin/activate
   pip install -r requirements.txt
   ```

3. **Create required directories**
   ```bash
   mkdir uploads data static templates
   ```

4. **Set up the detector module**
   - Ensure you have a `detector/model.py` file with `detect_human_simple()` function
   - This function should take an image path and return True/False for human detection

## Configuration

### Server Configuration
Edit the following variables in `app2.py`:
```python
# Server settings
HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 8000       # Server port
DEBUG = False     # Set to True for development

# File upload settings
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
UPLOAD_FOLDER = 'uploads'
```

### ESP Device Configuration
Update WiFi credentials in both ESP files:
```cpp
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverUrl = "http://YOUR_SERVER_IP:8000";
```

### Robot Movement Calibration
Adjust timing constants in ESP8266 code:
```cpp
const int MOVE_TIME_MS = 800;      // Time to move one grid cell
const int TURN_TIME_MS = 600;      // Time to turn 90 degrees  
const int OBSTACLE_DISTANCE = 15;  // Obstacle detection threshold (cm)
```

## Running the System

### 1. Start the Flask Server
```bash
python app2.py
```

The server will start on `http://0.0.0.0:8000`

### 2. Upload ESP Code
- Flash the improved ESP8266 code to your robot controller
- Flash the improved ESP32-CAM code to your camera module

### 3. Power On Devices
- Power on the ESP8266 robot controller
- Power on the ESP32-CAM module
- Both devices should connect to WiFi and communicate with the server

### 4. Monitor Progress
- Access web dashboard at `http://server-ip:8000`
- Watch console logs for detailed operation flow
- Monitor robot movement and obstacle handling

## API Endpoints

### Robot Control Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/robot/status` | Get current robot status and next move |
| POST | `/robot/start` | Start exploration process |
| POST | `/robot/stop` | Stop exploration process |
| POST | `/robot/position` | Update robot's current position |
| POST | `/robot/image` | Upload image from current position |
| POST | `/robot/blocked_position` | Report permanently blocked position |
| GET | `/robot/next_move` | Get next position to explore |

### Data Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/data/map` | Get exploration map data with statistics |
| GET | `/data/robot` | Get robot state information |
| GET | `/uploads/<filename>` | Serve uploaded images |

### Utility Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Server health check |
| POST | `/reset` | Reset all exploration data |
| GET | `/` | Web dashboard |

## Data Structure

### Robot State (`data/robot_state.json`)
```json
{
  "current_x": 0,
  "current_y": 0,
  "is_running": false,
  "waiting_for_image": false,
  "last_update": 1234567890.123
}
```

### Map Data (`data/map_data.json`)
```json
{
  "visited_positions": [
    {
      "x": 0,
      "y": 0,
      "human_detected": false,
      "blocked": false,
      "image_path": "uploads/pos_0_0_abcd1234.jpg",
      "timestamp": 1234567890.123
    },
    {
      "x": 2,
      "y": 0,
      "human_detected": false,
      "blocked": true,
      "image_path": null,
      "timestamp": 1234567890.456
    }
  ],
  "exploration_stack": [
    {"x": 1, "y": 0},
    {"x": 0, "y": 1}
  ],
  "blocked_positions": [
    {
      "x": 2,
      "y": 0,
      "timestamp": 1234567890.456
    }
  ]
}
```

## Exploration Algorithm

The system uses **Depth-First Search (DFS)** with obstacle avoidance:

1. **Start**: Robot begins at position (0,0)
2. **Image Capture**: Take photo and detect humans
3. **Add Neighbors**: Add unvisited, unblocked adjacent positions to stack
4. **Move**: Navigate to next position on stack (LIFO) with obstacle checking
5. **Handle Obstacles**: Try alternative approaches, mark permanently blocked if needed
6. **Repeat**: Continue until no more accessible positions to explore

### Coordinate System
```
    Y
    ↑
-1,1│ 0,1│ 1,1
────┼────┼────
-1,0│ 0,0│ 1,0  → X
────┼────┼────
-1,-1│0,-1│1,-1
```

### Movement States
- **CHECKING_STATUS**: Requesting next action from server
- **MOVING_TO_TARGET**: Navigating to assigned position
- **HANDLING_OBSTACLE**: Attempting to overcome obstacle
- **WAITING_FOR_IMAGE**: Position reached, waiting for camera processing
- **EXPLORATION_COMPLETE**: All accessible positions explored
- **ERROR_STATE**: System error, attempting recovery

## Troubleshooting

### Common Issues

1. **Robot Freezes When Meeting Obstacles**
   - **Fixed**: New obstacle handling system with retry mechanisms
   - Check ultrasonic sensor connections
   - Verify `OBSTACLE_DISTANCE` threshold is appropriate

2. **Server Crashes on ESP Connection**
   - Check server logs for detailed error messages
   - Ensure all required directories exist
   - Verify detector module is properly installed

3. **ESP Devices Not Connecting**
   - Verify WiFi credentials
   - Check server IP address and port
   - Test network connectivity with ping

4. **Image Upload Failures**
   - Check file size limits (default: 16MB)
   - Verify camera initialization
   - Monitor network stability and timeout settings

5. **Human Detection Not Working**
   - Ensure detector module is properly configured
   - Check image quality and lighting conditions
   - Verify model dependencies are installed

6. **Robot Stuck in Loop**
   - Check for blocked positions in web dashboard
   - Reset system if needed: `curl -X POST http://server-ip:8000/reset`
   - Review exploration stack for invalid positions

### Debug Mode

Enable debug mode for detailed logging:
```python
app.run(host='0.0.0.0', port=8000, debug=True)
```

### Log Analysis

The server provides detailed logging:
- **INFO**: Normal operations and status updates
- **ERROR**: Error conditions with stack traces
- **DEBUG**: Detailed execution flow (when debug=True)

Monitor ESP8266 serial output for movement decisions and obstacle detection.

## Testing

### Manual Testing
1. Use the web dashboard to monitor real-time status
2. Test obstacle handling by placing objects in robot's path
3. Verify blocked position reporting and alternative pathfinding

### API Testing
```bash
# Test server health
curl -X GET http://localhost:8000/health

# Start exploration
curl -X POST http://localhost:8000/robot/start

# Check status
curl -X GET http://localhost:8000/robot/status

# Update position
curl -X POST -H "Content-Type: application/json" \
     -d '{"x":1,"y":0}' http://localhost:8000/robot/position

# Report blocked position
curl -X POST -H "Content-Type: application/json" \
     -d '{"x":2,"y":0,"blocked":true}' http://localhost:8000/robot/blocked_position

# Get map data
curl -X GET http://localhost:8000/data/map
```

## Performance Considerations

- **Memory Usage**: Monitor ESP device memory, especially ESP32-CAM during image capture
- **Network Bandwidth**: Large images may cause timeouts on slow networks
- **Processing Time**: Human detection adds 1-3 seconds processing delay
- **Storage**: Images accumulate in uploads folder (consider cleanup mechanism)
- **Obstacle Handling**: Retry mechanisms add time but improve reliability

## Recent Improvements

### Version 2.0 Features
- ✅ **Robust Obstacle Handling**: Multi-strategy approach with fallback mechanisms
- ✅ **Blocked Position Management**: Automatic tracking and filtering of inaccessible areas
- ✅ **Enhanced Error Recovery**: Comprehensive retry logic with progressive delays
- ✅ **Better State Management**: Improved synchronization between robot and server
- ✅ **Advanced Movement Planning**: Alternative pathfinding around obstacles
- ✅ **Real-time Monitoring**: Enhanced web dashboard with obstacle visualization

## Security Notes

- Server runs without authentication (suitable for local networks only)
- No input sanitization for production use
- File uploads are unrestricted by type
- Consider adding rate limiting for production deployment

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Test obstacle handling scenarios
5. Submit a pull request with detailed description

## License

This project is provided as-is for educational and research purposes.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review server logs and ESP serial output
3. Test with the provided API endpoints
4. Monitor the web dashboard for system status
5. Create an issue with detailed logs and setup information