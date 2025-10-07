#!/usr/bin/env python3
"""Admission Assistant - Python Simulation

Enhanced version: integrates a trained intent classification model (scikit-learn
pipeline) if available; otherwise falls back to keyword matching.

Features:
 - Loads canonical FAQ data from CSV (for complete category coverage) with JSON fallback
 - Uses trained model artifact at ml_model/training/artifacts/intent_pipeline.joblib
 - Provides top-N intent suggestions when confidence is low
 - Conversation logging with intent metadata
"""

from __future__ import annotations
import json, csv, os, re, joblib, math, pathlib, argparse, sys, contextlib, io
from datetime import datetime
from typing import List, Dict, Optional

import pandas as pd  # still used for quick inspection / potential future analytics

# --- Optional Audio Dependencies (STT / TTS) ---------------------------------
try:
    import speech_recognition as sr  # Speech-to-text
    STT_AVAILABLE = True
except Exception:  # broad import guard
    sr = None
    STT_AVAILABLE = False

try:
    import pyttsx3  # Text-to-speech offline
    TTS_AVAILABLE = True
except Exception:
    pyttsx3 = None
    TTS_AVAILABLE = False

ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = ROOT
DATA_DIR = PROJECT_ROOT / 'database'
MODEL_BUNDLE_PATH = PROJECT_ROOT / 'ml_model' / 'training' / 'artifacts' / 'intent_pipeline.joblib'
FAQ_JSON_PATH = DATA_DIR / 'faq.json'
FAQ_CSV_PATH = DATA_DIR / 'faq.csv'

MIN_CONFIDENCE = 0.25
SUGGESTION_GAP = 0.08

# Rule-based keyword sets to override ML when clear intent words are present
RULE_KEYWORDS = {
    'deadline': [
        'deadline', 'deadlines', 'last date', 'last-day', 'last day', 'closing date', 'submission deadline'
    ],
    'fee': [
        'fee', 'fees', 'application fee', 'cost to apply', 'cost of application', 'price to apply', 'payment', 'charge'
    ],
    'process': [
        'process', 'application process', 'apply', 'how do i apply', 'steps to apply', 'procedure', 'application steps'
    ],
    'documents': [
        'documents', 'document', 'papers', 'certificates', 'required documents', 'needed documents'
    ],
    'financial_aid': [
        'financial aid', 'scholarship', 'scholarships', 'aid', 'grant'
    ],
    'programs': [
        'programs', 'courses', 'majors', 'degrees'
    ],
    'schedule': [
        'schedule', 'when do classes start', 'start of classes', 'semester start', 'classes start'
    ],
    'requirements': [
        'requirements', 'eligibility', 'criteria', 'requirement'
    ]
}

class AdmissionAssistant:
    def __init__(self):
        self.model_bundle = self._load_model_bundle()
        self.pipeline = None
        self.labels: List[str] = []
        if self.model_bundle:
            self.pipeline = self.model_bundle["pipeline"]
            self.labels = self.model_bundle["labels"]
        self.faq_records = self._load_faq_records()
        self.category_to_answer = self._build_category_answer_map()
        self.conversation_log: List[Dict] = []
        # Initialize TTS engine lazily
        self._tts_engine = None

    # --------------------------- Audio (TTS) ------------------------------- #
    def _ensure_tts(self):
        if not TTS_AVAILABLE:
            return False
        if self._tts_engine is None:
            try:
                self._tts_engine = pyttsx3.init()
                # Slightly slower rate for clarity
                rate = self._tts_engine.getProperty('rate')
                self._tts_engine.setProperty('rate', int(rate * 0.9))
            except Exception:
                self._tts_engine = None
        return self._tts_engine is not None

    def speak(self, text: str):
        if self._ensure_tts():
            try:
                self._tts_engine.say(text)
                self._tts_engine.runAndWait()
            except Exception:
                pass  # Fail silently if audio device not available

    # --------------------------- Audio (STT) ------------------------------- #
    def listen(self, timeout: float = 5.0, phrase_time_limit: float = 12.0, quiet: bool = False) -> Optional[str]:
        if not STT_AVAILABLE:
            return None
        recognizer = sr.Recognizer()
        try:
            stderr_backup = sys.stderr
            null_f = None
            if quiet:
                try:
                    null_f = open(os.devnull, 'w')
                    sys.stderr = null_f  # suppress ALSA / JACK noise
                except Exception:
                    pass
            with sr.Microphone() as source:
                print("🎤 (Listening... speak now)")
                recognizer.adjust_for_ambient_noise(source, duration=0.6)
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            if quiet and null_f:
                sys.stderr = stderr_backup
                null_f.close()
            try:
                text = recognizer.recognize_google(audio)
                print(f"📝 (You said): {text}")
                return text
            except sr.UnknownValueError:
                print("⚠️  (Could not understand audio)")
            except sr.RequestError as e:
                print(f"⚠️  (STT request error: {e})")
        except Exception as e:
            print(f"⚠️  (Microphone error: {e})")
            # Restore stderr if suppressed
            try:
                sys.stderr = stderr_backup
            except Exception:
                pass
        return None

    def _load_model_bundle(self):
        if MODEL_BUNDLE_PATH.exists():
            try:
                bundle = joblib.load(MODEL_BUNDLE_PATH)
                print(f"[Model] Loaded intent pipeline with {len(bundle['labels'])} labels.")
                return bundle
            except Exception as e:
                print(f"[Model] Failed to load model bundle: {e}")
        else:
            print("[Model] No trained model found; using keyword fallback.")
        return None

    def _load_faq_records(self) -> List[Dict]:
        records: List[Dict] = []
        if FAQ_CSV_PATH.exists():
            try:
                with open(FAQ_CSV_PATH, newline='', encoding='utf-8') as f:
                    r = csv.DictReader(f)
                    for row in r:
                        records.append({
                            'question': row['question'].strip(),
                            'answer': row['answer'].strip(),
                            'category': row['category'].strip()
                        })
            except Exception as e:
                print(f"[Data] Error reading CSV: {e}")
        if not records and FAQ_JSON_PATH.exists():
            try:
                with open(FAQ_JSON_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    records = data.get('faqs', [])
            except Exception as e:
                print(f"[Data] Error reading JSON: {e}")
        if not records:
            print("[Data] No FAQ source found; system responses limited.")
        return records

    def _build_category_answer_map(self) -> Dict[str, str]:
        mapping = {}
        for rec in self.faq_records:
            cat = rec.get('category')
            if cat and cat not in mapping:
                mapping[cat] = rec.get('answer', '')
        return mapping

    def _classify(self, text: str):
        if not self.pipeline:
            return None
        try:
            probs = None
            if hasattr(self.pipeline, 'predict_proba'):
                probs = self.pipeline.predict_proba([text])[0]
            preds = self.pipeline.predict([text])
            label_idx = preds[0]
            label = self.labels[label_idx]
            confidence = float(probs[label_idx]) if probs is not None else 1.0
            ranked = []
            if probs is not None:
                for i, p in sorted(enumerate(probs), key=lambda x: x[1], reverse=True):
                    ranked.append((self.labels[i], float(p)))
            return {'label': label, 'confidence': confidence, 'ranked': ranked}
        except Exception as e:
            print(f"[Inference] Error during classification: {e}")
            return None

    def process_query(self, user_input: str):
        original = user_input
        user_input = user_input.strip()
        lower = user_input.lower()
        entry = {
            'timestamp': datetime.now().isoformat(),
            'user_query': original,
            'response': None,
            'intent': None,
            'confidence': None
        }
        if not user_input:
            response = "Please ask me something about admissions (e.g., requirements, deadlines, fees)."
            entry['response'] = response
            self.conversation_log.append(entry)
            return response
        # Rule-based override BEFORE model
        rule_intent = self._rule_based_intent(lower)
        model_out = None
        if rule_intent:
            model_out = {'label': rule_intent, 'confidence': 1.0, 'ranked': [(rule_intent, 1.0)]}
        else:
            model_out = self._classify(lower)
        suggestions = ''
        if model_out:
            entry['intent'] = model_out['label']
            entry['confidence'] = model_out['confidence']
            top_label = model_out['label']
            conf = model_out['confidence']
            answer = self.category_to_answer.get(top_label)
            if answer and conf >= MIN_CONFIDENCE:
                response = answer
                ranked = model_out.get('ranked') or []
                if len(ranked) >= 2:
                    second = ranked[1]
                    if (conf - second[1]) < SUGGESTION_GAP and second[1] > 0.10:
                        suggestions = f" (If you meant '{second[0].replace('_',' ')}', ask again specifying that.)"
                        response += suggestions
            else:
                response = self.get_default_response(lower)
        else:
            response = self._legacy_keyword_match(lower)
        entry['response'] = response
        self.conversation_log.append(entry)
        return response

    def _legacy_keyword_match(self, user_input: str):
        best_match = None
        max_matches = 0
        for faq in self.faq_records:
            keywords = faq.get('keywords') or re.findall(r"[a-zA-Z]+", faq.get('question','').lower())
            matches = sum(1 for kw in keywords if kw.lower() in user_input)
            if matches > max_matches:
                max_matches = matches
                best_match = faq
        if best_match and max_matches > 0:
            return best_match.get('answer', '')
        return self.get_default_response(user_input)

    def _rule_based_intent(self, text: str) -> Optional[str]:
        """Return an intent if exactly one category's keyword set matches or one clearly dominates."""
        hit_counts = {}
        for cat, kws in RULE_KEYWORDS.items():
            count = 0
            for kw in kws:
                if kw in text:
                    count += 1
            if count > 0:
                hit_counts[cat] = count
        if not hit_counts:
            return None
        # Sort by count
        ranked = sorted(hit_counts.items(), key=lambda x: x[1], reverse=True)
        if len(ranked) == 1:
            return ranked[0][0]
        # If top clearly greater than second
        if ranked[0][1] >= ranked[1][1] + 1:
            return ranked[0][0]
        # Ambiguous
        return None
    
    def get_default_response(self, user_input: str):
        """Provide default responses for unmatched queries"""
        greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon']
        
        if any(greeting in user_input for greeting in greetings):
            return "Hello! I'm your admission assistant. I can help you with information about admission requirements, deadlines, fees, application process, and required documents. What would you like to know?"
        
        return "I'm sorry, I didn't find specific information about that. Please ask about admission requirements, deadlines, application fees, application process, or required documents."
    
    def start_conversation(self):
        """Start interactive conversation"""
        print("🎓 Admission Assistant Started")
        print("=" * 50)
        print("Hello! I'm here to help with your admission queries.")
        print("You can ask about:")
        print("• Admission requirements")
        print("• Application deadlines") 
        print("• Application fees")
        print("• Application process")
        print("• Required documents")
        print("• Financial aid")
        print("• Programs")
        print("• Schedule (start of classes)")
        print("\nType 'exit' to quit.\n")
        
        while True:
            try:
                user_input = input("🎤 You: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("🔊 Assistant: Thank you for using Admission Assistant. Good luck with your application!")
                    break
                
                if not user_input:
                    print("🔊 Assistant: Please ask me something about admissions.")
                    continue
                
                response = self.process_query(user_input)
                print(f"🔊 Assistant: {response}\n")
                # Speak response if TTS available
                self.speak(response)
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
    
    def save_conversation_log(self, filename="conversation_log.json"):
        """Save conversation history"""
        with open(filename, 'w') as f:
            json.dump(self.conversation_log, f, indent=2)
        print(f"Conversation log saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description="Admission Assistant Simulator")
    parser.add_argument('--voice', action='store_true', help='Enable voice (STT + TTS) interaction loop')
    parser.add_argument('--stt-only', action='store_true', help='Use microphone input but disable TTS output')
    parser.add_argument('--tts-only', action='store_true', help='Use TTS for responses but keep text input')
    parser.add_argument('--no-log', action='store_true', help='Do not write conversation log file')
    parser.add_argument('--stt-timeout', type=float, default=5.0, help='Seconds to wait for speech start (default 5)')
    parser.add_argument('--stt-phrase-limit', type=float, default=12.0, help='Max seconds per utterance (default 12)')
    parser.add_argument('--quiet-audio', action='store_true', help='Suppress ALSA / JACK stderr noise during capture')
    args = parser.parse_args()

    assistant = AdmissionAssistant()

    if args.voice:
        if not STT_AVAILABLE:
            print("⚠️  STT library not available (SpeechRecognition + PyAudio). Falling back to text mode.")
        else:
            print("🎧 Voice mode enabled. Press Ctrl+C to exit.")
        try:
            while True:
                query = None
                if STT_AVAILABLE:
                    query = assistant.listen(timeout=args.stt_timeout, phrase_time_limit=args.stt_phrase_limit, quiet=args.quiet_audio)
                if not query:
                    # Allow manual fallback
                    user_typed = input("(Type instead or press Enter to retry mic) > ").strip()
                    if user_typed:
                        query = user_typed
                if not query:
                    continue
                if query.lower() in ['exit', 'quit', 'bye']:
                    break
                response = assistant.process_query(query)
                print(f"🔊 Assistant: {response}\n")
                if (args.voice or args.tts_only) and not args.stt_only:
                    assistant.speak(response)
        except KeyboardInterrupt:
            print("\nExiting voice session.")
    else:
        # Text-only conversation
        assistant.start_conversation()

    if assistant.conversation_log and not args.no_log:
        assistant.save_conversation_log()

if __name__ == "__main__":
    main()
