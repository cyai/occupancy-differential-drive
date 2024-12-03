#include <ArduinoWebsockets.h>
#include <Wire.h>
#include <WiFi.h>
#include <L298N.h>
#include <VL53L0X.h>
#include <ArduinoJson.h>

using namespace websockets;

// WiFi credentials
const char* ssid = "Guest";          // Replace with your Wi-Fi SSID
const char* password = "Holiday#2023@";  // Replace with your Wi-Fi password

// WebSocket server configuration
const char* websockets_server_host = "10.1.60.38"; // Replace with your Flask server IP or hostname
const uint16_t websockets_server_port = 8005;     // WebSocket server port
const char* websockets_server_path = "/ws/move";  // WebSocket server path

// Motor pin assignments
const int ENA = 26;  // Right motor enable pin
const int IN1 = 27;  // Right motor input 1
const int IN2 = 14;  // Right motor input 2
const int ENB = 25;  // Left motor enable pin
const int IN3 = 12;  // Left motor input 1
const int IN4 = 13;  // Left motor input 2

// Create motor objects for L298N driver
L298N motor1(ENA, IN1, IN2);  // Right motor
L298N motor2(ENB, IN3, IN4);  // Left motor
VL53L0X sensor;

// WebSocket client
WebsocketsClient client;

// Timer for distance update
unsigned long lastDistanceSent = 0;
const unsigned long distanceUpdateInterval = 500;

void setup() {
    Serial.begin(115200);
    Wire.begin();

    // Initialize motors
    motor1.setSpeed(250);
    motor2.setSpeed(250);

    // Initialize VL53L0X sensor
    // sensor.setTimeout(10500);
    if (!sensor.init()) {
        Serial.println("Failed to detect and initialize VL53L0X");
        while (1) {}
    }
    sensor.startContinuous();

    // Connect to Wi-Fi
    WiFi.begin(ssid, password);
    for (int i = 0; i < 10 && WiFi.status() != WL_CONNECTED; i++) {
        Serial.print(".");
        delay(1000);
    }

    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("Failed to connect to Wi-Fi!");
        return;
    }

    Serial.println("Connected to Wi-Fi!");

    // Connect to WebSocket server
    if (client.connect(websockets_server_host, websockets_server_port, websockets_server_path)) {
        Serial.println("Connected to WebSocket server");
    } else {
        Serial.println("Failed to connect to WebSocket server");
        return;
    }

    // Set up WebSocket message handler
    client.onMessage([&](WebsocketsMessage message) {
        handleMessage(message.data());
    });
}

void loop() {
    // Check for WebSocket messages
    if (client.available()) {
        client.poll();
    }

    // Send distance readings at intervals
    unsigned long currentMillis = millis();
    if (currentMillis - lastDistanceSent >= distanceUpdateInterval) {
        lastDistanceSent = currentMillis;
        sendDistance();
    }
}

// Handle incoming WebSocket messages
void handleMessage(String message) {
    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, message);

    if (error) {
        Serial.print("Failed to parse message: ");
        Serial.println(error.f_str());
        return;
    }

    const char* command = doc["command"];
    if (command) {
        if (strcmp(command, "MOVE_FORWARD") == 0) {
            moveForward();
        } else if (strcmp(command, "MOVE_BACKWARD") == 0) {
            moveBackward();
        } else if (strcmp(command, "TURN_LEFT") == 0) {
            turnLeft();
        } else if (strcmp(command, "TURN_RIGHT") == 0) {
            turnRight();
        } else if (strcmp(command, "STOP") == 0) {
            stopMotors();
        } else {
            Serial.println("Unknown command received");
        }
    }
}

// Send distance readings to WebSocket server
void sendDistance() {
    uint16_t distance = sensor.readRangeContinuousMillimeters();
    if (!sensor.timeoutOccurred()) {
        String message = "{\"event\": \"distance\", \"value\": " + String(distance) + "}";
        client.send(message);
        // Serial.println("Sent distance: " + String(distance) + " mm");
    } else {
        Serial.println("Sensor timeout occurred");
    }
}

// Motor control functions
void moveForward() {
    motor1.forward();
    motor2.forward();
    Serial.println("Moving forward");
}

void moveBackward() {
    motor1.backward();
    motor2.backward();
    Serial.println("Moving backward");
}

void turnLeft() {
    motor1.forward();
    motor2.backward();
    Serial.println("Turning left");
}

void turnRight() {
    motor1.backward();
    motor2.forward();
    Serial.println("Turning right");
}

void stopMotors() {
    motor1.stop();
    motor2.stop();
    Serial.println("Stopping motors");
}
