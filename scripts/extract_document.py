
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

    if not raw_text:
        return []

    # 1) normalize newlines and collapse whitespace
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\s+", " ", text).strip()

    # 2) pattern for heading boundaries
    
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

def detect_fig_table(indexed_paras):
    captions = []

    fig_re = re.compile(
    r'(?i)\b(?:figure|fig)\.?\s*(\d+)\s*[:\-\.]\s*(.+?)(?=Figure|Fig|Table|$)')

    table_re = re.compile(
    r'(?i)\btable\.?\s*(\d+)\s*[:\-\.]\s*(.+?)(?=Figure|Fig|Table|$)')


    for item in indexed_paras:
        idx = item["index"]
        text = item["text"]

        # ----- FIGURES: find ALL -----
        for m in fig_re.finditer(text):
            captions.append({
                "index": idx,
                "type": "figure",
                "number": int(m.group(1)),
                "text": m.group(0).strip(),
                "caption_text": m.group(2).strip()
            })

        # ----- TABLES: find ALL -----
        for m in table_re.finditer(text):
            captions.append({
                "index": idx,
                "type": "table",
                "number": int(m.group(1)),
                "text": m.group(0).strip(),
                "caption_text": m.group(2).strip()
            })

    return captions


import re

# ---------- Regex patterns ----------
range_re = re.compile(r'(?i)\b(?:fig(?:ure)?|table)s?\.?\s*(\d+)\s*[–—-]\s*(\d+)\b')
list_re = re.compile(r'(?i)\b(?:fig(?:ure)?|table)s?\.?\s*((?:\d+[a-z]?(?:\s*(?:,|and|&)\s*)?)+)\b')
paren_re = re.compile(r'(?i)(?:\(|\b)(?:see|cf\.?|see also)?\s*(fig(?:ure)?|table)\.?\s*(\d+[a-z]?(?:\s*[–—-]\s*\d+)?)\b(?:\))?')
single_re = re.compile(r'(?i)\b(?:fig(?:ure)?|table)\.?\s*(\d+[a-z]?)\b')


# ---------- Helper ----------
def expand_list(s):
    """Turn '1, 2a and 4' into ['1','2a','4']"""
    parts = re.split(r'[,\s]+|and|&', s, flags=re.I)
    return [p for p in (p.strip() for p in parts) if p]


def detect_references(indexed_paras):
    references = []

    for item in indexed_paras:
        idx = item.get("index")
        text = (item.get("text") or "")
        lower = text.lower()

        # ---- 1) RANGES: 'Figure 1-3' → 1,2,3 ----
        for m in range_re.finditer(text):
            start = int(m.group(1))
            end = int(m.group(2))
            ref_type = "figure" if "fig" in m.group(0).lower() else "table"

            for num in range(start, end + 1):
                references.append({
                    "index": idx,
                    "ref_type": ref_type,
                    "ref_number": str(num),
                    "ref_text": f"{ref_type.capitalize()} {num}",
                })

        # ---- 2) LISTS: 'Fig. 1, 2a and 4' ----
        for m in list_re.finditer(text):
            ref_type = "figure" if "fig" in m.group(0).lower() else "table"
            nums = expand_list(m.group(1))

            for num in nums:
                references.append({
                    "index": idx,
                    "ref_type": ref_type,
                    "ref_number": num,
                    "ref_text": f"{ref_type.capitalize()} {num}",
                })

        # ---- 3) Parenthetical: '(see Fig. 2a)' ----
        for m in paren_re.finditer(text):
            ref_type = "figure" if "fig" in m.group(0).lower() else "table"
            val = m.group(2)

            # could be a range inside parentheses
            if re.search(r'[–—-]', val):
                start, end = re.split(r'[–—-]', val)
                start = int(start)
                end = int(end)
                for num in range(start, end + 1):
                    references.append({
                        "index": idx,
                        "ref_type": ref_type,
                        "ref_number": str(num),
                        "ref_text": f"{ref_type.capitalize()} {num}",
                    })
            else:
                references.append({
                    "index": idx,
                    "ref_type": ref_type,
                    "ref_number": val,
                    "ref_text": f"{ref_type.capitalize()} {val}",
                })

        # ---- 4) Single references: 'Figure 2a' ----
        for m in single_re.finditer(text):
            ref_type = "figure" if "fig" in m.group(0).lower() else "table"
            num = m.group(1)

            references.append({
                "index": idx,
                "ref_type": ref_type,
                "ref_number": num,
                "ref_text": f"{ref_type.capitalize()} {num}",
            })

    return references








    
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

with open("outputs/pdf_paragraphs.json","r",encoding="utf-8") as f:
    pdf_paragraphs = json.load(f)

with open("outputs/docx_paragraphs.json","r",encoding="utf-8") as f:
    docx_paragraphs = json.load(f)

pdf_captions = detect_fig_table(pdf_paragraphs)
docx_captions = detect_fig_table(docx_paragraphs)

with open("outputs/pdf_captions.json", "w", encoding="utf-8") as f:
    json.dump(pdf_captions, f, indent=2, ensure_ascii=False)

with open("outputs/docx_captions.json", "w", encoding="utf-8") as f:
    json.dump(docx_captions, f, indent=2, ensure_ascii=False)


with open("outputs/pdf_paragraphs.json","r",encoding="utf-8") as f:
    pdf_paragraphs = json.load(f)

with open("outputs/docx_paragraphs.json","r",encoding="utf-8") as f:
    docx_paragraphs = json.load(f)

pdf_references = detect_fig_table(pdf_paragraphs)
docx_references = detect_fig_table(docx_paragraphs)

with open("outputs/pdf_references.json", "w", encoding="utf-8") as f:
    json.dump(pdf_references, f, indent=2, ensure_ascii=False)

with open("outputs/docx_references.json", "w", encoding="utf-8") as f:
    json.dump(docx_references, f, indent=2, ensure_ascii=False)



if __name__ == "__main__":
    main()
