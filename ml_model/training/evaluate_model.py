#!/usr/bin/env python3
"""Evaluate the scikit-learn intent classifier (resubstitution)."""
import json, pathlib, joblib
from sklearn.metrics import accuracy_score, classification_report

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ART_DIR = pathlib.Path(__file__).resolve().parent / 'artifacts'
DATA_PATH = ART_DIR / 'processed_dataset.json'
MODEL_PATH = ART_DIR / 'intent_pipeline.joblib'

def load():
	with open(DATA_PATH, 'r', encoding='utf-8') as f:
		payload = json.load(f)
	samples = payload['samples']
	labels = payload['labels']
	return samples, labels

def main():
	if not MODEL_PATH.exists():
		raise SystemExit("Model not trained. Run train_model.py")
	samples, labels = load()
	bundle = joblib.load(MODEL_PATH)
	pipe = bundle['pipeline']
	lbls = bundle['labels']
	texts = [s['text'] for s in samples]
	y_true = [lbls.index(s['label']) for s in samples]
	preds = pipe.predict(texts)
	acc = accuracy_score(y_true, preds)
	print(f"Accuracy: {acc:.3f}")
	print(classification_report(y_true, preds, target_names=lbls))

if __name__ == '__main__':
	main()

