
#!/bin/bash
# Simulate ESP32-CAM uploading an image
echo "Uploading dummy image from ESP32-CAM..."
curl -X POST http://localhost:8000/upload -F "x=1" -F "y=2" -F "image=@dummy.jpg"
