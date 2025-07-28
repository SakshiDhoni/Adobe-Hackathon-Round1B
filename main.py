import pdfplumber
import json
import os
import re
from collections import defaultdict

def extract_document_outline(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        outline = []

        for i, page in enumerate(pdf.pages):
            page_number = i + 1
            chars = page.chars

            if not chars:
                continue

            try:
                # Try to get words with extra attrs, but if it fails, use raw words
                # Note: Skip extra_attrs if it fails; style-based detection is best-effort
                words = []
                try:
                    words = page.extract_words(keep_blank_chars=False, extra_attrs=["fontname", "size", "bold", "italic"])
                except KeyError:
                    # Fall back on plain word extraction if extra attrs fail
                    words = page.extract_words(keep_blank_chars=False)

                # Group by top position to get "lines" for context
                lines = defaultdict(list)
                for word in words:
                    top = round(word['top'], 1)
                    lines[top].append(word)

                for _, line_words in sorted(lines.items()):
                    text = ' '.join(w['text'] for w in line_words)
                    if text.strip().isdigit() or len(text.strip()) < 3:
                        continue

                    first_word = line_words[0]
                    last_word = line_words[-1]
                    line_center = (first_word['x0'] + last_word['x1']) / 2
                    page_center = page.width / 2
                    is_centered = abs(line_center - page_center) < 30

                    # Style detection is best-effort (fall back on all false if no extra_attrs)
                    extra_attrs_ok = all(('italic' in word and 'bold' in word) for word in line_words if isinstance(word, dict))
                    if not extra_attrs_ok:
                        is_large = False
                        is_bold = False
                        is_all_caps = False
                    else:
                        font_size_sum = sum(w.get('size', 0) for w in line_words)
                        avg_size = font_size_sum / len(line_words) if line_words else 0
                        # Arbitrary size threshold; adjust based on PDF
                        is_large = avg_size > 12  # threshold for "large" text, tweak as needed
                        is_bold = any(w.get('bold', False) for w in line_words)
                        is_all_caps = text == text.upper()

                    # Heuristic: numbered sections/chapters are usually headings
                    has_numbering = re.match(r'^(Chapter|Chap|§|Section|Sec|Part|\d+[\.\s-])', text.strip())
                    has_subsection_numbering = re.match(r'^\d+\.\d+$|^\d+\.\d+\.\d+$|^\d+\.\d+[^0-9]', text.strip().split()[0])

                    level = None
                    # Title (usually first, centered, large, on page 1)
                    if i == 0 and (is_centered or is_bold or is_large):
                        level = "H1"
                    # Chapter (explicit by "Chapter n" or section number)
                    elif has_numbering and len(text.strip().split()) > 2:
                        level = "H1" if 'Chapter' in text[:10] else "H2"
                        # If starts with 1.2, it's H2; 1.2.3 is H3; etc.
                        if has_subsection_numbering:
                            dots = text.strip().split()[0].count('.')
                            level = "H2" if dots == 1 else "H3"
                    # Generic headings: bold and large on later pages
                    elif (is_bold and is_large) and page_number > 1:
                        level = "H2"

                    if level:
                        entry = {
                            "level": level,
                            "text": text.strip(),
                            "page": page_number
                        }
                        outline.append(entry)

            except Exception as e:
                print(f"Error on page {page_number}: {str(e)}")
                continue

        if outline:
            title = outline[0]["text"] if outline[0]["level"] == "H1" else os.path.splitext(os.path.basename(pdf_path))[0]
            return {
                "title": title,
                "outline": outline
            }
        return None

if not os.path.exists("./output"):
    os.makedirs("./output")

pdf_files = [f for f in os.listdir("./input") if f.lower().endswith(".pdf")]
for pdf_file in pdf_files:
    outline = extract_document_outline(f"./input/{pdf_file}")
    if outline:
        with open(f"./output/{pdf_file}.json", "w", encoding="utf-8") as f:
            json.dump(outline, f, indent=2, ensure_ascii=False)
