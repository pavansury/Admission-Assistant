// ml_model.h - Stub ML model interface for Admission Assistant
#ifndef ML_MODEL_H
#define ML_MODEL_H

#include <Arduino.h>

struct ClassificationResult {
  String category;
  float confidence; // 0..1
};

class AdmissionModel {
 public:
  bool begin();               // Initialize / load model
  ClassificationResult classify(const String &text); // Classify a query

 private:
  String normalize(const String &in) const;
};

#endif // ML_MODEL_H
