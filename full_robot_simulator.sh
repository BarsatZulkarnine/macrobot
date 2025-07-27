#!/bin/bash

# Robot Simulator without jq dependency
SERVER="http://172.26.35.251:8000"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Robot state
CURRENT_X=0
CURRENT_Y=0

# Create a minimal valid JPEG
create_dummy_image() {
    echo -n -e '\xFF\xD8\xFF\xE0\x00\x10\x4A\x46\x49\x46\x00\x01\x01\x01\x00\x48\x00\x48\x00\x00\xFF\xDB\x00\x43\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\x09\x09\x08\x0A\x0C\x14\x0D\x0C\x0B\x0B\x0C\x19\x12\x13\x0F\x14\x1D\x1A\x1F\x1E\x1D\x1A\x1C\x1C\x20\x24\x2E\x27\x20\x22\x2C\x23\x1C\x1C\x28\x37\x29\x2C\x30\x31\x34\x34\x34\x1F\x27\x39\x3D\x38\x32\x3C\x2E\x33\x34\x32\xFF\xC0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xFF\xC4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xFF\xC4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xDA\x00\x0C\x03\x01\x00\x02\x11\x03\x11\x00\x3F\x00\xAA\xFF\xD9' > robot_image.jpg
}

# Simple JSON parsing without jq
extract_json_value() {
    local json="$1"
    local key="$2"
    
    # Simple regex to extract values - works for basic cases
    echo "$json" | sed -n "s/.*\"$key\":\s*\"\([^\"]*\)\".*/\1/p" | head -1
    if [[ -z "$(echo "$json" | sed -n "s/.*\"$key\":\s*\"\([^\"]*\)\".*/\1/p" | head -1)" ]]; then
        # Try without quotes (for booleans/numbers)
        echo "$json" | sed -n "s/.*\"$key\":\s*\([^,}]*\).*/\1/p" | head -1
    fi
}

# Logging functions
log_esp8266() {
    echo -e "${BLUE}[ESP8266]${NC} $1"
}

log_esp32cam() {
    echo -e "${GREEN}[ESP32-CAM]${NC} $1"
}

log_server() {
    echo -e "${YELLOW}[SERVER]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Test individual endpoints
test_reset() {
    echo "=== 1. RESET BACKEND ==="
    local response=$(curl -s -X POST "$SERVER/reset")
    echo "Response: $response"
    echo ""
}

test_initial_status() {
    echo "=== 2. CHECK INITIAL STATUS ==="
    local response=$(curl -s "$SERVER/robot/status")
    echo "Response: $response"
    
    local is_running=$(extract_json_value "$response" "is_running")
    local needs_image=$(extract_json_value "$response" "needs_image")
    echo "Parsed - Running: $is_running, Needs Image: $needs_image"
    echo ""
}

test_start_exploration() {
    echo "=== 3. START EXPLORATION ==="
    local response=$(curl -s -X POST "$SERVER/robot/start")
    echo "Response: $response"
    echo ""
}

test_status_after_start() {
    echo "=== 4. CHECK STATUS AFTER START ==="
    local response=$(curl -s "$SERVER/robot/status")
    echo "Response: $response"
    
    local is_running=$(extract_json_value "$response" "is_running")
    local needs_image=$(extract_json_value "$response" "needs_image")
    echo "Parsed - Running: $is_running, Needs Image: $needs_image"
    echo ""
}

test_set_position() {
    local x=$1
    local y=$2
    echo "=== 5. SET POSITION TO ($x,$y) ==="
    local response=$(curl -s -X POST -H "Content-Type: application/json" \
                    -d "{\"x\":$x,\"y\":$y}" \
                    "$SERVER/robot/position")
    echo "Response: $response"
    CURRENT_X=$x
    CURRENT_Y=$y
    echo ""
}

test_upload_image() {
    echo "=== 6. UPLOAD IMAGE AT ($CURRENT_X,$CURRENT_Y) ==="
    local response=$(curl -s -X POST -H "Content-Type: image/jpeg" \
                    --data-binary @robot_image.jpg \
                    "$SERVER/robot/image")
    echo "Response: $response"
    
    local human_detected=$(extract_json_value "$response" "human_detected")
    if [[ "$human_detected" == "true" ]]; then
        echo "🚨 HUMAN DETECTED!"
    elif [[ "$human_detected" == "false" ]]; then
        echo "✅ No human detected"
    fi
    echo ""
}

test_status_after_image() {
    echo "=== 7. CHECK STATUS AFTER IMAGE ==="
    local response=$(curl -s "$SERVER/robot/status")
    echo "Response: $response"
    
    # Check if there's a next move
    if echo "$response" | grep -q "next_move"; then
        echo "✅ Next move available in response"
    else
        echo "❌ No next move found"
    fi
    echo ""
}

test_get_next_move() {
    echo "=== 8. GET NEXT MOVE ==="
    local response=$(curl -s "$SERVER/robot/next_move")
    echo "Response: $response"
    
    # Extract coordinates if available
    if echo "$response" | grep -q "next_move"; then
        echo "📍 Next move found in response"
    else
        echo "🏁 No more moves or exploration complete"
    fi
    echo ""
}

test_move_to_new_position() {
    echo "=== 9. MOVE TO NEW POSITION (1,0) ==="
    test_set_position 1 0
}

test_upload_second_image() {
    echo "=== 10. UPLOAD IMAGE AT NEW POSITION ==="
    test_upload_image
}

test_get_map_data() {
    echo "=== 11. GET MAP DATA ==="
    local response=$(curl -s "$SERVER/data/map")
    echo "Response: $response"
    
    # Count visited positions
    local position_count=$(echo "$response" | grep -o '"x":' | wc -l)
    echo "Found $position_count visited positions"
    echo ""
}

test_get_robot_data() {
    echo "=== 12. GET ROBOT DATA ==="
    local response=$(curl -s "$SERVER/data/robot")
    echo "Response: $response"
    echo ""
}

test_stop_exploration() {
    echo "=== 13. STOP EXPLORATION ==="
    local response=$(curl -s -X POST "$SERVER/robot/stop")
    echo "Response: $response"
    echo ""
}

# Full simulation without jq
run_full_simulation() {
    echo "🤖 Starting Full Robot Simulation"
    echo "=================================="
    echo "Server: $SERVER"
    echo ""
    
    # Create dummy image
    create_dummy_image
    
    # Run all tests in sequence
    test_reset
    sleep 1
    
    test_initial_status
    sleep 1
    
    test_start_exploration
    sleep 1
    
    test_status_after_start
    sleep 1
    
    test_set_position 0 0
    sleep 1
    
    test_upload_image
    sleep 2  # Wait for processing
    
    test_status_after_image
    sleep 1
    
    test_get_next_move
    sleep 1
    
    test_move_to_new_position
    sleep 1
    
    test_upload_second_image
    sleep 2  # Wait for processing
    
    test_get_map_data
    sleep 1
    
    test_get_robot_data
    sleep 1
    
    # Continue exploration loop
    echo "=== CONTINUING EXPLORATION ==="
    for i in {1..5}; do
        echo "--- Exploration Step $i ---"
        
        # Check status
        local status_response=$(curl -s "$SERVER/robot/status")
        echo "Status: $status_response"
        
        # Check if exploration is complete
        if echo "$status_response" | grep -q "exploration_complete.*true"; then
            echo "🎉 Exploration completed!"
            break
        fi
        
        # Check if next move is available
        if echo "$status_response" | grep -q "next_move"; then
            echo "📍 Next move available, checking..."
            local next_response=$(curl -s "$SERVER/robot/next_move")
            echo "Next move: $next_response"
            
            # For simplicity, just move to a few more positions
            case $i in
                1) test_set_position 0 1 ;;
                2) test_set_position -1 0 ;;
                3) test_set_position 0 -1 ;;
                4) test_set_position 2 0 ;;
                *) echo "Continuing exploration..." ;;
            esac
            
            test_upload_image
        else
            echo "🏁 No more moves available"
            break
        fi
        
        sleep 2
    done
    
    test_stop_exploration
    
    echo ""
    echo "=== FINAL RESULTS ==="
    test_get_map_data
    test_get_robot_data
    
    # Cleanup
    rm -f robot_image.jpg
    
    echo ""
    echo "🏁 Simulation completed!"
}

# Quick connectivity test
test_connectivity() {
    echo "🔌 Testing server connectivity..."
    if curl -s --connect-timeout 5 "$SERVER/robot/status" > /dev/null; then
        echo "✅ Server is reachable"
        return 0
    else
        echo "❌ Cannot reach server at $SERVER"
        return 1
    fi
}

# Main menu
main() {
    if ! test_connectivity; then
        echo "Please check your server URL and try again."
        exit 1
    fi
    
    echo ""
    echo "Choose test mode:"
    echo "1. Full simulation (recommended)"
    echo "2. Step by step (manual)"
    echo "3. Quick connectivity test"
    read -p "Enter choice [1-3]: " choice
    
    case $choice in
        1)
            run_full_simulation
            ;;
        2)
            echo "Manual testing mode"
            echo "Run individual functions:"
            echo "test_reset, test_initial_status, test_start_exploration, etc."
            ;;
        3)
            echo "Quick test:"
            test_reset
            test_initial_status
            test_start_exploration
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac
}

# Check if running directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi