
#!/bin/bash
# Simulate ESP8266 sending x/y position to backend
echo "Sending simulated x/y position to backend..."
curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 1, "y": 2}'
