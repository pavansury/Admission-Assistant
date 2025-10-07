#include "audio_io.h"

#ifdef ARDUINO_ARCH_ESP32
#include <driver/i2s.h>

// Example pins; adjust for your board / wiring
#ifndef I2S_MIC_WS
#define I2S_MIC_WS   25
#endif
#ifndef I2S_MIC_SCK
#define I2S_MIC_SCK  26
#endif
#ifndef I2S_MIC_SD
#define I2S_MIC_SD   22
#endif

#ifndef I2S_SPK_WS
#define I2S_SPK_WS   I2S_MIC_WS
#endif
#ifndef I2S_SPK_SCK
#define I2S_SPK_SCK  I2S_MIC_SCK
#endif
#ifndef I2S_SPK_SD
#define I2S_SPK_SD   21 // speaker data out
#endif

static bool g_outputEnabled = true;

bool AudioIO::begin(bool enableOutput) {
  g_outputEnabled = enableOutput;

  // Config for microphone (RX)
  i2s_config_t i2s_config_rx = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = AUDIO_SAMPLE_RATE,
    .bits_per_sample = (i2s_bits_per_sample_t)AUDIO_SAMPLE_BITS,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = 0,
    .dma_buf_count = 4,
    .dma_buf_len = AUDIO_FRAME_SAMPLES,
    .use_apll = false,
    .tx_desc_auto_clear = false,
    .fixed_mclk = 0
  };
  i2s_pin_config_t pin_config_rx = {
    .bck_io_num = I2S_MIC_SCK,
    .ws_io_num = I2S_MIC_WS,
    .data_out_num = -1,
    .data_in_num = I2S_MIC_SD
  };
  if (i2s_driver_install(I2S_NUM_0, &i2s_config_rx, 0, nullptr) != ESP_OK) return false;
  if (i2s_set_pin(I2S_NUM_0, &pin_config_rx) != ESP_OK) return false;

  if (g_outputEnabled) {
    i2s_config_t i2s_config_tx = i2s_config_rx;
    i2s_config_tx.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX);
    i2s_pin_config_t pin_config_tx = {
      .bck_io_num = I2S_SPK_SCK,
      .ws_io_num = I2S_SPK_WS,
      .data_out_num = I2S_SPK_SD,
      .data_in_num = -1
    };
    if (i2s_driver_install(I2S_NUM_1, &i2s_config_tx, 0, nullptr) != ESP_OK) return false;
    if (i2s_set_pin(I2S_NUM_1, &pin_config_tx) != ESP_OK) return false;
  }

  return true;
}

size_t AudioIO::readSamples(AudioBuffer &buf, uint32_t timeoutMs) {
  size_t bytesRead = 0;
  i2s_read(I2S_NUM_0, (void*)buf.samples, AUDIO_FRAME_SAMPLES * sizeof(int16_t), &bytesRead, timeoutMs / portTICK_PERIOD_MS);
  buf.count = bytesRead / sizeof(int16_t);
  return buf.count;
}

void AudioIO::playSamples(const int16_t *data, size_t count) {
  if (!g_outputEnabled) return;
  size_t written = 0;
  i2s_write(I2S_NUM_1, (const void*)data, count * sizeof(int16_t), &written, portMAX_DELAY);
}

float AudioIO::rms(const AudioBuffer &buf) const {
  if (buf.count == 0) return 0.f;
  double acc = 0.0;
  for (size_t i = 0; i < buf.count; ++i) {
    double s = buf.samples[i];
    acc += s * s;
  }
  return sqrt(acc / (double)buf.count) / 32768.0; // normalized
}

#else
// Non-ESP32 placeholder implementations
bool AudioIO::begin(bool) { return false; }
size_t AudioIO::readSamples(AudioBuffer &, uint32_t) { return 0; }
void AudioIO::playSamples(const int16_t *, size_t) {}
float AudioIO::rms(const AudioBuffer &) const { return 0.f; }
#endif
