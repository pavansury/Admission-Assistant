#ifndef ESP32_TTS_CLIENT_H
#define ESP32_TTS_CLIENT_H

#include <Arduino.h>
#include "audio_io.h"

class TTSClient {
public:
  bool begin(const String &endpointUrl);
  bool requestAndPlay(const String &text, AudioIO &audio);
private:
  String m_endpoint;
};

#endif // ESP32_TTS_CLIENT_H
