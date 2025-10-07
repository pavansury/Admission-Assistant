// stt_module.cpp - Simulated speech to text via Serial input
#include "stt_module.h"
#include "config.h"

void STTModule::begin() {
	if (DEBUG_MODE) {
		Serial.println(F("[STT] Module ready (simulated)"));
	}
}

bool STTModule::available() {
	return Serial.available() > 0;
}

String STTModule::readUtterance() {
	if (!Serial.available()) return "";
	String line = Serial.readString();
	line.trim();
	return line;
}

