# Robot Exploration System

A Flask-based web server that coordinates ESP8266 and ESP32-CAM devices for autonomous robot exploration with human detection capabilities.

## Overview

This system implements a Depth-First Search (DFS) exploration algorithm where:
- **ESP8266** controls robot movement and navigation
- **ESP32-CAM** captures images at each position for human detection
- **Flask Server** coordinates the exploration and processes images
- **Web Interface** provides real-time monitoring

## System Architecture

```
┌─────────────────┐    WiFi     ┌─────────────────┐
│   ESP8266       │◄───────────►│  Flask Server   │
│ (Robot Control) │             │   (app2.py)     │
└─────────────────┘             └─────────────────┘
                                         ▲
                                    WiFi │
                                         ▼
┌─────────────────┐             ┌─────────────────┐
│   ESP32-CAM     │◄───────────►│  Web Interface  │
│ (Camera Module) │             │   (Dashboard)   │
└─────────────────┘             └─────────────────┘
```

## Features

- **Autonomous Navigation**: DFS-based exploration algorithm
- **Human Detection**: AI-powered human detection in captured images
- **Real-time Monitoring**: Web dashboard for system status
- **Robust Error Handling**: Comprehensive error recovery and retry mechanisms
- **Data Persistence**: JSON-based state management
- **RESTful API**: Clean API for robot communication

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

## API Endpoints

### Robot Control Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/robot/status` | Get current robot status and next move |
| POST | `/robot/start` | Start exploration process |
| POST | `/robot/stop` | Stop exploration process |
| POST | `/robot/position` | Update robot's current position |
| POST | `/robot/image` | Upload image from current position |
| GET | `/robot/next_move` | Get next position to explore |

### Data Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/data/map` | Get exploration map data |
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
      "image_path": "uploads/pos_0_0_abcd1234.jpg",
      "timestamp": 1234567890.123
    }
  ],
  "exploration_stack": [
    {"x": 1, "y": 0},
    {"x": 0, "y": 1}
  ]
}
```

## Exploration Algorithm

The system uses **Depth-First Search (DFS)** for exploration:

1. **Start**: Robot begins at position (0,0)
2. **Image Capture**: Take photo and detect humans
3. **Add Neighbors**: Add unvisited adjacent positions to stack
4. **Move**: Go to next position on stack (LIFO)
5. **Repeat**: Continue until no more positions to explore

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

## Troubleshooting

### Common Issues

1. **Server Crashes on ESP Connection**
   - Check server logs for detailed error messages
   - Ensure all required directories exist
   - Verify detector module is properly installed

2. **ESP Devices Not Connecting**
   - Verify WiFi credentials
   - Check server IP address and port
   - Test network connectivity

3. **Image Upload Failures**
   - Check file size limits (default: 16MB)
   - Verify camera initialization
   - Monitor network stability

4. **Human Detection Not Working**
   - Ensure detector module is properly configured
   - Check image quality and lighting
   - Verify model dependencies are installed

### Debug Mode

Enable debug mode for detailed logging:
```python
app.run(host='0.0.0.0', port=8000, debug=True)
```

### Log Analysis

The server provides detailed logging:
- **INFO**: Normal operations
- **ERROR**: Error conditions with stack traces
- **DEBUG**: Detailed execution flow (when debug=True)

## Testing

### Manual Testing
1. Use the provided test script: `test_server.sh`
2. Monitor server logs during ESP device operations
3. Check web dashboard at `http://server-ip:8000`

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
```

## Performance Considerations

- **Memory Usage**: Monitor ESP device memory, especially ESP32-CAM
- **Network Bandwidth**: Large images may cause timeouts on slow networks
- **Processing Time**: Human detection adds processing delay
- **Storage**: Images accumulate in uploads folder

## Security Notes

- Server runs without authentication (suitable for local networks only)
- No input sanitization for production use
- File uploads are unrestricted by type

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is provided as-is for educational and research purposes.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review server logs
3. Test with the provided test script
4. Create an issue with detailed logs and setup information