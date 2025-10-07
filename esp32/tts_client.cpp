#include "tts_client.h"

#ifdef ARDUINO_ARCH_ESP32
#include <WiFi.h>
#include <HTTPClient.h>

bool TTSClient::begin(const String &endpointUrl) {
  m_endpoint = endpointUrl;
  return true;
}

bool TTSClient::requestAndPlay(const String &text, AudioIO &audio) {
  HTTPClient http;
  http.begin(m_endpoint + "/tts");
  http.addHeader("Content-Type", "application/json");
  String body = String("{\"text\":\"") + text + "\"}";
  int rc = http.POST(body);
  if (rc != 200) {
    http.end();
    return false;
  }
  // Expect raw PCM 16-bit 16kHz mono in response (this is a simplification)
  WiFiClient * stream = http.getStreamPtr();
  const size_t CHUNK = 512;
  int16_t buf[CHUNK];
  while (http.connected()) {
    size_t avail = stream->available();
    if (!avail) { delay(5); continue; }
    size_t toRead = min(avail, CHUNK * sizeof(int16_t));
    int readBytes = stream->readBytes((char*)buf, toRead);
    if (readBytes <= 0) break;
    audio.playSamples(buf, readBytes / sizeof(int16_t));
  }
  http.end();
  return true;
}

#else
bool TTSClient::begin(const String &) { return false; }
bool TTSClient::requestAndPlay(const String &, AudioIO &) { return false; }
#endif
