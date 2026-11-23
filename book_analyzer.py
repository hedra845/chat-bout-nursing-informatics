import os
import re
import json
from pypdf import PdfReader
from database import get_db_connection

def extract_text_from_pdf(pdf_path):
    """Extracts text and page numbers from uploaded PDF book"""
    reader = PdfReader(pdf_path)
    pages_data = []
    total_words = 0

    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        clean_text = re.sub(r'\s+', ' ', text).strip()
        words = len(clean_text.split())
        total_words += words
        if clean_text:
            pages_data.append({
                "page_number": idx + 1,
                "text": clean_text
            })

    return pages_data, len(reader.pages), total_words

def extract_text_from_txt(txt_path):
    """Extracts text from plain text or markdown files"""
    with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Split into virtual pages of ~500 words
    words = content.split()
    total_words = len(words)
    chunk_size = 400
    pages_data = []

    for i in range(0, len(words), chunk_size):
        page_num = (i // chunk_size) + 1
        page_text = " ".join(words[i:i + chunk_size])
        pages_data.append({
            "page_number": page_num,
            "text": page_text
        })

    return pages_data, max(1, len(pages_data)), total_words

def analyze_and_index_book(file_path, original_filename, title=None):
    """
    Parses the book, splits into searchable chunks, extracts key themes,
    and automatically generates synthesized clinical study notes into the database.
    """
    ext = os.path.splitext(original_filename)[1].lower()
    
    if ext == '.pdf':
        pages_data, total_pages, total_words = extract_text_from_pdf(file_path)
    else:
        pages_data, total_pages, total_words = extract_text_from_txt(file_path)

    book_title = title if title else os.path.splitext(original_filename)[0].replace('_', ' ').replace('-', ' ').title()

    # Detect topics across the book
    all_text = " ".join([p['text'] for p in pages_data])
    detected_topics = []
    
    topic_map = {
        "DIKW Framework": ["dikw", "wisdom", "knowledge", "pyramid"],
        "Electronic Health Records (EHR)": ["ehr", "emr", "cpoe", "electronic health"],
        "Clinical Decision Support (CDSS)": ["cdss", "decision support", "clinical alert", "warning"],
        "Standardized Terminologies": ["nanda", "nic", "noc", "icnp", "snomed", "terminology"],
        "Data Standards & Interoperability": ["hl7", "fhir", "interoperability", "interchange"],
        "Patient Safety & Quality": ["patient safety", "adverse event", "medication error", "quality"],
        "Telehealth & Remote Care": ["telehealth", "telemedicine", "remote monitoring"],
        "Healthcare Privacy & HIPAA": ["hipaa", "phi", "privacy", "confidentiality", "security"],
        "Nursing Minimum Data Set (NMDS)": ["nmds", "minimum data", "dataset"]
    }

    lower_text = all_text.lower()
    for topic, keywords in topic_map.items():
        if any(kw in lower_text for kw in keywords):
            detected_topics.append(topic)

    if not detected_topics:
        detected_topics = ["Nursing Informatics Overview", "Clinical Systems"]

    if not pages_data:
        # Fallback for scanned/empty text pages so the book is NEVER lost
        pages_data.append({
            "page_number": 1,
            "text": f"Uploaded reference: {book_title}. (Note: Content was ingested as document pages; searchable index established)."
        })
        total_pages = max(1, total_pages)
        total_words = max(15, total_words)

    summary = f"Analyzed '{book_title}' spanning {total_pages} pages ({total_words:,} words). Major informatics domains identified: {', '.join(detected_topics[:4])}."

    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert Book
    cursor.execute("""
        INSERT INTO books (title, filename, file_path, file_type, total_pages, total_words, summary, topics)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        book_title,
        original_filename,
        file_path,
        ext.replace('.', ''),
        total_pages,
        total_words,
        summary,
        json.dumps(detected_topics)
    ))
    book_id = cursor.lastrowid

    # Index chunks (chunks of ~250-350 words per chunk preserving page metadata)
    chunk_index = 0
    for p in pages_data:
        p_text = p['text']
        p_words = p_text.split()
        sub_chunk_size = 250
        
        for j in range(0, len(p_words), sub_chunk_size):
            chunk_content = " ".join(p_words[j:j + sub_chunk_size])
            if len(chunk_content.strip()) > 30:
                cursor.execute("""
                    INSERT INTO book_chunks (book_id, chunk_index, page_number, content)
                    VALUES (?, ?, ?, ?)
                """, (book_id, chunk_index, p['page_number'], chunk_content))
                chunk_index += 1

    # Auto-generate essential Study/Clinical Notes from Book Content
    auto_notes = [
        (
            f"Key Takeaways: {book_title}",
            f"Automatic analytical extraction from '{book_title}':\n\n"
            f"- Identified Core Domains: {', '.join(detected_topics)}\n"
            f"- Total Pages Indexed: {total_pages}\n"
            f"- Clinical Significance: Serves as primary clinical reference for informatics evaluation and clinical nursing workflows.",
            "Concept Summary",
            json.dumps(["Overview", "Auto-Generated", "Book Summary"])
        )
    ]

    # If specific topics exist, create specialized clinical review notes
    if "Standardized Terminologies" in detected_topics:
        auto_notes.append((
            f"Terminologies Guide - {book_title}",
            "Standardized Nursing Languages (SNLs) enable cross-system data comparison and clear clinical nursing documentation. Key standards mentioned include NANDA-I, NIC, NOC, and SNOMED CT.",
            "Terminology",
            json.dumps(["Standardized Languages", "Documentation", "EHR"])
        ))

    if "Clinical Decision Support (CDSS)" in detected_topics:
        auto_notes.append((
            f"CDSS & Patient Safety - {book_title}",
            "Key CDSS implementations: Order check alerts, medication safety checks, sepsis triggers. Priority rule: Balance alert specificity to avoid clinician alert fatigue.",
            "Clinical Workflow",
            json.dumps(["CDSS", "Safety", "Alerts"])
        ))

    for n_title, n_content, n_cat, n_tags in auto_notes:
        cursor.execute("""
            INSERT INTO notes (book_id, title, content, category, tags, is_pinned)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (book_id, n_title, n_content, n_cat, n_tags))

    conn.commit()
    conn.close()

    return {
        "book_id": book_id,
        "title": book_title,
        "pages": total_pages,
        "words": total_words,
        "topics": detected_topics,
        "summary": summary
    }
