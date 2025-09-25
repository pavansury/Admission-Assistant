#include "config.h"

// Global variables
bool isListening = false;
bool isProcessing = false;
String currentQuery = "";
String currentResponse = "";

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
  setupSystem();
  
  Serial.println("System ready! Say 'Hello' to start...");
}

void loop() {
  handleUserInput();
  
  if (isListening) {
    // Simulate speech-to-text processing
    if (Serial.available()) {
      currentQuery = Serial.readString();
      currentQuery.trim();
      
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
  
  // Simple keyword matching for demo
  query.toLowerCase();
  
  if (query.indexOf("requirement") >= 0 || query.indexOf("eligibility") >= 0) {
    currentResponse = "You need to have completed 12th grade with minimum 75% marks and pass the entrance exam.";
  }
  else if (query.indexOf("deadline") >= 0 || query.indexOf("last date") >= 0) {
    currentResponse = "The admission deadline is March 31st, 2026.";
  }
  else if (query.indexOf("fee") >= 0 || query.indexOf("cost") >= 0) {
    currentResponse = "The application fee is $50 for domestic students and $100 for international students.";
  }
  else if (query.indexOf("apply") >= 0 || query.indexOf("application") >= 0) {
    currentResponse = "Visit our official website, create an account, fill the application form, and submit required documents.";
  }
  else if (query.indexOf("document") >= 0 || query.indexOf("paper") >= 0) {
    currentResponse = "You need transcripts, ID proof, passport photo, and entrance exam scorecard.";
  }
  else if (query.indexOf("hello") >= 0 || query.indexOf("hi") >= 0) {
    currentResponse = "Hello! I'm your admission assistant. How can I help you today?";
  }
  else {
    currentResponse = "I'm sorry, I didn't understand your question. Please ask about admissions, requirements, deadlines, fees, or application process.";
  }
}

void provideFeedback() {
  Serial.println("\n🔊 Response: " + currentResponse);
  Serial.println("\nPress the button and ask another question, or type 'exit' to quit.");
  
  // Blink LED to indicate response
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, LOW);
    delay(200);
    digitalWrite(LED_PIN, HIGH);
    delay(200);
  }
  
  currentQuery = "";
  currentResponse = "";
}
