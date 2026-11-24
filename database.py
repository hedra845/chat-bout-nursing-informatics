import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "nursing_informatics.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Documents / Books Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_type TEXT NOT NULL,
        total_pages INTEGER DEFAULT 0,
        total_words INTEGER DEFAULT 0,
        summary TEXT,
        topics TEXT, -- JSON array of detected key topics
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 2. Book Chunks Table for text search & RAG
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS book_chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        chunk_index INTEGER NOT NULL,
        page_number INTEGER DEFAULT 1,
        content TEXT NOT NULL,
        FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
    )
    ''')

    # 3. Chat Sessions & Messages Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        book_id INTEGER,
        role TEXT NOT NULL, -- 'user' or 'assistant'
        content TEXT NOT NULL,
        sources TEXT, -- JSON list of page citations/chunks
        model_used TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE SET NULL
    )
    ''')

    # 4. Repeated & Frequent Questions Analytics Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS repeated_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        canonical_question TEXT NOT NULL UNIQUE,
        normalized_keywords TEXT NOT NULL,
        category TEXT DEFAULT 'General Nursing Informatics',
        frequency INTEGER DEFAULT 1,
        first_asked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_asked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 5. Clinical / Study Notes Table (Auto-generated notes & User notes)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        category TEXT DEFAULT 'Concept Summary', -- 'Clinical Workflow', 'Terminology', 'EHR/EMR', 'Nursing Standard'
        tags TEXT, -- JSON array
        is_pinned INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE SET NULL
    )
    ''')

    # 6. Researcher Profile, Tone & Idea Memory Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS researcher_profile (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL UNIQUE,
        researcher_name TEXT DEFAULT 'الباحث السريري',
        research_interests TEXT, -- JSON array of interests (e.g. CDSS, Sepsis, Telehealth)
        communication_style TEXT DEFAULT 'تحليلي أكاديمي ودقيق', -- detected tone & preference
        synthesized_ideas TEXT, -- JSON array of researcher's logged thoughts and hypotheses
        vocabulary_preferences TEXT, -- JSON array of researcher's frequent words and linguistic style
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 7. Researcher Hypothesis & Idea Logs Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS researcher_ideas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        idea_type TEXT DEFAULT 'فرضية بحثية', -- 'فرضية بحثية', 'ملاحظة نقدية', 'فكرة مشروع تخرج/دراسة', 'منهجية سريرية'
        raw_statement TEXT NOT NULL,
        inferred_meaning TEXT NOT NULL,
        suggested_direction TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 8. Standard Reference Knowledge Dataset Table (Nursing Informatics Benchmark Knowledge Base)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reference_dataset (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concept_code TEXT NOT NULL UNIQUE,       -- e.g. 'NI-DIKW-01', 'NI-CDSS-02', 'NI-TERMINOLOGY-03'
        domain TEXT NOT NULL,                     -- 'Core Concepts', 'Terminologies', 'Clinical Decision Support', 'EHR & Systems', 'Safety & Quality', 'Ethics & HIPAA'
        concept_name_en TEXT NOT NULL,
        concept_name_ar TEXT NOT NULL,
        clinical_definition TEXT NOT NULL,
        clinical_importance TEXT NOT NULL,
        real_world_example TEXT NOT NULL,
        standard_mapping TEXT,                   -- Mapping to SNOMED CT, ICNP, NANDA, HL7, etc.
        source_reference TEXT DEFAULT 'ANA & IMIA Nursing Informatics International Guidelines',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 9. System & AI Settings Table (For Admin Dashboard & Cloud Integration)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS system_settings (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Default system settings if not present
    cursor.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('gemini_api_key', '')")
    cursor.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('default_ai_mode', 'auto')")
    cursor.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('ai_temperature', '0.4')")
    cursor.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('system_prompt', 'أنت مساعد وباحث خبير في معلوماتية التمريض (Nursing Informatics AI Assistant & Academic Research Mentor).')")

    # 10. Pre-populate default seed knowledge if empty
    cursor.execute('SELECT COUNT(*) as count FROM books')
    count = cursor.fetchone()['count']
    if count == 0:
        seed_default_nursing_informatics_data(cursor)

    conn.commit()
    conn.close()

def seed_default_nursing_informatics_data(cursor):
    cursor.execute('''
    INSERT INTO books (title, filename, file_path, file_type, total_pages, total_words, summary, topics)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        "Handbook of Nursing Informatics & Clinical Systems",
        "nursing_informatics_core.txt",
        "sample",
        "txt",
        15,
        3500,
        "A foundational guide covering Nursing Informatics definitions, EHR/EMR implementation, Clinical Decision Support Systems (CDSS), Nursing Minimum Data Set (NMDS), SNOMED CT, ICNP, telehealth, patient safety, and data privacy (HIPAA).",
        json.dumps(["EHR / EMR", "CDSS", "SNOMED CT & ICNP", "NMDS", "Patient Safety & Quality", "HIPAA & Telehealth", "Workflow Optimization"])
    ))
    book_id = cursor.lastrowid

    # Core chunks on Nursing Informatics
    seed_chunks = [
        (book_id, 0, 1, """Nursing Informatics (NI) is the specialty that integrates nursing science with multiple information and analytical sciences to identify, define, manage, and communicate data, information, knowledge, and wisdom in nursing practice. NI supports nurses, consumers, patients, the interprofessional healthcare team, and other stakeholders in their decision-making in all roles and settings to achieve desired outcomes. (ANA Definition)"""),
        (book_id, 1, 2, """The DIKW Pyramid in Nursing:
- Data: Raw, unorganized facts without context (e.g., Blood Pressure 120/80 mmHg, SpO2 94%).
- Information: Data that has been structured and contextualized (e.g., patient's BP is 120/80 mmHg post-operative day 1).
- Knowledge: Synthesized information with clinical meaning, patterns recognized (e.g., recognizing that declining SpO2 combined with elevated respiration indicates respiratory distress).
- Wisdom: Judicious and ethical application of knowledge to direct patient care and future policy (e.g., ordering preemptive airway management and altering clinical protocols based on predictive risk)."""),
        (book_id, 2, 3, """Standardized Nursing Terminologies (SNTs):
1. ICNP (International Classification for Nursing Practice): Maintained by ICN, provides formal terminology for nursing diagnoses, interventions, and outcomes.
2. NANDA-International (NANDA-I): Diagnostic classification for nursing diagnoses.
3. NIC (Nursing Interventions Classification): Comprehensive standardized language describing treatments nurses perform.
4. NOC (Nursing Outcomes Classification): Standardized classification to evaluate outcomes influenced by nursing interventions.
5. SNOMED CT: Comprehensive clinical healthcare terminology mapped with nursing terminologies for interoperable Electronic Health Records (EHR).
6. LOINC: Codes for clinical observations and laboratory results."""),
        (book_id, 3, 4, """Electronic Health Records (EHR) and Clinical Decision Support Systems (CDSS):
EHRs replace paper records with longitudinal electronic patient health records. Key components include Computerized Provider Order Entry (CPOE), electronic Medication Administration Record (eMAR), bar-code medication scanning (BCMA), and clinical alerts.
CDSS provides clinicians, staff, and patients with knowledge and person-specific information to enhance health decisions. Examples include drug-drug interaction alerts, fall risk predictors, and sepsis early warning alarms (e.g., MEWS / qSOFA alerts). Alert fatigue is a critical challenge where clinicians become desensitized to frequent alarms."""),
        (book_id, 4, 5, """Nursing Minimum Data Set (NMDS) and Data Standards:
NMDS is a minimum set of items with uniform definitions to collect essential nursing care data across health settings. Categories include:
1. Nursing Care Elements: Nursing diagnosis, nursing intervention, nursing outcome, intensity of nursing care.
2. Patient Demographic Elements: Personal identification, birth date, gender, race/ethnicity, residence.
3. Service Elements: Facility number, unique health record number, discharge date, disposition, primary nurse identifier."""),
        (book_id, 5, 6, """Ethical, Legal, and Privacy Considerations (HIPAA & Security):
Nursing informatics professionals must safeguard Protected Health Information (PHI). Under HIPAA regulations, strict access controls, encryption, and audit logs are mandated. Role-Based Access Control (RBAC) ensures nurses only access patient records within their assigned unit/care team. Telehealth nursing must adhere to interstate licensure compacts and secure end-to-end encrypted video channels.""")
    ]

    for b_id, c_idx, page, content in seed_chunks:
        cursor.execute('''
        INSERT INTO book_chunks (book_id, chunk_index, page_number, content)
        VALUES (?, ?, ?, ?)
        ''', (b_id, c_idx, page, content))

    # Pre-populate some repeated questions
    cursor.execute('''
    INSERT INTO repeated_questions (canonical_question, normalized_keywords, category, frequency)
    VALUES 
    (?, ?, ?, ?),
    (?, ?, ?, ?)
    ''', (
        "What is the DIKW hierarchy in Nursing Informatics?",
        "dikw hierarchy data information knowledge wisdom nursing",
        "Core Concepts",
        6,
        "What are the differences between NANDA-I, NIC, and NOC?",
        "nanda nic noc standardized terminologies differences",
        "Standardized Terminologies",
        4
    ))

    # Pre-populate sample clinical notes
    cursor.execute('''
    INSERT INTO notes (book_id, title, content, category, tags, is_pinned)
    VALUES 
    (?, ?, ?, ?, ?, ?),
    (?, ?, ?, ?, ?, ?)
    ''', (
        book_id,
        "Key Distinctions in Nursing Terminology (NANDA vs NIC vs NOC)",
        "NANDA-I focuses on diagnosis (identifying the human response).\nNIC classifies interventions (nursing actions).\nNOC measures patient outcomes across a numeric Likert scale.\nRemember: Assessment -> NANDA -> NIC -> NOC -> Evaluation.",
        "Terminology",
        json.dumps(["NANDA", "NIC", "NOC", "Exam Review"]),
        1,
        book_id,
        "Alert Fatigue Mitigation in CDSS",
        "Clinical Decision Support alerts must be tiered:\n- Level 1: Hard stop (critical life threat, e.g. severe anaphylactic penicillin allergy).\n- Level 2: Soft stop with override reason required.\n- Level 3: Informational banner only.\nMinimizing non-actionable alarms reduces alert fatigue among bedside nurses.",
        "Clinical Workflow",
        json.dumps(["CDSS", "Safety", "Alert Fatigue", "Best Practice"]),
        1
    ))

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at", DB_PATH)
