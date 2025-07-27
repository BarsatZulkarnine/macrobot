#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>

// Wi-Fi Configuration
const char* ssid = "Khalili";
const char* password = "Khalili007070700";
const char* serverUrl = "http://192.168.0.111:8000";

// Motor pins
const int motorA1 = 16; // GPIO16 D0
const int motorA2 = 5;  // GPIO5 D1
const int motorB1 = 4;  // GPIO4 D2
const int motorB2 = 0;  // GPIO0 D3

// Ultrasonic sensor pins
const int trigPin = 14; // GPIO14 D5
const int echoPin = 12; // GPIO12 D6

// Robot state
int currentX = 0, currentY = 0;
int targetX = 0, targetY = 0;
enum Direction { NORTH, EAST, SOUTH, WEST };
Direction facing = EAST;  // Start facing right

// Movement timing (adjust based on your robot's speed)
const int MOVE_TIME_MS = 800;    // Time to move one grid cell
const int TURN_TIME_MS = 600;    // Time to turn 90 degrees
const int OBSTACLE_DISTANCE = 15; // Distance threshold for obstacles (cm)

// State machine
enum RobotState { 
  CHECKING_STATUS,
  MOVING_TO_TARGET, 
  WAITING_FOR_IMAGE,
  EXPLORATION_COMPLETE 
};
RobotState robotState = CHECKING_STATUS;

unsigned long lastStatusCheck = 0;
const unsigned long STATUS_CHECK_INTERVAL = 2000; // Check every 2 seconds

void setup() {
  Serial.begin(115200);
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");
  Serial.println(WiFi.localIP());
  
  // Setup motors
  pinMode(motorA1, OUTPUT);
  pinMode(motorA2, OUTPUT);
  pinMode(motorB1, OUTPUT);
  pinMode(motorB2, OUTPUT);
  
  // Setup ultrasonic sensor
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  
  stopMotors();
  
  // Send initial position and start exploration
  sendPositionUpdate(0, 0);
  startExploration();
  
  Serial.println("Robot initialized. Starting DFS exploration...");
}

void loop() {
  switch (robotState) {
    case CHECKING_STATUS:
      if (millis() - lastStatusCheck > STATUS_CHECK_INTERVAL) {
        checkRobotStatus();
        lastStatusCheck = millis();
      }
      break;
      
    case MOVING_TO_TARGET:
      moveToTarget();
      break;
      
    case WAITING_FOR_IMAGE:
      // Wait for ESP32-CAM to process image
      if (millis() - lastStatusCheck > STATUS_CHECK_INTERVAL) {
        checkRobotStatus();
        lastStatusCheck = millis();
      }
      break;
      
    case EXPLORATION_COMPLETE:
      Serial.println("Exploration completed!");
      delay(5000);
      break;
  }
  
  delay(100);
}

void checkRobotStatus() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected");
    return;
  }
  
  WiFiClient client;
  HTTPClient http;
  http.begin(client, String(serverUrl) + "/robot/status");
  
  int httpCode = http.GET();
  if (httpCode == 200) {
    String response = http.getString();
    Serial.println("Status response: " + response);
    
    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, response);
    
    if (!error) {
      bool isRunning = doc["is_running"];
      bool needsImage = doc["needs_image"];
      bool waitingForImage = doc["waiting_for_image"];
      
      if (!isRunning) {
        robotState = EXPLORATION_COMPLETE;
        Serial.println("Robot stopped or exploration complete");
        return;
      }
      
      if (needsImage) {
        robotState = WAITING_FOR_IMAGE;
        Serial.println("Waiting for image to be processed...");
        return;
      }
      
      if (waitingForImage) {
        robotState = WAITING_FOR_IMAGE;
        Serial.println("Backend waiting for image...");
        return;
      }
      
      // Check for next move
      if (doc.containsKey("next_move") && !doc["next_move"].isNull()) {
        targetX = doc["next_move"]["x"];
        targetY = doc["next_move"]["y"];
        Serial.printf("New target: (%d, %d)\n", targetX, targetY);
        robotState = MOVING_TO_TARGET;
      } else if (doc.containsKey("exploration_complete") && doc["exploration_complete"]) {
        robotState = EXPLORATION_COMPLETE;
        Serial.println("Exploration completed!");
      } else {
        robotState = CHECKING_STATUS;
      }
    }
  } else {
    Serial.printf("Status check failed: %d\n", httpCode);
  }
  
  http.end();
}

void moveToTarget() {
  Serial.printf("Moving from (%d,%d) to (%d,%d)\n", currentX, currentY, targetX, targetY);
  
  // Calculate path to target
  int deltaX = targetX - currentX;
  int deltaY = targetY - currentY;
  
  // Move in X direction first, then Y
  if (deltaX != 0) {
    Direction targetDir = (deltaX > 0) ? EAST : WEST;
    turnToDirection(targetDir);
    
    if (canMoveForward()) {
      moveForwardOneCell();
      currentX += (deltaX > 0) ? 1 : -1;
      Serial.printf("Moved to (%d, %d)\n", currentX, currentY);
    } else {
      Serial.println("Obstacle detected! Cannot move forward.");
      // For now, just update status - could implement obstacle avoidance later
      robotState = CHECKING_STATUS;
      return;
    }
  } 
  else if (deltaY != 0) {
    Direction targetDir = (deltaY > 0) ? SOUTH : NORTH;
    turnToDirection(targetDir);
    
    if (canMoveForward()) {
      moveForwardOneCell();
      currentY += (deltaY > 0) ? 1 : -1;
      Serial.printf("Moved to (%d, %d)\n", currentX, currentY);
    } else {
      Serial.println("Obstacle detected! Cannot move forward.");
      robotState = CHECKING_STATUS;
      return;
    }
  }
  
  // Check if we've reached the target
  if (currentX == targetX && currentY == targetY) {
    Serial.println("Reached target position!");
    sendPositionUpdate(currentX, currentY);
    robotState = CHECKING_STATUS;
  }
}

void turnToDirection(Direction targetDir) {
  while (facing != targetDir) {
    turnRight();
    facing = static_cast<Direction>((facing + 1) % 4);
    delay(TURN_TIME_MS);
    stopMotors();
    
    Serial.print("Turned right, now facing: ");
    printDirection(facing);
  }
}

void printDirection(Direction dir) {
  switch (dir) {
    case NORTH: Serial.println("NORTH"); break;
    case EAST:  Serial.println("EAST"); break;
    case SOUTH: Serial.println("SOUTH"); break;
    case WEST:  Serial.println("WEST"); break;
  }
}

bool canMoveForward() {
  int distance = getDistance();
  Serial.printf("Distance ahead: %d cm\n", distance);
  return distance > OBSTACLE_DISTANCE;
}

int getDistance() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  long duration = pulseIn(echoPin, HIGH, 30000);  // 30ms timeout
  int distance = duration * 0.034 / 2;
  
  return (distance == 0) ? 999 : distance;  // Return large value if no echo
}

void moveForwardOneCell() {
  digitalWrite(motorA1, HIGH);
  digitalWrite(motorA2, LOW);
  digitalWrite(motorB1, HIGH);
  digitalWrite(motorB2, LOW);
  
  delay(MOVE_TIME_MS);
  stopMotors();
}

void turnRight() {
  digitalWrite(motorA1, LOW);
  digitalWrite(motorA2, HIGH);
  digitalWrite(motorB1, HIGH);
  digitalWrite(motorB2, LOW);
}

void stopMotors() {
  digitalWrite(motorA1, LOW);
  digitalWrite(motorA2, LOW);
  digitalWrite(motorB1, LOW);
  digitalWrite(motorB2, LOW);
}

void sendPositionUpdate(int x, int y) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected");
    return;
  }
  
  WiFiClient client;
  HTTPClient http;
  http.begin(client, String(serverUrl) + "/robot/position");
  http.addHeader("Content-Type", "application/json");
  
  String jsonPayload = "{\"x\":" + String(x) + ",\"y\":" + String(y) + "}";
  
  int httpCode = http.POST(jsonPayload);
  if (httpCode > 0) {
    String response = http.getString();
    Serial.printf("Position update (%d, %d) - Response: %s\n", x, y, response.c_str());
  } else {
    Serial.printf("Position update failed: %d\n", httpCode);
  }
  
  http.end();
}

void startExploration() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected");
    return;
  }
  
  WiFiClient client;
  HTTPClient http;
  http.begin(client, String(serverUrl) + "/robot/start");
  
  int httpCode = http.POST("");
  if (httpCode > 0) {
    String response = http.getString();
    Serial.printf("Started exploration - Response: %s\n", response.c_str());
  } else {
    Serial.printf("Start exploration failed: %d\n", httpCode);
  }
  
  http.end();
}