# Backend Testing Curl Commands
# Testing server at 172.26.35.251:8000

# 1. RESET EVERYTHING (Clean slate for testing)
echo "=== 1. Reset all data ==="
curl -X POST http://172.26.35.251:8000/reset
echo -e "\n"

# 2. CHECK INITIAL STATUS
echo "=== 2. Check robot status (should be stopped initially) ==="
curl http://172.26.35.251:8000/robot/status | jq
echo -e "\n"

# 3. START EXPLORATION
echo "=== 3. Start exploration ==="
curl -X POST http://172.26.35.251:8000/robot/start
echo -e "\n"

# 4. CHECK STATUS AFTER START
echo "=== 4. Check status after start (should show needs_image=true) ==="
curl http://172.26.35.251:8000/robot/status | jq
echo -e "\n"

# 5. SIMULATE ROBOT AT STARTING POSITION (0,0)
echo "=== 5. Update position to (0,0) ==="
curl -X POST -H "Content-Type: application/json" \
     -d '{"x":0,"y":0}' \
     http://192.168.0.111:8000/robot/position
echo -e "\n"

# 6. SIMULATE IMAGE UPLOAD AT (0,0) - Using a dummy image
echo "=== 6. Upload dummy image at (0,0) ==="
# Create a small dummy JPEG file
echo -n -e '\xFF\xD8\xFF\xE0\x00\x10\x4A\x46\x49\x46\x00\x01\x01\x01\x00\x48\x00\x48\x00\x00\xFF\xDB\x00\x43\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\x09\x09\x08\x0A\x0C\x14\x0D\x0C\x0B\x0B\x0C\x19\x12\x13\x0F\x14\x1D\x1A\x1F\x1E\x1D\x1A\x1C\x1C\x20\x24\x2E\x27\x20\x22\x2C\x23\x1C\x1C\x28\x37\x29\x2C\x30\x31\x34\x34\x34\x1F\x27\x39\x3D\x38\x32\x3C\x2E\x33\x34\x32\xFF\xC0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xFF\xC4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xFF\xC4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xDA\x00\x0C\x03\x01\x00\x02\x11\x03\x11\x00\x3F\x00\xAA\xFF\xD9' > dummy.jpg
curl -X POST -H "Content-Type: image/jpeg" \
     --data-binary @dummy.jpg \
     http://192.168.0.111:8000/robot/image
echo -e "\n"

# 7. CHECK STATUS AFTER IMAGE (should suggest next move)
echo "=== 7. Check status after image processing ==="
curl http://192.168.0.111:8000/robot/status | jq
echo -e "\n"

# 8. GET NEXT MOVE
echo "=== 8. Get next move from DFS stack ==="
curl http://192.168.0.111:8000/robot/next_move | jq
echo -e "\n"

# 9. SIMULATE MOVE TO (1,0)
echo "=== 9. Move to (1,0) ==="
curl -X POST -H "Content-Type: application/json" \
     -d '{"x":1,"y":0}' \
     http://192.168.0.111:8000/robot/position
echo -e "\n"

# 10. UPLOAD IMAGE AT (1,0)
echo "=== 10. Upload image at (1,0) ==="
curl -X POST -H "Content-Type: image/jpeg" \
     --data-binary @dummy.jpg \
     http://192.168.0.111:8000/robot/image
echo -e "\n"

# 11. CHECK MAP DATA
echo "=== 11. Check map data ==="
curl http://192.168.0.111:8000/data/map | jq
echo -e "\n"

# 12. CHECK ROBOT DATA
echo "=== 12. Check robot state ==="
curl http://192.168.0.111:8000/data/robot | jq
echo -e "\n"

# 13. SIMULATE MOVE TO (0,1)
echo "=== 13. Move to (0,1) ==="
curl -X POST -H "Content-Type: application/json" \
     -d '{"x":0,"y":1}' \
     http://192.168.0.111:8000/robot/position
echo -e "\n"

# 14. UPLOAD IMAGE AT (0,1)
echo "=== 14. Upload image at (0,1) ==="
curl -X POST -H "Content-Type: image/jpeg" \
     --data-binary @dummy.jpg \
     http://192.168.0.111:8000/robot/image
echo -e "\n"

# 15. CONTINUE EXPLORATION CYCLE
echo "=== 15. Check status for next move ==="
curl http://192.168.0.111:8000/robot/status | jq
echo -e "\n"

# 16. SIMULATE MOVE TO (-1,0)
echo "=== 16. Move to (-1,0) ==="
curl -X POST -H "Content-Type: application/json" \
     -d '{"x":-1,"y":0}' \
     http://192.168.0.111:8000/robot/position
echo -e "\n"

# 17. UPLOAD IMAGE AT (-1,0)
echo "=== 17. Upload image at (-1,0) ==="
curl -X POST -H "Content-Type: image/jpeg" \
     --data-binary @dummy.jpg \
     http://192.168.0.111:8000/robot/image
echo -e "\n"

# 18. SIMULATE MOVE TO (0,-1)
echo "=== 18. Move to (0,-1) ==="
curl -X POST -H "Content-Type: application/json" \
     -d '{"x":0,"y":-1}' \
     http://192.168.0.111:8000/robot/position
echo -e "\n"

# 19. UPLOAD IMAGE AT (0,-1)
echo "=== 19. Upload image at (0,-1) ==="
curl -X POST -H "Content-Type: image/jpeg" \
     --data-binary @dummy.jpg \
     http://192.168.0.111:8000/robot/image
echo -e "\n"

# 20. CHECK FINAL STATUS
echo "=== 20. Final status check (should show exploration complete or more moves) ==="
curl http://192.168.0.111:8000/robot/status | jq
echo -e "\n"

# 21. CHECK FINAL MAP
echo "=== 21. Final map data ==="
curl http://192.168.0.111:8000/data/map | jq
echo -e "\n"

# 22. STOP EXPLORATION
echo "=== 22. Stop exploration ==="
curl -X POST http://192.168.0.111:8000/robot/stop
echo -e "\n"

# 23. CHECK STATUS AFTER STOP
echo "=== 23. Status after stop ==="
curl http://192.168.0.111:8000/robot/status | jq
echo -e "\n"

# Cleanup
rm -f dummy.jpg

echo "=== Testing Complete ==="
echo "Check data/robot_state.json and data/map_data.json files for results"