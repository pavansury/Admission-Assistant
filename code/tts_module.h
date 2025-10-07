// tts_module.h - Text to Speech stub
#ifndef TTS_MODULE_H
#define TTS_MODULE_H

#include <Arduino.h>

class TTSModule {
 public:
  void begin(int speakerPin);
  void speak(const String &text);
};

#endif // TTS_MODULE_H
