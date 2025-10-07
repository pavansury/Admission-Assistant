#ifndef ESP32_AUDIO_IO_H
#define ESP32_AUDIO_IO_H

#include <Arduino.h>

// Configure I2S sample format
#define AUDIO_SAMPLE_RATE   16000
#define AUDIO_SAMPLE_BITS   16
#define AUDIO_CHANNELS      1
#define AUDIO_FRAME_SAMPLES 512

struct AudioBuffer {
  int16_t samples[AUDIO_FRAME_SAMPLES];
  size_t  count = 0; // number of valid samples
};

class AudioIO {
public:
  bool begin(bool enableOutput = true);
  size_t readSamples(AudioBuffer &buf, uint32_t timeoutMs = 20);
  void playSamples(const int16_t *data, size_t count);
  float rms(const AudioBuffer &buf) const;
};

#endif // ESP32_AUDIO_IO_H
