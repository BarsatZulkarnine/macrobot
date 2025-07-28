// ESP32-CAM IMPROVED CODE WITH ROBUST ERROR HANDLING
#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// Wi-Fi Configuration
const char* ssid = "Khalili";
const char* password = "Khalili007070700";
const char* serverUrl = "http://192.168.0.111:8000";

// Timing and retry configuration
unsigned long lastStatusCheck = 0;
const unsigned long STATUS_CHECK_INTERVAL = 3000; // Increased to 3 seconds
const int MAX_RETRIES = 3;
const int UPLOAD_TIMEOUT = 30000; // 30 seconds timeout
const int STATUS_TIMEOUT = 10000;  // 10 seconds timeout
const int WIFI_RETRY_DELAY = 5000; // 5 seconds

// Camera and connection state
bool cameraInitialized = false;
int consecutiveFailures = 0;
const int MAX_CONSECUTIVE_FAILURES = 5;
int wifiReconnectAttempts = 0;
const int MAX_WIFI_RECONNECT_ATTEMPTS = 5;

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== ESP32-CAM Controller Starting ===");
  
  // Connect to WiFi with retry logic
  connectToWiFi();
  
  // Initialize camera
  if (setupCamera()) {
    cameraInitialized = true;
    Serial.println("Camera initialized successfully");
    
    // Test server connectivity
    if (testServerConnectivity()) {
      Serial.println("Server connectivity test passed");
    } else {
      Serial.println("Warning: Server connectivity test failed");
    }
  } else {
    Serial.println("Camera initialization failed!");
  }
}

void loop() {
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected, reconnecting...");
    connectToWiFi();
    if (WiFi.status() != WL_CONNECTED) {
      delay(WIFI_RETRY_DELAY);
      return;
    }
  }
  
  if (!cameraInitialized) {
    Serial.println("Camera not initialized, retrying...");
    if (setupCamera()) {
      cameraInitialized = true;
      Serial.println("Camera initialized successfully");
      consecutiveFailures = 0;
    } else {
      delay(5000);
      return;
    }
  }
  
  // Reset device if too many consecutive failures
  if (consecutiveFailures >= MAX_CONSECUTIVE_FAILURES) {
    Serial.println("Too many consecutive failures, restarting...");
    ESP.restart();
  }
  
  // Check if robot needs image
  if (millis() - lastStatusCheck > STATUS_CHECK_INTERVAL) {
    checkAndCaptureImage();
    lastStatusCheck = millis();
  }
  
  delay(100);
}

void connectToWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(1000);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("WiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Signal strength (RSSI): ");
    Serial.println(WiFi.RSSI());
    consecutiveFailures = 0;
    wifiReconnectAttempts = 0;
  } else {
    Serial.println();
    Serial.println("WiFi connection failed!");
    consecutiveFailures++;
    wifiReconnectAttempts++;
    
    if (wifiReconnectAttempts >= MAX_WIFI_RECONNECT_ATTEMPTS) {
      Serial.println("Max WiFi reconnection attempts reached. Restarting ESP...");
      ESP.restart();
    }
  }
}

bool testServerConnectivity() {
  Serial.println("Testing server connectivity...");
  
  WiFiClient client;
  HTTPClient http;
  http.setTimeout(5000);
  http.begin(client, String(serverUrl) + "/health");
  
  int httpCode = http.GET();
  http.end();
  
  if (httpCode == 200) {
    Serial.println("Server is reachable!");
    return true;
  } else {
    Serial.printf("Server unreachable. HTTP code: %d\n", httpCode);
    return false;
  }
}

bool setupCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = 5;
  config.pin_d1       = 18;
  config.pin_d2       = 19;
  config.pin_d3       = 21;
  config.pin_d4       = 36;
  config.pin_d5       = 39;
  config.pin_d6       = 34;
  config.pin_d7       = 35;
  config.pin_xclk     = 0;
  config.pin_pclk     = 22;
  config.pin_vsync    = 25;
  config.pin_href     = 23;
  config.pin_sscb_sda = 26;
  config.pin_sscb_scl = 27;
  config.pin_pwdn     = 32;
  config.pin_reset    = -1;
  
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  // Optimized settings for better network transmission
  config.frame_size = FRAMESIZE_SVGA;  // Good balance between quality and size
  config.jpeg_quality = 15;            // Reasonable quality (lower number = higher quality)
  config.fb_count = 1;                 // Use single frame buffer
  
  // Initialize camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    return false;
  }
  
  // Get camera sensor and adjust settings for optimal performance
  sensor_t* s = esp_camera_sensor_get();
  if (s != NULL) {
    s->set_brightness(s, 0);     // -2 to 2
    s->set_contrast(s, 1);       // -2 to 2
    s->set_saturation(s, 0);     // -2 to 2
    s->set_special_effect(s, 0); // 0 to 6 (0 - No Effect, 1 - Negative, 2 - Grayscale, 3 - Red Tint, 4 - Green Tint, 5 - Blue Tint, 6 - Sepia)
    s->set_whitebal(s, 1);       // 0 = disable , 1 = enable
    s->set_awb_gain(s, 1);       // 0 = disable , 1 = enable
    s->set_wb_mode(s, 0);        // 0 to 4 - if awb_gain enabled (0 - Auto, 1 - Sunny, 2 - Cloudy, 3 - Office, 4 - Home)
    s->set_exposure_ctrl(s, 1);  // 0 = disable , 1 = enable
    s->set_aec2(s, 0);           // 0 = disable , 1 = enable
    s->set_ae_level(s, 0);       // -2 to 2
    s->set_aec_value(s, 300);    // 0 to 1200
    s->set_gain_ctrl(s, 1);      // 0 = disable , 1 = enable
    s->set_agc_gain(s, 0);       // 0 to 30
    s->set_gainceiling(s, (gainceiling_t)0);  // 0 to 6
    s->set_bpc(s, 0);            // 0 = disable , 1 = enable
    s->set_wpc(s, 1);            // 0 = disable , 1 = enable
    s->set_raw_gma(s, 1);        // 0 = disable , 1 = enable
    s->set_lenc(s, 1);           // 0 = disable , 1 = enable
    s->set_hmirror(s, 0);        // 0 = disable , 1 = enable
    s->set_vflip(s, 0);          // 0 = disable , 1 = enable
    s->set_dcw(s, 1);            // 0 = disable , 1 = enable
    s->set_colorbar(s, 0);       // 0 = disable , 1 = enable
    
    Serial.println("Camera sensor settings applied successfully");
  } else {
    Serial.println("Warning: Could not get camera sensor for configuration");
  }
  
  return true;
}

void checkAndCaptureImage() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected during status check");
    consecutiveFailures++;
    return;
  }
  
  // Check robot status with timeout
  WiFiClient client;
  HTTPClient http;
  http.begin(client, String(serverUrl) + "/robot/status");
  http.setTimeout(STATUS_TIMEOUT);
  
  int httpCode = http.GET();
  if (httpCode == 200) {
    String response = http.getString();
    
    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, response);
    
    if (!error) {
      bool needsImage = doc["needs_image"];
      bool isRunning = doc["is_running"];
      
      if (isRunning && needsImage) {
        int currentX = doc["current_position"]["x"];
        int currentY = doc["current_position"]["y"];
        
        Serial.printf("Image needed at position (%d, %d). Capturing...\n", currentX, currentY);
        
        // Wait longer to ensure robot has stopped moving
        delay(2000);
        
        if (captureAndUploadImageWithRetry()) {
          consecutiveFailures = 0;
          Serial.println("Image capture and upload successful");
        } else {
          consecutiveFailures++;
          Serial.println("Image capture and upload failed");
        }
      } else {
        // Reset failure count on successful status check when no image needed
        consecutiveFailures = 0;
      }
    } else {
      Serial.printf("Failed to parse status response: %s\n", error.c_str());
      consecutiveFailures++;
    }
  } else if (httpCode > 0) {
    Serial.printf("Status check failed with code: %d\n", httpCode);
    consecutiveFailures++;
  } else {
    Serial.printf("Status check connection failed: %s\n", http.errorToString(httpCode).c_str());
    consecutiveFailures++;
  }
  
  http.end();
}

bool captureAndUploadImageWithRetry() {
  for (int attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    Serial.printf("Upload attempt %d/%d\n", attempt, MAX_RETRIES);
    
    if (captureAndUploadImage()) {
      Serial.println("Upload successful!");
      return true;
    }
    
    if (attempt < MAX_RETRIES) {
      Serial.printf("Upload failed, retrying in %d seconds...\n", attempt * 2);
      delay(attempt * 2000); // Progressive delay
    }
  }
  
  Serial.println("All upload attempts failed!");
  return false;
}

bool captureAndUploadImage() {
  // Clear any pending camera operations
  camera_fb_t* fb = nullptr;
  
  // Multiple capture attempts
  for (int captureAttempt = 1; captureAttempt <= 3; captureAttempt++) {
    fb = esp_camera_fb_get();
    if (fb) {
      break;
    }
    Serial.printf("Camera capture attempt %d failed\n", captureAttempt);
    delay(500);
  }
  
  if (!fb) {
    Serial.println("All camera capture attempts failed");
    return false;
  }
  
  Serial.printf("Image captured: %d bytes\n", fb->len);
  
  // Check if image is reasonable size
  if (fb->len < 1000) {
    Serial.println("Image too small, likely corrupted");
    esp_camera_fb_return(fb);
    return false;
  }
  
  // Check if image is too large (adjust quality if needed)
  if (fb->len > 150000) { // 150KB limit
    Serial.printf("Image large (%d bytes), but proceeding...\n", fb->len);
  }
  
  // Upload image with extended timeout
  WiFiClient client;
  HTTPClient http;
  
  // Set longer timeout for image upload
  http.setTimeout(UPLOAD_TIMEOUT);
  http.begin(client, String(serverUrl) + "/robot/image");
  http.addHeader("Content-Type", "image/jpeg");
  http.addHeader("Content-Length", String(fb->len));
  http.addHeader("Connection", "close"); // Ensure connection is closed after request
  
  Serial.println("Starting image upload...");
  unsigned long uploadStart = millis();
  
  int httpCode = http.POST(fb->buf, fb->len);
  
  unsigned long uploadTime = millis() - uploadStart;
  Serial.printf("Upload completed in %lu ms\n", uploadTime);
  
  if (httpCode > 0) {
    Serial.printf("Upload successful! Response code: %d\n", httpCode);
    
    if (httpCode == 200) {
      String response = http.getString();
      Serial.println("Server response: " + response);
      
      // Parse response to check for human detection
      StaticJsonDocument<256> doc;
      DeserializationError error = deserializeJson(doc, response);
      if (!error && doc.containsKey("human_detected")) {
        bool humanDetected = doc["human_detected"];
        Serial.printf("Human detection result: %s\n", humanDetected ? "DETECTED" : "NOT DETECTED");
      }
    }
    
    http.end();
    esp_camera_fb_return(fb);
    return true;
  } else {
    Serial.printf("Image upload failed. HTTP code: %d\n", httpCode);
    String error = http.errorToString(httpCode);
    Serial.println("Error: " + error);
    
    // Log specific error types
    switch (httpCode) {
      case HTTPC_ERROR_CONNECTION_REFUSED:
        Serial.println("Connection refused - check server availability");
        break;
      case HTTPC_ERROR_CONNECTION_LOST:
        Serial.println("Connection lost - network unstable");
        break;
      case HTTPC_ERROR_READ_TIMEOUT:
        Serial.println("Read timeout - server too slow or image too large");
        break;
      case HTTPC_ERROR_CONNECTION_FAILED:
        Serial.println("Connection failed - network issue");
        break;
      default:
        Serial.printf("Unknown error code: %d\n", httpCode);
        break;
    }
    
    http.end();
    esp_camera_fb_return(fb);
    return false;
  }
}

// Memory diagnostic function
void printMemoryInfo() {
  Serial.printf("Free heap: %d bytes\n", ESP.getFreeHeap());
  Serial.printf("Min free heap: %d bytes\n", ESP.getMinFreeHeap());
  Serial.printf("Max alloc heap: %d bytes\n", ESP.getMaxAllocHeap());
}

// Test function for connectivity (can be called manually)
void performConnectivityTest() {
  Serial.println("=== Connectivity Test ===");
  testServerConnectivity();
  printMemoryInfo();
}