// utils.cpp - Utility implementations
#include "utils.h"

String toLowerCopy(const String &s) {
	String out = s; out.toLowerCase(); return out;
}

void blinkLED(uint8_t ledPin, uint8_t times, uint16_t onMs, uint16_t offMs) {
	for (uint8_t i = 0; i < times; ++i) {
		digitalWrite(ledPin, LOW);
		delay(onMs);
		digitalWrite(ledPin, HIGH);
		delay(offMs);
	}
}

