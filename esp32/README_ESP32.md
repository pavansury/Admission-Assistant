# ESP32 Voice Integration (STT + TTS) Roadmap

This directory contains scaffolding to add real speech-to-text (STT) and text-to-speech (TTS) to the Admission Assistant on **ESP32** hardware.

## Architecture Options

### 1. Cloud-Assisted (Recommended for Prototype)
1. ESP32 performs wake / button detection + audio capture (I2S microphone).
2. Streams PCM (or compressed) audio to a lightweight HTTP endpoint.
3. Server performs STT (e.g., Whisper, Vosk, Amazon Transcribe) and returns text.
4. ESP32 sends interpreted text to existing intent logic (or forwards to cloud NLU / Alexa).
5. For TTS, ESP32 requests synthesized audio (e.g., Amazon Polly, Coqui TTS) and streams PCM back for playback via I2S DAC / speaker.

### 2. Alexa Voice Service (AVS) Integration
Use Espressif's `esp-va-sdk` (ESP-IDF based) which handles:
* Authorization (Login With Amazon)
* Audio capture, keyword spotting, barge-in
* Downstream directive handling + media playback

> NOTE: Migrating to AVS requires switching from Arduino build to ESP-IDF. The current repository can coexist by creating an `idf/` subproject that reuses business logic via C modules.

### 3. Mostly Offline (Challenging on ESP32)
Limited by RAM/Flash. Full ASR + TTS locally is generally not feasible without external accelerators. Hybrid approach: local wake word + cloud STT/TTS.

## Files in this Directory
| File | Purpose |
|------|---------|
| `audio_io.h/.cpp` | I2S microphone + speaker init and raw PCM capture/playback utilities |
| `stt_client.h/.cpp` | Buffer management + HTTP streaming of audio chunks to server for STT |
| `tts_client.h/.cpp` | Fetch synthesized audio chunks from server and playback via I2S |
| `README_ESP32.md` | This documentation |

## Hardware Assumptions
* ESP32 DevKitC / similar
* I2S MEMS microphone (e.g., INMP441, SPH0645)
* I2S amplifier DAC (MAX98357A) or external DAC + speaker

## Pin Example (Adjust as Needed)
```
I2S_WS   (LRCK)  -> GPIO 25
I2S_SCK  (BCLK)  -> GPIO 26
I2S_SD   (DOUT)  -> GPIO 22  (microphone data into ESP32)
SPEAKER I2S_SD   -> GPIO 21  (if using separate output channel)
```

## Minimal Flow (Cloud STT)
1. Initialize I2S via `AudioIO.begin()`.
2. On button press or wake word → call `sttClient.beginStream()`.
3. Continuously capture frames with `AudioIO.readSamples()` and push with `sttClient.pushAudio()`.
4. When silence detected or timeout → `sttClient.endStream()` returns recognized text.
5. Run text through existing intent classifier.
6. Request TTS: `ttsClient.requestAndPlay(responseText)`.

## Silence Detection (Simple Heuristic)
Compute short-term RMS or average absolute amplitude. If below threshold for N consecutive windows → assume end of utterance.

## Server Expectation (Example Contract)
```
POST /stt/stream (chunked)  -> {"partial":"..."} or final {"text":"..."}
POST /tts (JSON)             Body: {"text":"..."}  Response: audio/x-pcm 16-bit LE 16kHz
```

## Next Steps
* Implement a small Python FastAPI server for STT/TTS bridging.
* Merge ESP32 state machine with existing `main.ino` logic (or create `main_esp32.ino`).
* Optional: integrate wake-word engine (Porcupine / ESP-SR) before streaming.

---
**Disclaimer:** Alexa AVS requires adherence to Amazon's certification process and use of authorized SDKs. This scaffold does *not* embed Alexa— it prepares your code to send audio/text to a backend that could interface with AVS or other services.
