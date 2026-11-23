import json
import re
from database import get_db_connection

def analyze_and_update_researcher_profile(session_id, user_message):
    """
    Analyzes researcher's statement to detect:
    1. Communication style / tone (Formal academic, practical clinical, inquisitive, critical/philosophical).
    2. Emerging research ideas, hypotheses, and projects.
    3. Research interests and keywords.
    4. Preferred phrasing and vocabulary.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Retrieve or create profile
    cursor.execute("SELECT * FROM researcher_profile WHERE session_id = ?", (session_id,))
    profile = cursor.fetchone()

    if not profile:
        cursor.execute("""
            INSERT INTO researcher_profile (session_id, researcher_name, research_interests, communication_style, synthesized_ideas, vocabulary_preferences)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            "الباحث السريري (Clinical Researcher)",
            json.dumps(["معلوماتية التمريض", "EHR", "CDSS"]),
            "تحليلي منطقي دقيق",
            json.dumps([]),
            json.dumps([])
        ))
        conn.commit()
        cursor.execute("SELECT * FROM researcher_profile WHERE session_id = ?", (session_id,))
        profile = cursor.fetchone()

    current_interests = json.loads(profile['research_interests']) if profile['research_interests'] else []
    current_ideas = json.loads(profile['synthesized_ideas']) if profile['synthesized_ideas'] else []
    current_vocab = json.loads(profile['vocabulary_preferences']) if profile['vocabulary_preferences'] else []
    detected_style = profile['communication_style'] or "تحليلي أكاديمي"

    lower_msg = user_message.lower()

    # 1. Detect Interests
    topic_cues = {
        "Clinical Decision Support (CDSS)": ["cdss", "قرار", "decision", "تنبيه", "alert", "إنذار", "fatigue"],
        "Electronic Health Records (EHR)": ["ehr", "emr", "سجل", "سجلات", "cpoe", "emar"],
        "DIKW & Nursing Science": ["dikw", "بيانات", "حكمة", "معرفة", "wisdom", "data"],
        "Standardized Terminologies": ["nanda", "nic", "noc", "icnp", "snomed", "مصطلحات"],
        "Patient Safety & Quality": ["safety", "سلامة", "أخطاء", "error", "جودة", "quality"],
        "Telehealth & Remote Care": ["telehealth", "telemedicine", "عن بعد", "عن بُعد", "افتراضي"],
        "Ethical & Legal (HIPAA)": ["hipaa", "خصوصية", "أخلاقي", "legal", "سرية"]
    }

    for topic, keywords in topic_cues.items():
        if any(kw in lower_msg for kw in keywords):
            if topic not in current_interests:
                current_interests.append(topic)

    # 2. Detect Communication Style & Tone
    if any(w in lower_msg for w in ["أعتقد", "في رأيي", "أرى أن", "i think", "hypothesis", "أقترح", "أفترض"]):
        detected_style = "تأملي استنتاجي (Hypothesis-Driven & Reflective)"
    elif any(w in lower_msg for w in ["كيف", "ما الدليل", "ما المعيار", "هل يوجد بحث", "evidence", "دراسة", "إحصائية"]):
        detected_style = "أكاديمي تحليلي دقيق (Evidence-Based & Rigorous)"
    elif any(w in lower_msg for w in ["تطبيق", "مستشفى", "تمريض عملي", "سريري", "ممارسة", "clinical", "bedside"]):
        detected_style = "سريري عملي واقعي (Applied Clinical Practice)"

    # 3. Detect and Record Ideas / Hypotheses / Critical Notes
    idea_markers = [
        ("فرضية بحثية", ["أفترض أن", "هل يمكن أن", "ما إذا كان", "فرضيتي", "hypothesis", "could it be that"]),
        ("فكرة دراسة أو مشروع", ["أفكر في عمل", "أريد دراسة", "فكرة بحث", "مشروع تخرج", "دراسة أثر", "my research project"]),
        ("ملاحظة نقدية وسريرية", ["لكن المشكلة أن", "الواقع مختلف", "العيب في ذلك", "هناك تعارض", "the limitation is", "however in practice"])
    ]

    detected_new_idea = None
    for idea_type, cues in idea_markers:
        if any(cue in lower_msg for cue in cues):
            inferred = user_message.strip()
            # Store in dedicated researcher_ideas table
            cursor.execute("""
                INSERT INTO researcher_ideas (session_id, idea_type, raw_statement, inferred_meaning, suggested_direction)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session_id,
                idea_type,
                user_message,
                f"فكرة مسجلة من الباحث: {inferred[:150]}",
                "يوصى بدمجها مع أحدث دراسات ومراجع معلوماتية التمريض المنشورة."
            ))

            if inferred[:100] not in current_ideas:
                current_ideas.append(inferred[:100])
                detected_new_idea = {"type": idea_type, "text": inferred}
            break

    # 4. Track preferred vocabulary (words of 4+ letters)
    tokens = [w for w in re.findall(r'\b[\w\u0600-\u06FF]{4,}\b', user_message) if len(w) > 3]
    for t in tokens[:5]:
        if t not in current_vocab:
            current_vocab.append(t)
    current_vocab = current_vocab[-20:] # Keep last 20 characteristic tokens

    # Update profile in DB
    cursor.execute("""
        UPDATE researcher_profile
        SET research_interests = ?,
            communication_style = ?,
            synthesized_ideas = ?,
            vocabulary_preferences = ?,
            last_active = CURRENT_TIMESTAMP
        WHERE session_id = ?
    """, (
        json.dumps(current_interests[-8:]),
        detected_style,
        json.dumps(current_ideas[-10:]),
        json.dumps(current_vocab),
        session_id
    ))
    conn.commit()
    conn.close()

    return {
        "style": detected_style,
        "interests": current_interests,
        "ideas_count": len(current_ideas),
        "new_idea": detected_new_idea
    }

def get_researcher_context(session_id):
    """Fetches the researcher's cognitive profile to contextualize the conversation logically."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM researcher_profile WHERE session_id = ?", (session_id,))
    prof = cursor.fetchone()

    cursor.execute("SELECT * FROM researcher_ideas WHERE session_id = ? ORDER BY id DESC LIMIT 5", (session_id,))
    recent_ideas = cursor.fetchall()
    conn.close()

    if not prof:
        return {
            "style": "تحليلي أكاديمي منطقي",
            "interests": ["معلوماتية التمريض"],
            "ideas": []
        }

    return {
        "style": prof['communication_style'] or "تحليلي أكاديمي دقيق",
        "interests": json.loads(prof['research_interests']) if prof['research_interests'] else [],
        "ideas": [r['raw_statement'] for r in recent_ideas],
        "ideas_list": [{
            "id": r['id'],
            "type": r['idea_type'],
            "text": r['raw_statement'],
            "created_at": r['created_at']
        } for r in recent_ideas]
    }
