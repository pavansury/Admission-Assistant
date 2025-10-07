// utils.h - Utility helpers
#ifndef UTILS_H
#define UTILS_H

#include <Arduino.h>

String toLowerCopy(const String &s);
void blinkLED(uint8_t ledPin, uint8_t times, uint16_t onMs = 150, uint16_t offMs = 150);

#endif // UTILS_H
