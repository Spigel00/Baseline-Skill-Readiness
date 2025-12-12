

This project is my complete extraction pipeline for working with scientific documents in PDF and DOCX.
I built it step-by-step to understand how raw text becomes structured metadata.


What This Project Does

This pipeline takes a scientific paper (PDF + DOCX) and extracts:

* Raw text
* Clean paragraphs
* Headings (numbered + known)
* Figure captions
* Table captions
* Figure/table references inside paragraphs
* Mapped links (reference → caption)
* A manifest summarizing counts
* A final `metadata.json` for both PDF and DOCX

The final output is a structured representation of the entire document.



How the Pipeline Works 

1️⃣ Extract text

* PyMuPDF → PDF text
* python-docx → DOCX text

2️⃣ Split into clean paragraphs

Handles issues like:

* PDFs using single newlines
* Inline headings like `... pipelines. 1. Introduction`
* Line wraps inside paragraphs

3️⃣ Detect headings

* Numbered (e.g., `1. Introduction`)
* Known headings (“Abstract”, “Methodology”, etc.)

Short and full titles are extracted.

4️⃣ Detect captions

Regex-based:

* `Figure 1: ...`
* `Table 2 - ...`
  Also handles multiple captions inside one paragraph.

5️⃣ Detect references inside text

Covers:

* `Figure 1`
* `Fig. 2`
* `Tables 1–3`
* `(Fig. 1)`
* comma lists like `Fig. 1, 2, and 4`

6️⃣ Map references → captions

If a paragraph says “Figure 1”, we link it to the actual caption entry.

7️⃣ Build a manifest

Counts:

* paragraphs
* headings
* captions
* references
* word count
* page count

8️⃣ Package everything into metadata.json

This is the final deliverable that contains all collected information in one place.

What I Learned

This project taught me how real extraction pipelines work:

* PDFs lose structure; DOCX preserves it
* Regex needs to be tested, not trusted
* Splitting text is harder than extracting it
* Pipelines work best when every step is separate and simple
* Metadata is just structured meaning

I also learned core Python ideas like:

* `.split()`, `.strip()`, `.enumerate()`
* JSON handling
* Regex groups
* Designing functions so they are testable
* Thinking in terms of **input → transform → output**



How to Run the Pipeline

Run extraction:


python scripts/extract_document_funcs.py


Run heading/caption/reference detection:


python scripts/extract_document.py


Finally, build the full metadata:


python scripts/build_metadata.py


Outputs will appear in the `outputs/` folder.



Notes

This pipeline is intentionally “simple-first”.
It is not meant to be perfect — it is meant to be understandable.


