// tts_module.cpp - Stub text to speech (prints to Serial)
#include "tts_module.h"
#include "config.h"

static int g_speakerPin = -1;

void TTSModule::begin(int speakerPin) {
	g_speakerPin = speakerPin;
	pinMode(g_speakerPin, OUTPUT);
	if (DEBUG_MODE) {
		Serial.println(F("[TTS] Module initialized (stub)"));
	}
}

void TTSModule::speak(const String &text) {
	// In a real system convert text -> phonemes -> audio synthesis or send to external module
	Serial.println("\n🔊 Response: " + text);
	// Simple activity pulse
	if (g_speakerPin >= 0) {
		digitalWrite(g_speakerPin, HIGH);
		delay(40);
		digitalWrite(g_speakerPin, LOW);
	}
}

