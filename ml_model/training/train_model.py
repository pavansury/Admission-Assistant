#!/usr/bin/env python3
"""Train a lightweight intent classifier using scikit-learn.

TensorFlow is not available in this runtime (Python 3.12) so we fallback to
TF-IDF + Logistic Regression. We still emit a placeholder 'model.tflite' so the
expected artifact path exists for firmware integration planning.
"""
from __future__ import annotations
import json, pathlib, joblib, datetime, hashlib
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ART_DIR = pathlib.Path(__file__).resolve().parent / 'artifacts'
DATA_PATH = ART_DIR / 'processed_dataset.json'
MODEL_DIR = ROOT / 'ml_model'
MODEL_DIR.mkdir(exist_ok=True)
SK_MODEL_PATH = ART_DIR / 'intent_pipeline.joblib'
TFLITE_PLACEHOLDER = MODEL_DIR / 'model.tflite'
META_PATH = ART_DIR / 'model_metadata.json'

def load_dataset():
	with open(DATA_PATH, 'r', encoding='utf-8') as f:
		payload = json.load(f)
	samples = payload['samples']
	labels = payload['labels']
	texts = [s['text'] for s in samples]
	y = [labels.index(s['label']) for s in samples]
	return texts, y, labels

def build_pipeline():
	return Pipeline([
		("tfidf", TfidfVectorizer(max_features=800, ngram_range=(1,2)) ),
		("clf", LogisticRegression(max_iter=500))
	])

def main():
	if not DATA_PATH.exists():
		raise SystemExit("Processed dataset missing. Run dataset_preprocessing.py first.")

	texts, y, labels = load_dataset()
	pipe = build_pipeline()
	pipe.fit(texts, y)
	preds = pipe.predict(texts)
	acc = accuracy_score(y, preds)
	print(f"Training (resubstitution) accuracy: {acc:.3f}")

	joblib.dump({"pipeline": pipe, "labels": labels}, SK_MODEL_PATH)
	print(f"Saved scikit-learn model to {SK_MODEL_PATH}")

	# Produce metadata
	meta = {
		"created": datetime.datetime.utcnow().isoformat() + "Z",
		"labels": labels,
		"accuracy_train": acc,
		"backend": "scikit-learn",
		"pipeline": [step for step,_ in pipe.steps],
		"tflite_available": False
	}
	META_PATH.write_text(json.dumps(meta, indent=2), encoding='utf-8')

	# Emit placeholder TFLite file so downstream paths do not break
	if not TFLITE_PLACEHOLDER.exists():
		TFLITE_PLACEHOLDER.write_bytes(b"PLACEHOLDER_TFLITE_NOT_AVAILABLE")
		print(f"Created placeholder {TFLITE_PLACEHOLDER}")

if __name__ == '__main__':
	main()

