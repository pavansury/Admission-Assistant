#ifndef ESP32_STT_CLIENT_H
#define ESP32_STT_CLIENT_H

#include <Arduino.h>
#include "audio_io.h"

enum class STTState { Idle, Streaming };

class STTClient {
public:
  bool begin(const String &endpointUrl);
  bool beginStream();
  bool pushAudio(const AudioBuffer &buf); // send chunk
  bool endStream(String &finalText);      // finalize and get result
  STTState state() const { return m_state; }
private:
  String m_endpoint;
  STTState m_state = STTState::Idle;
};

#endif // ESP32_STT_CLIENT_H
