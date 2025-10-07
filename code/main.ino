#include "config.h"
#include "ml_model.h"
#include "stt_module.h"
#include "tts_module.h"
#include "utils.h"
#include "faq_responder.h"

// Global variables
bool isListening = false;
bool isProcessing = false;
String currentQuery = "";
String currentResponse = "";

// Modules
AdmissionModel g_model;
STTModule g_stt;
TTSModule g_tts;

// Function declarations
void setupSystem();
void handleUserInput();
void processQuery(String query);
void provideFeedback();
void initializeComponents();

void setup() {
  Serial.begin(SERIAL_BAUD_RATE);
  
  if (DEBUG_MODE) {
    Serial.println("=== Admission Assistant Starting ===");
    Serial.println("System: " + String(SYSTEM_NAME));
    Serial.println("Version: " + String(VERSION));
  }
  
  initializeComponents();
  g_model.begin();
  g_stt.begin();
  g_tts.begin(SPEAKER_PIN);
  setupSystem();
  
  Serial.println("System ready! Say 'Hello' to start...");
}

void loop() {
  handleUserInput();
  
  if (isListening) {
    if (g_stt.available()) {
      currentQuery = g_stt.readUtterance();
      if (currentQuery.length() > 0) {
        isListening = false;
        isProcessing = true;
        processQuery(currentQuery);
      }
    }
  }
  
  if (isProcessing) {
    provideFeedback();
    isProcessing = false;
  }
  
  delay(100);
}

void initializeComponents() {
  // Initialize pins
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(MIC_PIN, INPUT);
  pinMode(SPEAKER_PIN, OUTPUT);
  
  // Turn on status LED
  digitalWrite(LED_PIN, HIGH);
  
  if (DEBUG_MODE) {
    Serial.println("Hardware components initialized");
  }
}

void setupSystem() {
  // Initialize ML model
  Serial.println("Loading ML model...");
  
  // Initialize STT module
  Serial.println("Initializing Speech-to-Text...");
  
  // Initialize TTS module  
  Serial.println("Initializing Text-to-Speech...");
  
  // Load FAQ database
  Serial.println("Loading FAQ database...");
  
  digitalWrite(LED_PIN, LOW);
  delay(500);
  digitalWrite(LED_PIN, HIGH);
}

void handleUserInput() {
  // Check for button press or voice activation
  if (digitalRead(BUTTON_PIN) == LOW && !isListening && !isProcessing) {
    isListening = true;
    Serial.println("\n🎤 Listening... Please ask your question:");
    digitalWrite(LED_PIN, LOW);
  }
}

void processQuery(String query) {
  Serial.println("Processing query: " + query);
  ClassificationResult r = g_model.classify(query);
  currentResponse = faqResponseForCategory(r.category);
  if (DEBUG_MODE) {
    Serial.print(F("[ML] Category: ")); Serial.print(r.category); Serial.print(F(" (confidence=")); Serial.print(r.confidence, 3); Serial.println(F(")"));
  }
}

void provideFeedback() {
  g_tts.speak(currentResponse);
  Serial.println("\nPress the button and ask another question, or type 'exit' to quit.");
  
  // Blink LED to indicate response
  blinkLED(LED_PIN, 3, 200, 200);
  
  currentQuery = "";
  currentResponse = "";
}
