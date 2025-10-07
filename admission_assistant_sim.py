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
import json, csv, os, re, joblib, math, pathlib, argparse, sys, contextlib, io, time
from datetime import datetime
from typing import List, Dict, Optional

import pandas as pd  # still used for quick inspection / potential future analytics

# --- Optional Audio Dependencies (STT / TTS) ---------------------------------
try:
    import speech_recognition as sr  # type: ignore  # Speech-to-text
    STT_AVAILABLE = True
except Exception:  # broad import guard
    sr = None  # type: ignore
    STT_AVAILABLE = False

try:
    import pyttsx3  # type: ignore  # Text-to-speech offline
    TTS_AVAILABLE = True
except Exception:
    pyttsx3 = None  # type: ignore
    TTS_AVAILABLE = False

# Optional offline STT (Vosk) availability flag
try:
    import vosk  # type: ignore
    VOSK_AVAILABLE = True
except Exception:  # pragma: no cover - optional dep
    vosk = None  # type: ignore
    VOSK_AVAILABLE = False

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
        # TTS configuration store (simple dict)
        self._tts_config = {'rate': None, 'volume': None, 'voice_query': None, 'voice_index': None, 'slow': False}

    # --------------------------- Audio (TTS) ------------------------------- #
    def _ensure_tts(self):
        if not TTS_AVAILABLE:
            return False
        if self._tts_engine is None:
            try:
                self._tts_engine = pyttsx3.init()  # type: ignore[attr-defined]
                # Slightly slower rate for clarity
                rate = self._tts_engine.getProperty('rate')  # type: ignore[assignment]
                self._tts_engine.setProperty('rate', int(rate * 0.9))  # type: ignore[attr-defined]
                # Apply any deferred user config
                self._apply_tts_config()
            except Exception:
                self._tts_engine = None
        return self._tts_engine is not None

    def _apply_tts_config(self):
        if not self._tts_engine:
            return
        cfg = self._tts_config
        try:
            if cfg.get('rate') is not None:
                self._tts_engine.setProperty('rate', int(cfg['rate']))  # type: ignore[attr-defined]
            elif cfg.get('slow'):
                # Apply stronger slowdown if slow flag without explicit rate
                rate = self._tts_engine.getProperty('rate')  # type: ignore[attr-defined]
                self._tts_engine.setProperty('rate', int(rate * 0.8))  # type: ignore[attr-defined]
            if cfg.get('volume') is not None:
                vol = max(0.0, min(1.0, float(cfg['volume'])))
                self._tts_engine.setProperty('volume', vol)  # type: ignore[attr-defined]
            if cfg.get('voice_query'):
                q = cfg['voice_query'].lower()
                voices = self._tts_engine.getProperty('voices')  # type: ignore[attr-defined]
                chosen = None
                for v in voices:
                    # v.id and maybe v.name
                    name = getattr(v, 'name', '') or ''
                    if q in name.lower() or q in (getattr(v, 'id', '') or '').lower():
                        chosen = v.id
                        break
                if chosen:
                    self._tts_engine.setProperty('voice', chosen)  # type: ignore[attr-defined]
            elif cfg.get('voice_index') is not None:
                try:
                    voices = self._tts_engine.getProperty('voices')  # type: ignore[attr-defined]
                    idx = int(cfg['voice_index'])
                    if 0 <= idx < len(voices):
                        self._tts_engine.setProperty('voice', voices[idx].id)  # type: ignore[attr-defined]
                except Exception:
                    pass
        except Exception:
            pass

    def configure_tts(self, rate: Optional[int] = None, volume: Optional[float] = None, voice_query: Optional[str] = None,
                      voice_index: Optional[int] = None, slow: bool = False):
        """Store user TTS configuration and apply if engine already initialized."""
        if rate is not None:
            self._tts_config['rate'] = rate
        if volume is not None:
            self._tts_config['volume'] = volume
        if voice_query:
            self._tts_config['voice_query'] = voice_query
        if voice_index is not None:
            self._tts_config['voice_index'] = voice_index
        if slow:
            self._tts_config['slow'] = True
        # If engine already exists, apply immediately
        if self._tts_engine:
            self._apply_tts_config()

    def list_voices(self):
        if not TTS_AVAILABLE:
            print("[TTS] pyttsx3 not available.")
            return
        try:
            if not self._tts_engine:
                self._tts_engine = pyttsx3.init()  # type: ignore[attr-defined]
            voices = self._tts_engine.getProperty('voices')  # type: ignore[attr-defined]
            print("Available voices:")
            for idx, v in enumerate(voices):
                attrs = []
                for a in ('id','name','languages','age','gender'):
                    val = getattr(v, a, None)
                    if val:
                        attrs.append(f"{a}={val}")
                print(f"  [{idx}] " + ", ".join(attrs))
        except Exception as e:
            print(f"[TTS] Could not list voices: {e}")

    def speak(self, text: str):
        if self._ensure_tts():
            try:
                for chunk in self._tts_chunks(self._prepare_tts_text(text)):
                    self._tts_engine.say(chunk)  # type: ignore[attr-defined]
                self._tts_engine.runAndWait()  # type: ignore[attr-defined]
            except Exception:
                pass  # Fail silently if audio device not available

    def _prepare_tts_text(self, text: str) -> str:
        # Ensure sentence-final punctuation for clarity
        if text and text[-1].isalnum():
            text += '.'
        # Collapse excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        return text

    def _tts_chunks(self, text: str, max_len: int = 180):
        # Split by sentence boundaries first
        sentences = re.split(r'(?<=[.!?]) +', text)
        buf = ''
        for s in sentences:
            if not s:
                continue
            if len(buf) + len(s) + 1 <= max_len:
                buf = (buf + ' ' + s).strip()
            else:
                if buf:
                    yield buf
                buf = s
        if buf:
            yield buf

    # --------------------------- Audio (STT) ------------------------------- #
    def listen(self, timeout: float = 5.0, phrase_time_limit: float = 12.0, quiet: bool = False,
               backend: str = 'auto', retries: int = 0) -> Optional[str]:
        if not STT_AVAILABLE:
            return None
        if not sr:  # runtime guard
            return None
        recognizer = sr.Recognizer()  # type: ignore
        stderr_backup = sys.stderr
        try:
            null_f = None
            if quiet:
                try:
                    null_f = open(os.devnull, 'w')
                    sys.stderr = null_f  # suppress ALSA / JACK noise
                except Exception:
                    pass
            with sr.Microphone() as source:  # type: ignore
                print("🎤 (Listening... speak now)")
                recognizer.adjust_for_ambient_noise(source, duration=0.6)  # type: ignore[arg-type]
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            if quiet and null_f:
                sys.stderr = stderr_backup
                null_f.close()
            # Decide backend order
            if backend == 'google':
                backend_order = ['google']
            elif backend == 'vosk':
                backend_order = ['vosk']
            else:  # auto
                backend_order = ['google', 'vosk'] if VOSK_AVAILABLE else ['google']
            attempt = 0
            while attempt <= retries:
                for b in backend_order:
                    try:
                        if b == 'google':
                            text = recognizer.recognize_google(audio)  # type: ignore[attr-defined]
                        elif b == 'vosk' and VOSK_AVAILABLE:
                            raw = recognizer.recognize_vosk(audio)  # type: ignore[attr-defined]
                            # Vosk returns JSON or plain text depending on SR version
                            try:
                                data = json.loads(raw)
                                text = data.get('text', '').strip()
                            except Exception:
                                text = raw.strip()
                            if not text:
                                raise sr.UnknownValueError()
                        else:
                            continue
                        print(f"📝 (You said): {text}")
                        return text
                    except Exception:  # treat as UnknownValueError
                        if attempt == retries and b == backend_order[-1]:
                            print("⚠️  (Could not understand audio)")
                    # No separate RequestError handling to avoid duplicate broad except
                attempt += 1
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
    parser.add_argument('--stt-backend', choices=['auto', 'google', 'vosk'], default='auto', help='Preferred STT backend (default auto)')
    parser.add_argument('--auto-retries', type=int, default=0, help='Automatic recognition retry attempts on failure')
    parser.add_argument('--offline-stt-model', type=str, default='', help='Path to Vosk model directory (optional)')
    # TTS clarity controls
    parser.add_argument('--tts-rate', type=int, help='Set absolute TTS speech rate (words per minute approx)')
    parser.add_argument('--tts-volume', type=float, help='Set TTS volume 0.0 - 1.0')
    parser.add_argument('--tts-voice', type=str, help='Substring to select a TTS voice by name/id')
    parser.add_argument('--list-voices', action='store_true', help='List available TTS voices and exit')
    parser.add_argument('--tts-voice-index', type=int, help='Select TTS voice by numeric index (see --list-voices)')
    parser.add_argument('--tts-slow', action='store_true', help='Enable slower, clearer speech pacing')
    args = parser.parse_args()

    assistant = AdmissionAssistant()
    # Apply user TTS config before first use
    assistant.configure_tts(rate=args.tts_rate, volume=args.tts_volume, voice_query=args.tts_voice,
                            voice_index=args.tts_voice_index, slow=args.tts_slow)
    if args.list_voices:
        assistant.list_voices()
        return

    # Validate offline model if provided
    if args.offline_stt_model:
        if VOSK_AVAILABLE and os.path.isdir(args.offline_stt_model):
            try:
                if vosk:
                    vosk.Model(args.offline_stt_model)  # type: ignore[attr-defined]
                print(f"[VOSK] Offline model ready: {args.offline_stt_model}")
            except Exception as e:
                print(f"[VOSK] Failed to load offline model: {e}")
        else:
            print("[VOSK] Offline model path invalid or vosk not installed.")

    if args.voice:
        if not STT_AVAILABLE:
            print("⚠️  STT library not available (SpeechRecognition + PyAudio). Falling back to text mode.")
        else:
            print("🎧 Voice mode enabled. Press Ctrl+C to exit.")
        try:
            while True:
                query = None
                if STT_AVAILABLE:
                    query = assistant.listen(timeout=args.stt_timeout,
                                             phrase_time_limit=args.stt_phrase_limit,
                                             quiet=args.quiet_audio,
                                             backend=args.stt_backend,
                                             retries=args.auto_retries)
                if not query:
                    # Allow manual fallback
                    user_typed = input("(Type instead or press Enter to retry mic) > ").strip()
                    if user_typed:
                        if user_typed.lower() in {'instead'}:
                            query = ''  # treat as control word meaning retry
                        else:
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
