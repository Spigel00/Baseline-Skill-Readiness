import os
import json
import re
import fitz  # PyMuPDF

OUT_DIR = "outputs"
PDF_FILE = "data/realistic_extraction_paper.pdf"
DOCX_FILE = "data/realistic_extraction_paper.docx"

def load_json_safe(path):
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def read_text_safe(path):
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def create_metadata(file_type):
    """
    file_type: "pdf" or "docx"
    Produces outputs/<file_type>_metadata.json
    """
    os.makedirs(OUT_DIR, exist_ok=True)

    # file-specific paths
    content_path = os.path.join(OUT_DIR, f"{file_type}_content.txt")
    paras_path = os.path.join(OUT_DIR, f"{file_type}_paragraphs.json")
    headings_path = os.path.join(OUT_DIR, f"{file_type}_headings.json")
    captions_path = os.path.join(OUT_DIR, f"{file_type}_captions.json")
    references_path = os.path.join(OUT_DIR, f"{file_type}_references.json")
    links_path = os.path.join(OUT_DIR, f"{file_type}_reference_links.json")
    manifest_path = os.path.join(OUT_DIR, f"{file_type}_manifest.json")

    # load everything safely
    raw_text = read_text_safe(content_path)
    paragraphs = load_json_safe(paras_path)
    headings = load_json_safe(headings_path)
    captions = load_json_safe(captions_path)
    references = load_json_safe(references_path)
    reference_links = load_json_safe(links_path)
    manifest_partial = load_json_safe(manifest_path)  # optional earlier manifest

    # page count (pdf only)
    page_count = None
    if file_type == "pdf" and os.path.exists(PDF_FILE):
        try:
            doc = fitz.open(PDF_FILE)
            page_count = len(doc)
            doc.close()
        except Exception:
            page_count = None

    # word count (simple token count)
    word_count = len(re.findall(r"\w+", raw_text)) if raw_text else 0

    # counts
    paragraph_count = len(paragraphs)
    heading_count = len(headings)
    figure_caption_count = sum(1 for c in captions if c.get("type") == "figure")
    table_caption_count = sum(1 for c in captions if c.get("type") == "table")
    reference_count = len(references)

    # assemble metadata
    metadata = {
        "file_name": "realistic_extraction_paper." + ("pdf" if file_type == "pdf" else "docx"),
        "file_type": file_type,
        "page_count": page_count,
        "word_count": word_count,
        "paragraph_count": paragraph_count,
        "heading_count": heading_count,
        "figure_caption_count": figure_caption_count,
        "table_caption_count": table_caption_count,
        "reference_count": reference_count,
        "paragraphs": paragraphs,
        "headings": headings,
        "captions": captions,
        "references": references,
        "reference_links": reference_links,
        "manifest_partial": manifest_partial,  # optional included for completeness
        "notes": ""
    }

    out_path = os.path.join(OUT_DIR, f"{file_type}_metadata.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"Wrote {out_path} (paragraphs={paragraph_count}, headings={heading_count}, captions={len(captions)}, references={reference_count})")
    return metadata

def main():
    create_metadata("pdf")
    create_metadata("docx")

if __name__ == "__main__":
    main()
