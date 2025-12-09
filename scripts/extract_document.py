
import fitz
from docx import Document
import json
import os
import re

# File paths
PDF_PATH = "data/realistic_extraction_paper.pdf"
DOCX_PATH = "data/realistic_extraction_paper.docx"
OUT_DIR = "outputs"

def extract_pdf_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text")
    doc.close()
    return text

def extract_docx_text(docx_path):
    d = Document(docx_path)
    text = ""
    for p in d.paragraphs:
        text += p.text + "\n"
    return text

def save_text(text, out_path):
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)

def split_into_paragraphs(raw_text):
    """
    Simple, heading-driven splitter:

    1) Normalize whitespace (all newlines -> spaces, collapse multiple spaces).
    2) Treat the whole thing as one long string.
    3) Split whenever we see a new 'heading start':
       - 'Abstract'
       - 'Figures'
       - 'Tables'
       - any numbered heading like '1. Introduction', '2. Related Work', etc.
    4) Each resulting chunk becomes a 'paragraph', and every heading
       starts at the beginning of its chunk.
    """
    if not raw_text:
        return []

    # 1) normalize newlines and collapse whitespace
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\s+", " ", text).strip()

    # 2) pattern for heading boundaries
    #    - Abstract
    #    - Figures
    #    - Tables
    #    - 1. Something / 2.1 Something (number-dot-space + Capital letter)
    heading_pattern = re.compile(
        r"Abstract\b|Figures\b|Tables\b|\d+(?:\.\d+)*\.\s+[A-Z]"
    )

    paragraphs = []
    prev = 0

    # 3) cut the text whenever a heading-like pattern starts
    for m in heading_pattern.finditer(text):
        start = m.start()
        if start > prev:
            chunk = text[prev:start].strip()
            if chunk:
                paragraphs.append(chunk)
        prev = start

    # 4) add the final tail
    tail = text[prev:].strip()
    if tail:
        paragraphs.append(tail)

    return paragraphs

def index_paragraphs(paragraphs):
    indexed = []
    for i, p in enumerate(paragraphs):
        indexed.append({"index": i, "text": p})
    return indexed

def save_json(obj, out_path):
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)



import re

def clean_title(s):
    s = re.sub(r'\s+', ' ', (s or "")).strip()
    return s.rstrip(' .:;,-—')

def heading_detection(indexed_paras):
    known = [
        "Abstract","Introduction","Methodology","Methods","Materials",
        "Results","Discussion","Conclusion","Conclusions","References",
        "Acknowledgements","Figures","Tables","Related work","Background",
        "Experimental setup","Supplementary","Acknowledgments"
    ]

    num_re = re.compile(r'^\s*(\d+(?:\.\d+)*)\.\s*(.+)$')
    known_re = re.compile(r'^\s*(?:' + r'|'.join(re.escape(k) for k in known) + r')\b', re.I)

    headings = []

    for item in indexed_paras:
        idx = item.get("index")
        text = (item.get("text") or "").strip()
        if not text:
            continue

        # -------- NUMBERED HEADING --------
        m = num_re.match(text)
        if m:
            number = m.group(1)
            rest = m.group(2).strip()

            # short = first word of rest (usually the heading)
            title_short = clean_title(rest.split()[0])

            # full = entire remainder cleaned
            title_full = clean_title(rest)

            headings.append({
                "index": idx,
                "number": number,
                "title_short": title_short,
                "title_full": title_full,
                "classification": "numbered",
                "method": "num_re"
            })
            continue

        # -------- KNOWN HEADING --------
        k = known_re.match(text)
        if k:
            # short = the known heading word itself
            title_short = clean_title(text.split()[0])

            # full = entire paragraph cleaned
            title_full = clean_title(text)

            headings.append({
                "index": idx,
                "number": None,
                "title_short": title_short,
                "title_full": title_full,
                "classification": "known",
                "method": "known_re"
            })
            continue

    return headings





    
def main():
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)

    print("Extracting PDF...")
    pdf_text = extract_pdf_text(PDF_PATH)

    print("Extracting DOCX...")
    docx_text = extract_docx_text(DOCX_PATH)

    print("\nPDF preview:")
    print(pdf_text[:1000])

    print("\nDOCX preview:")
    print(docx_text[:1000])

    # Save raw extracted text
    save_text(pdf_text, OUT_DIR + "/pdf_content.txt")
    save_text(docx_text, OUT_DIR + "/docx_content.txt")
    print("\nSaved raw text.")

    # Split into heading-based 'paragraphs'
    print("Splitting into paragraphs...")
    pdf_paras = split_into_paragraphs(pdf_text)
    docx_paras = split_into_paragraphs(docx_text)
    print(f"PDF paragraphs: {len(pdf_paras)}, DOCX paragraphs: {len(docx_paras)}")

    # Index and save
    indexed_pdf = index_paragraphs(pdf_paras)
    indexed_docx = index_paragraphs(docx_paras)

    save_json(indexed_pdf, OUT_DIR + "/pdf_paragraphs.json")
    save_json(indexed_docx, OUT_DIR + "/docx_paragraphs.json")
    print("Saved paragraph JSONs.")

    import json

with open("outputs/pdf_paragraphs.json","r",encoding="utf-8") as f:
    pdf_paragraphs = json.load(f)

with open("outputs/docx_paragraphs.json","r",encoding="utf-8") as f:
    docx_paragraphs = json.load(f)

pdf_headings = heading_detection(pdf_paragraphs)
docx_headings = heading_detection(docx_paragraphs)

with open("outputs/pdf_headings.json","w",encoding="utf-8") as f:
    json.dump(pdf_headings, f, indent=2, ensure_ascii=False)

with open("outputs/docx_headings.json","w",encoding="utf-8") as f:
    json.dump(docx_headings, f, indent=2, ensure_ascii=False)






if __name__ == "__main__":
    main()
