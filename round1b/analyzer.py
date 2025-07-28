import os
import fitz
import json
from datetime import datetime

KEYWORDS = []

def load_metadata():
    with open("data/persona.txt", "r") as f:
        persona = f.read().strip()
    with open("data/task.txt", "r") as f:
        job = f.read().strip()
    global KEYWORDS
    KEYWORDS = [word.lower() for word in job.split() if len(word) > 3]
    return persona, job

def extract_relevant_sections(pdf_path):
    doc = fitz.open(pdf_path)
    results = []

    for page_num, page in enumerate(doc, 1):
        blocks = page.get_text("blocks")
        for b in blocks:
            text = b[4].strip()
            if not text or len(text.split()) < 10:
                continue
            score = sum(1 for word in KEYWORDS if word in text.lower())
            if score >= 1:
                results.append({
                    "document": os.path.basename(pdf_path),
                    "page": page_num,
                    "section_title": text.split("\n")[0][:50],
                    "importance_rank": score,
                    "refined_text": text
                })

    return sorted(results, key=lambda x: -x["importance_rank"])

def main():
    persona, job = load_metadata()
    all_results = []
    pdf_files = [f for f in os.listdir("input") if f.endswith(".pdf")]

    for file in pdf_files:
        all_results.extend(extract_relevant_sections(os.path.join("input", file)))

    output = {
        "metadata": {
            "documents": pdf_files,
            "persona": persona,
            "job": job,
            "timestamp": datetime.now().isoformat()
        },
        "results": all_results[:10]
    }

    with open("output/round1b_output.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    main()
