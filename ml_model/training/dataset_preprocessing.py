#!/usr/bin/env python3
"""Dataset preprocessing for Admission Assistant intent model.

Reads the FAQ CSV and builds a small intent dataset. Because the raw data is tiny,
we apply minimal augmentation by duplicating entries with keyword variants.
Outputs:
  processed_dataset.json : list of {text, label}
  labels.txt             : label order used during training
"""

from __future__ import annotations
import csv, json, random, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CSV_PATH = ROOT / 'database' / 'faq.csv'
OUT_DIR = pathlib.Path(__file__).resolve().parent / 'artifacts'
OUT_DIR.mkdir(parents=True, exist_ok=True)

def load_rows():
	rows = []
	with open(CSV_PATH, newline='', encoding='utf-8') as f:
		r = csv.DictReader(f)
		for row in r:
			rows.append(row)
	return rows

CATEGORY_EXTRAS = {
	'fee': [
		'what is the application fee', 'how much is the application fee', 'fee amount', 'cost to apply',
		'application fee cost', 'is there any application fee'
	],
	'process': [
		'what is the application process', 'how do i apply', 'steps to apply', 'application procedure',
		'explain application steps'
	],
	'deadline': [
		'what is the application deadline', 'application last date', 'last date to apply', 'submission deadline'
	],
	'requirements': [
		'what are the admission requirements', 'eligibility criteria', 'admission eligibility'
	],
	'documents': [
		'required documents list', 'what documents are needed', 'documents required for application'
	],
	'financial_aid': [
		'is financial aid available', 'are there scholarships', 'scholarship options', 'financial assistance'
	],
	'programs': [
		'available programs', 'what programs do you offer', 'list of courses', 'available courses'
	],
	'schedule': [
		'when do classes start', 'class start date', 'semester start', 'start of classes'
	],
}

def simple_augment(text: str, label: str):
	base = text.strip()
	variants = [base, base.lower()]
	polite = ["please ", "could you ", "kindly "]
	for p in polite:
		variants.append(p + base.lower())
	# Add category extras
	extras = CATEGORY_EXTRAS.get(label, [])
	variants.extend(extras)
	return list(dict.fromkeys(variants))

def build_dataset(rows):
	dataset = []
	for row in rows:
		base = row['question'].strip()
		label = row['category'].strip()
		for v in simple_augment(base, label):
			dataset.append({"text": v, "label": label})
	random.shuffle(dataset)
	return dataset

def main():
	rows = load_rows()
	dataset = build_dataset(rows)
	labels = sorted({d['label'] for d in dataset})
	with open(OUT_DIR / 'processed_dataset.json', 'w', encoding='utf-8') as f:
		json.dump({"samples": dataset, "labels": labels}, f, indent=2)
	with open(ROOT / 'ml_model' / 'labels.txt', 'w', encoding='utf-8') as f:
		f.write("\n".join(labels) + "\n")
	print(f"Wrote {len(dataset)} samples across {len(labels)} labels")

if __name__ == '__main__':
	main()

