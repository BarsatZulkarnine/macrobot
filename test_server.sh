#!/bin/bash

# Robot Exploration System - Server Testing Script
# This script tests all server endpoints and simulates ESP device interactions

# Configuration
SERVER_URL="http://localhost:8000"
TEST_IMAGE="test_image.jpg"
TEMP_DIR="/tmp/robot_test"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_TESTS=0

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "PASS")
            echo -e "${GREEN}[PASS]${NC} $message"
            ((TESTS_PASSED++))
            ;;
        "FAIL")
            echo -e "${RED}[FAIL]${NC} $message"
            ((TESTS_FAILED++))
            ;;
        "INFO")
            echo -e "${BLUE}[INFO]${NC} $message"
            ;;
        "WARN")
            echo -e "${YELLOW}[WARN]${NC} $message"
            ;;
    esac
    ((TOTAL_TESTS++))
}

# Function to make HTTP request and check response
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_status=$4
    local description=$5
    
    echo -e "\n${YELLOW}Testing:${NC} $description"
    echo -e "${BLUE}Request:${NC} $method $endpoint"
    
    if [ -n "$data" ]; then
        if [[ $data == @* ]]; then
            # File upload
            response=$(curl -s -w "\n%{http_code}" -X $method "$SERVER_URL$endpoint" -F "image=$data")
        else
            # JSON data
            response=$(curl -s -w "\n%{http_code}" -X $method "$SERVER_URL$endpoint" \
                      -H "Content-Type: application/json" -d "$data")
        fi
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "$SERVER_URL$endpoint")
    fi
    
    # Extract HTTP status code (last line)
    http_code=$(echo "$response" | tail -n1)
    # Extract response body (all but last line)
    response_body=$(echo "$response" | head -n -1)
    
    echo -e "${BLUE}Response Code:${NC} $http_code"
    echo -e "${BLUE}Response Body:${NC} $response_body"
    
    if [ "$http_code" = "$expected_status" ]; then
        print_status "PASS" "$description"
        return 0
    else
        print_status "FAIL" "$description (Expected: $expected_status, Got: $http_code)"
        return 1
    fi
}

# Function to create test image
create_test_image() {
    mkdir -p $TEMP_DIR
    
    # Check if ImageMagick is available
    if command -v convert &> /dev/null; then
        convert -size 640x480 xc:blue -pointsize 30 -fill white \
                -annotate +50+240 "Test Image for Robot" "$TEMP_DIR/$TEST_IMAGE"
        print_status "INFO" "Created test image using ImageMagick"
    elif command -v python3 &> /dev/null; then
        # Create test image using Python PIL
        python3 -c "
from PIL import Image, ImageDraw, ImageFont
import os

# Create a simple test image
img = Image.new('RGB', (640, 480), color='blue')
draw = ImageDraw.Draw(img)

# Add text
try:
    # Try to use a default font
    font = ImageFont.load_default()
    draw.text((50, 240), 'Test Image for Robot', fill='white', font=font)
except:
    # Fallback without font
    draw.text((50, 240), 'Test Image for Robot', fill='white')

# Save the image
img.save('$TEMP_DIR/$TEST_IMAGE', 'JPEG')
print('Test image created successfully')
"
        if [ $? -eq 0 ]; then
            print_status "INFO" "Created test image using Python PIL"
        else
            # Create a minimal dummy file
            echo -e "\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xFF\xDB\x00C\x00" > "$TEMP_DIR/$TEST_IMAGE"
            print_status "WARN" "Created minimal JPEG header as test image"
        fi
    else
        # Create a minimal dummy file
        echo -e "\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xFF\xDB\x00C\x00" > "$TEMP_DIR/$TEST_IMAGE"
        print_status "WARN" "Created minimal JPEG header as test image"
    fi
}

# Function to check server connectivity
check_server() {
    echo -e "\n${YELLOW}=== Server Connectivity Check ===${NC}"
    
    if curl -s --connect-timeout 5 "$SERVER_URL" > /dev/null; then
        print_status "PASS" "Server is reachable at $SERVER_URL"
        return 0
    else
        print_status "FAIL" "Server is not reachable at $SERVER_URL"
        echo -e "${RED}Please ensure the server is running:${NC}"
        echo -e "  python app2.py"
        return 1
    fi
}

# Function to test basic endpoints
test_basic_endpoints() {
    echo -e "\n${YELLOW}=== Basic Endpoint Tests ===${NC}"
    
    # Health check
    test_endpoint "GET" "/health" "" "200" "Health check endpoint"
    
    # Home page
    test_endpoint "GET" "/" "" "200" "Home page access"
    
    # Robot status (initial)
    test_endpoint "GET" "/robot/status" "" "200" "Initial robot status"
    
    # Map data (initial)
    test_endpoint "GET" "/data/map" "" "200" "Initial map data"
    
    # Robot data (initial)
    test_endpoint "GET" "/data/robot" "" "200" "Initial robot data"
}

# Function to test robot control flow
test_robot_control() {
    echo -e "\n${YELLOW}=== Robot Control Flow Tests ===${NC}"
    
    # Reset system first
    test_endpoint "POST" "/reset" "" "200" "Reset system state"
    
    # Start exploration
    test_endpoint "POST" "/robot/start" "" "200" "Start exploration"
    
    # Check status after start
    test_endpoint "GET" "/robot/status" "" "200" "Status after starting exploration"
    
    # Update position
    # Update multiple positions to simulate exploration
    test_endpoint "POST" "/robot/position" '{"x": 1, "y": 0}' "200" "Update robot position to (1,0)"
    test_endpoint "POST" "/robot/position" '{"x": 2, "y": 0}' "200" "Update robot position to (2,0)"
    test_endpoint "POST" "/robot/position" '{"x": 2, "y": 1}' "200" "Update robot position to (2,1)"
    test_endpoint "POST" "/robot/position" '{"x": 1, "y": 1}' "200" "Update robot position to (1,1)"
    test_endpoint "POST" "/robot/position" '{"x": 0, "y": 1}' "200" "Update robot position to (0,1)"
        
    # Check status after position update
    test_endpoint "GET" "/robot/status" "" "200" "Status after position update"
    
    # Get next move
    test_endpoint "GET" "/robot/next_move" "" "200" "Get next move"
    
    # Stop exploration
    test_endpoint "POST" "/robot/stop" "" "200" "Stop exploration"
}

# Function to test image upload
test_image_upload() {
    echo -e "\n${YELLOW}=== Image Upload Tests ===${NC}"
    
    # Create test image first
    create_test_image
    
    if [ -f "$TEMP_DIR/$TEST_IMAGE" ]; then
        # Start exploration first
        test_endpoint "POST" "/robot/start" "" "200" "Start exploration for image test"
        
        # Update position to trigger image need
        test_endpoint "POST" "/robot/position" '{"x": 0, "y": 1}' "200" "Update position for image test"
        
        # Upload test image
        test_endpoint "POST" "/robot/image" "@$TEMP_DIR/$TEST_IMAGE" "200" "Upload test image"
        
        # Test image serving
        # First, let's check what images are available
        response=$(curl -s "$SERVER_URL/data/map")
        if echo "$response" | grep -q "image_path"; then
            # Extract image path from response (basic extraction)
            image_name=$(echo "$response" | grep -o '"image_path":"[^"]*"' | head -1 | cut -d':' -f2 | tr -d '"' | sed 's|uploads/||')
            if [ -n "$image_name" ]; then
                test_endpoint "GET" "/uploads/$image_name" "" "200" "Serve uploaded image"
            else
                print_status "WARN" "Could not extract image name from map data"
            fi
        else
            print_status "WARN" "No images found in map data"
        fi
    else
        print_status "FAIL" "Test image creation failed"
    fi
}

# Function to test error conditions
test_error_conditions() {
    echo -e "\n${YELLOW}=== Error Condition Tests ===${NC}"
    
    # Invalid JSON
    test_endpoint "POST" "/robot/position" '{"invalid": json}' "400" "Invalid JSON handling"
    
    # Missing required fields
    test_endpoint "POST" "/robot/position" '{"x": 1}' "400" "Missing required field (y coordinate)"
    
    # Invalid coordinates
    test_endpoint "POST" "/robot/position" '{"x": "invalid", "y": 0}' "400" "Invalid coordinate type"
    
    # Non-existent image
    test_endpoint "GET" "/uploads/nonexistent.jpg" "" "404" "Non-existent image request"
    
    # Get next move without running
    test_endpoint "POST" "/robot/stop" "" "200" "Stop robot first"
    test_endpoint "GET" "/robot/next_move" "" "400" "Get next move when not running"
}

# Function to simulate ESP device interactions
simulate_esp_devices() {
    echo -e "\n${YELLOW}=== ESP Device Simulation ===${NC}"
    
    print_status "INFO" "Simulating ESP8266 and ESP32-CAM interaction..."
    
    # Reset and start fresh
    test_endpoint "POST" "/reset" "" "200" "Reset for ESP simulation"
    
    # ESP8266: Start exploration
    test_endpoint "POST" "/robot/start" "" "200" "[ESP8266] Start exploration"
    
    # ESP8266: Check initial status
    test_endpoint "GET" "/robot/status" "" "200" "[ESP8266] Check initial status"
    
    # ESP8266: Update position to (0,0)
    test_endpoint "POST" "/robot/position" '{"x": 0, "y": 0}' "200" "[ESP8266] Update to starting position"
    
    # ESP32-CAM: Check if image is needed
    response=$(curl -s "$SERVER_URL/robot/status")
    if echo "$response" | grep -q '"needs_image":true'; then
        print_status "PASS" "[ESP32-CAM] Image needed detected"
        
        # ESP32-CAM: Upload image
        if [ -f "$TEMP_DIR/$TEST_IMAGE" ]; then
            test_endpoint "POST" "/robot/image" "@$TEMP_DIR/$TEST_IMAGE" "200" "[ESP32-CAM] Upload image"
        fi
    else
        print_status "INFO" "[ESP32-CAM] No image needed at current position"
    fi
    
    # ESP8266: Check for next move
    test_endpoint "GET" "/robot/status" "" "200" "[ESP8266] Check for next move"
    
    # Simulate moving to next position
    test_endpoint "POST" "/robot/position" '{"x": 1, "y": 0}' "200" "[ESP8266] Move to (1,0)"
    
    # ESP32-CAM: Upload image for new position
    if [ -f "$TEMP_DIR/$TEST_IMAGE" ]; then
        test_endpoint "POST" "/robot/image" "@$TEMP_DIR/$TEST_IMAGE" "200" "[ESP32-CAM] Upload image for (1,0)"
    fi
    
    # Check final map state
    test_endpoint "GET" "/data/map" "" "200" "Check final exploration map"
}

# Function to test concurrent requests (basic load test)
test_concurrent_requests() {
    echo -e "\n${YELLOW}=== Concurrent Request Test ===${NC}"
    
    print_status "INFO" "Testing server stability with concurrent requests..."
    
    # Create multiple background requests
    for i in {1..5}; do
        curl -s "$SERVER_URL/robot/status" > /dev/null &
        curl -s "$SERVER_URL/data/map" > /dev/null &
    done
    
    # Wait for all background jobs to complete
    wait
    
    # Test if server is still responsive
    if curl -s --connect-timeout 5 "$SERVER_URL/health" > /dev/null; then
        print_status "PASS" "Server remains responsive after concurrent requests"
    else
        print_status "FAIL" "Server became unresponsive after concurrent requests"
    fi
}

# Function to print test summary
print_summary() {
    echo -e "\n${YELLOW}=== Test Summary ===${NC}"
    echo -e "Total Tests: $TOTAL_TESTS"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "\n${GREEN}🎉 All tests passed! Server is working correctly.${NC}"
        exit_code=0
    else
        echo -e "\n${RED}❌ Some tests failed. Please check the server logs and configuration.${NC}"
        exit_code=1
    fi
    
    # Cleanup
    rm -rf $TEMP_DIR
    
    return $exit_code
}

# Main execution
main() {
    echo -e "${BLUE}Robot Exploration System - Server Test Suite${NC}"
    echo -e "${BLUE}=============================================${NC}"
    
    # Check dependencies
    if ! command -v curl &> /dev/null; then
        echo -e "${RED}Error: curl is required but not installed.${NC}"
        exit 1
    fi
    
    # Run test suites
    check_server || exit 1
    
    test_basic_endpoints
    test_robot_control
    test_image_upload
    test_error_conditions
    simulate_esp_devices
    test_concurrent_requests
    
    print_summary
    exit $?
}

# Handle script arguments
case "${1:-}" in
    -h|--help)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Test script for Robot Exploration System server"
        echo ""
        echo "Options:"
        echo "  -h, --help     Show this help message"
        echo "  -s, --server   Set server URL (default: http://localhost:8000)"
        echo ""
        echo "Examples:"
        echo "  $0                                    # Test local server"
        echo "  $0 -s http://192.168.1.100:8000     # Test remote server"
        exit 0
        ;;
    -s|--server)
        if [ -n "$2" ]; then
            SERVER_URL="$2"
            shift 2
        else
            echo -e "${RED}Error: --server requires a URL argument${NC}"
            exit 1
        fi
        ;;
esac

# Run main function
main "$@"