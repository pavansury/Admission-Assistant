// stt_module.h - Speech (simulated) capture interface
#ifndef STT_MODULE_H
#define STT_MODULE_H

#include <Arduino.h>

class STTModule {
 public:
  void begin();
  // For now we simulate by reading Serial input
  bool available();
  String readUtterance();
};

#endif // STT_MODULE_H
