#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// Wi-Fi Configuration - Update these to match your ESP8266
const char* ssid = "Khalili";
const char* password = "Khalili007070700";
const char* serverUrl = "http://192.168.0.111:8000";

// Timing
unsigned long lastStatusCheck = 0;
const unsigned long STATUS_CHECK_INTERVAL = 1500; // Check every 1.5 seconds

// Camera state
bool cameraInitialized = false;

void setup() {
  Serial.begin(115200);
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  Serial.println(WiFi.localIP());
  
  // Initialize camera
  if (setupCamera()) {
    cameraInitialized = true;
    Serial.println("Camera initialized successfully");
  } else {
    Serial.println("Camera initialization failed!");
  }
}

void loop() {
  if (!cameraInitialized) {
    Serial.println("Camera not initialized, retrying...");
    if (setupCamera()) {
      cameraInitialized = true;
      Serial.println("Camera initialized successfully");
    }
    delay(5000);
    return;
  }
  
  // Check if robot needs image
  if (millis() - lastStatusCheck > STATUS_CHECK_INTERVAL) {
    checkAndCaptureImage();
    lastStatusCheck = millis();
  }
  
  delay(100);
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
  config.frame_size = FRAMESIZE_VGA;  // Higher quality for better detection
  config.jpeg_quality = 8;           // Lower number = higher quality
  config.fb_count = 1;
  
  // Initialize camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    return false;
  }
  
  // Get camera sensor and adjust settings for better human detection
  sensor_t* s = esp_camera_sensor_get();
  if (s != NULL) {
    s->set_brightness(s, 0);     // -2 to 2
    s->set_contrast(s, 1);       // -2 to 2
    s->set_saturation(s, 0);     // -2 to 2
    s->set_special_effect(s, 0); // 0 to 6 (0-No Effect, 1-Negative, 2-Grayscale, 3-Red Tint, 4-Green Tint, 5-Blue Tint, 6-Sepia)
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
  }
  
  return true;
}

void checkAndCaptureImage() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected");
    return;
  }
  
  // Check robot status to see if image is needed
  WiFiClient client;
  HTTPClient http;
  http.begin(client, String(serverUrl) + "/robot/status");
  
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
        
        // Small delay to ensure robot has stopped moving
        delay(500);
        
        captureAndUploadImage();
      } else {
        // Serial.println("No image needed at this time");
      }
    } else {
      Serial.println("Failed to parse status response");
    }
  } else {
    Serial.printf("Status check failed: %d\n", httpCode);
  }
  
  http.end();
}

void captureAndUploadImage() {
  // Capture image
  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    return;
  }
  
  Serial.printf("Image captured: %d bytes\n", fb->len);
  
  // Upload image
  WiFiClient client;
  HTTPClient http;
  http.begin(client, String(serverUrl) + "/robot/image");
  http.addHeader("Content-Type", "image/jpeg");
  http.setTimeout(15000); // 15 second timeout
  
  int httpCode = http.POST(fb->buf, fb->len);
  
  if (httpCode > 0) {
    String response = http.getString();
    Serial.printf("Image uploaded successfully. Response code: %d\n", httpCode);
    Serial.println("Server response: " + response);
    
    // Parse response to check for human detection
    StaticJsonDocument<256> doc;
    DeserializationError error = deserializeJson(doc, response);
    if (!error && doc.containsKey("human_detected")) {
      bool humanDetected = doc["human_detected"];
      Serial.printf("Human detection result: %s\n", humanDetected ? "DETECTED" : "NOT DETECTED");
    }
  } else {
    Serial.printf("Image upload failed. HTTP code: %d\n", httpCode);
    String error = http.errorToString(httpCode);
    Serial.println("Error: " + error);
  }
  
  http.end();
  esp_camera_fb_return(fb);
}

// Optional: Function to test camera capture without uploading
void testCameraCapture() {
  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    return;
  }
  
  Serial.printf("Test capture successful: %d bytes, %dx%d pixels\n", 
                fb->len, fb->width, fb->height);
  
  esp_camera_fb_return(fb);
}