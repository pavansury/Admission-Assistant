#include "stt_client.h"

#ifdef ARDUINO_ARCH_ESP32
#include <WiFi.h>
#include <HTTPClient.h>

bool STTClient::begin(const String &endpointUrl) {
  m_endpoint = endpointUrl;
  return true;
}

bool STTClient::beginStream() {
  if (m_state != STTState::Idle) return false;
  // Could initiate a session via POST /stt/start to get a session id
  m_state = STTState::Streaming;
  return true;
}

bool STTClient::pushAudio(const AudioBuffer &buf) {
  if (m_state != STTState::Streaming) return false;
  // Simplified: send each buffer independently (can be optimized to chunked transfer)
  HTTPClient http;
  http.begin(m_endpoint + "/stt/chunk");
  http.addHeader("Content-Type", "application/octet-stream");
  int rc = http.POST((uint8_t*)buf.samples, buf.count * sizeof(int16_t));
  http.end();
  return rc > 0;
}

bool STTClient::endStream(String &finalText) {
  if (m_state != STTState::Streaming) return false;
  HTTPClient http;
  http.begin(m_endpoint + "/stt/finish");
  int rc = http.GET();
  if (rc == 200) {
    finalText = http.getString();
  } else {
    finalText = "";
  }
  http.end();
  m_state = STTState::Idle;
  return !finalText.isEmpty();
}

#else
bool STTClient::begin(const String &) { return false; }
bool STTClient::beginStream() { return false; }
bool STTClient::pushAudio(const AudioBuffer &) { return false; }
bool STTClient::endStream(String &) { return false; }
#endif
