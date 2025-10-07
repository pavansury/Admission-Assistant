// ml_model.cpp - Lightweight placeholder model for embedded classification
#include "ml_model.h"
#include "config.h"

// Simple keyword tables per category (could move to PROGMEM if needed)
static const char *REQ_WORDS[] = {"requirement", "eligibility", "criteria"};
static const char *DEADLINE_WORDS[] = {"deadline", "last date", "timeline"};
static const char *FEE_WORDS[] = {"fee", "cost", "payment", "charge"};
static const char *PROCESS_WORDS[] = {"apply", "application", "process", "online"};
static const char *DOC_WORDS[] = {"document", "documents", "papers", "certificates"};
static const char *GREETING_WORDS[] = {"hello", "hi", "hey"};

bool AdmissionModel::begin() {
	// Placeholder for real TFLite Micro model initialization
	// In a future iteration: load model from flash and allocate tensors
	if (DEBUG_MODE) {
		Serial.println(F("[ML] Model initialized (stub)"));
	}
	return true;
}

String AdmissionModel::normalize(const String &in) const {
	String out = in; 
	out.toLowerCase();
	return out;
}

static float scoreCategory(const String &text, const char **words, size_t count) {
	float hits = 0;
	for (size_t i = 0; i < count; ++i) {
		if (text.indexOf(words[i]) >= 0) {
			hits += 1.0f;
		}
	}
	if (count == 0) return 0;
	return hits / (float)count; // simple fractional match
}

ClassificationResult AdmissionModel::classify(const String &raw) {
	String text = normalize(raw);
	ClassificationResult best{"unknown", 0.0f};

	struct Cat { const char *name; const char **words; size_t n; };
	const Cat cats[] = {
		{"requirements", REQ_WORDS, sizeof(REQ_WORDS)/sizeof(char*)},
		{"deadline", DEADLINE_WORDS, sizeof(DEADLINE_WORDS)/sizeof(char*)},
		{"fee", FEE_WORDS, sizeof(FEE_WORDS)/sizeof(char*)},
		{"process", PROCESS_WORDS, sizeof(PROCESS_WORDS)/sizeof(char*)},
		{"documents", DOC_WORDS, sizeof(DOC_WORDS)/sizeof(char*)},
		{"greeting", GREETING_WORDS, sizeof(GREETING_WORDS)/sizeof(char*)}
	};

	for (auto &c : cats) {
		float s = scoreCategory(text, c.words, c.n);
		if (s > best.confidence) {
			best.category = c.name;
			best.confidence = s;
		}
	}

	// Apply a simple threshold
	if (best.confidence < 0.15f) {
		best.category = "unknown";
	}
	return best;
}

