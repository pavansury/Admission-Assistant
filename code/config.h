#ifndef CONFIG_H
#define CONFIG_H

// System Configuration
#define SYSTEM_NAME "Admission Assistant"
#define VERSION "1.0.0"

// Hardware Pins
#define MIC_PIN A0
#define SPEAKER_PIN 3
#define LED_PIN 13
#define BUTTON_PIN 2

// Audio Configuration
#define SAMPLE_RATE 16000
#define AUDIO_BUFFER_SIZE 512

// Network Configuration
#define WIFI_SSID "your_wifi_ssid"
#define WIFI_PASSWORD "your_wifi_password"

// ML Model Configuration
#define MODEL_INPUT_SIZE 128
#define MODEL_OUTPUT_SIZE 10
#define CONFIDENCE_THRESHOLD 0.7

// System Settings
#define SERIAL_BAUD_RATE 115200
#define DEBUG_MODE true

// Timing Constants
#define RESPONSE_TIMEOUT 5000  // 5 seconds
#define LISTEN_DURATION 3000   // 3 seconds

#endif
