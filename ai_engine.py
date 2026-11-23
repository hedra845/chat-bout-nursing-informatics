import re
import math
from collections import Counter
import json
import os
import requests
from database import get_db_connection

def is_arabic_text(text):
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    latin_chars = len(re.findall(r'[a-zA-Z]', text))
    return arabic_chars > 0 and arabic_chars >= latin_chars * 0.5

def extract_keywords(text):
    stopwords = {
        'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'in', 'for', 'to', 'of', 'with', 'by',
        'what', 'how', 'why', 'who', 'when', 'where', 'can', 'does', 'do', 'are', 'was', 'were', 'explain',
        'tell', 'me', 'about', 'summarize', 'definition', 'meaning',
        'من', 'إلى', 'عن', 'على', 'في', 'ما', 'هو', 'هي', 'كيف', 'لماذا', 'هل', 'مع', 'هذا', 'هذه', 'أن',
        'اشرح', 'وضح', 'عرف', 'ماهو', 'ماهي', 'ماذا', 'عبر', 'كل', 'بين'
    }
    words = re.findall(r'\b[\w\u0600-\u06FF]{3,}\b', text.lower())
    filtered = [w for w in words if w not in stopwords]
    return filtered

def search_relevant_chunks(query, book_id=None, limit=3):
    conn = get_db_connection()
    cursor = conn.cursor()

    if book_id:
        cursor.execute("SELECT id, book_id, page_number, content FROM book_chunks WHERE book_id = ?", (book_id,))
    else:
        cursor.execute("SELECT id, book_id, page_number, content FROM book_chunks")
    
    rows = cursor.fetchall()

    # Also retrieve matching benchmark dataset entries as authoritative references
    cursor.execute("SELECT * FROM reference_dataset")
    dataset_rows = cursor.fetchall()
    conn.close()

    term_synonyms = {
        "هدف": "objectives objective goal goals outcome purpose",
        "الهدف": "objectives objective goal goals outcome purpose",
        "اهداف": "objectives objective goals",
        "الأهداف": "objectives objective goals",
        "شرح": "explain describe detail summary understand define",
        "ادوار": "roles responsibilities role",
        "أدوار": "roles responsibilities role",
        "مسؤوليات": "responsibilities responsibility duty duties",
        "فرص": "opportunities opportunity career",
        "تعليم": "education training learning academic",
        "بيانات": "data", "معلومات": "information", "معرفة": "knowledge", "حكمة": "wisdom",
        "هرم": "pyramid hierarchy dikw", "مصطلحات": "terminologies nanda nic noc snomed",
        "تمريض": "nursing", "تشخيص": "diagnosis nanda", "تدخلات": "interventions nic",
        "نتائج": "outcomes noc", "دعم القرار": "decision support cdss",
        "سجل صحي": "electronic health record ehr emr", "أخطاء دوائية": "medication error alert",
        "خصوصية": "hipaa privacy security", "مجموعة البيانات": "nmds minimum data set",
        "عن بعد": "telehealth telemedicine"
    }

    query_lower = query.lower()
    expanded_terms = []
    for ar_term, en_map in term_synonyms.items():
        if ar_term in query_lower:
            expanded_terms.extend(en_map.split())

    q_tokens = extract_keywords(query) + expanded_terms
    if not q_tokens:
        q_tokens = query.lower().split()

    scored_chunks = []

    # 1. Search in Book Chunks
    for row in rows:
        chunk_text = row['content']
        chunk_tokens = extract_keywords(chunk_text)
        chunk_counter = Counter(chunk_tokens)
        
        score = 0
        for token in q_tokens:
            if token in chunk_counter:
                score += chunk_counter[token] * 1.5
            elif any(token in ct for ct in chunk_counter):
                score += 0.5
        
        if any(term in chunk_text.lower() for term in q_tokens if len(term) > 3):
            score += 1.0

        if score > 0:
            scored_chunks.append({
                'id': row['id'],
                'book_id': row['book_id'],
                'page_number': row['page_number'],
                'content': chunk_text,
                'source_type': 'book',
                'score': score
            })

    # 2. Search in Reference Dataset (Benchmark Knowledge Base)
    for ds in dataset_rows:
        ds_combined = f"{ds['concept_name_en']} {ds['concept_name_ar']} {ds['clinical_definition']} {ds['clinical_importance']} {ds['real_world_example']}"
        ds_tokens = extract_keywords(ds_combined)
        ds_counter = Counter(ds_tokens)

        score = 0
        for token in q_tokens:
            if token in ds_counter:
                score += ds_counter[token] * 2.0  # Dataset has high authoritative weight
            elif any(token in ct for ct in ds_counter):
                score += 0.8

        if any(term in ds_combined.lower() for term in q_tokens if len(term) > 3):
            score += 1.5

        if score > 0:
            scored_chunks.append({
                'id': ds['id'],
                'book_id': None,
                'page_number': f"Dataset [{ds['concept_code']}]",
                'content': f"【قاعدة بيانات المرجع: {ds['concept_name_ar']} / {ds['concept_name_en']}】\n"
                           f"• التعريف السريري: {ds['clinical_definition']}\n"
                           f"• الأهمية الطبية: {ds['clinical_importance']}\n"
                           f"• مثال واقعي: {ds['real_world_example']}\n"
                           f"• المعيار الدولي: {ds['standard_mapping']}",
                'source_type': 'dataset',
                'score': score
            })

    scored_chunks.sort(key=lambda x: x['score'], reverse=True)
    return scored_chunks[:limit]

def record_or_update_question(question_text):
    conn = get_db_connection()
    cursor = conn.cursor()

    q_keywords = extract_keywords(question_text)
    q_tokens_set = set(q_keywords)

    cursor.execute("SELECT id, canonical_question, normalized_keywords, frequency FROM repeated_questions")
    existing_questions = cursor.fetchall()

    matched_id = None
    best_similarity = 0.0

    for eq in existing_questions:
        eq_keywords_set = set(eq['normalized_keywords'].split())
        if not q_tokens_set or not eq_keywords_set:
            continue
        intersection = len(q_tokens_set.intersection(eq_keywords_set))
        union = len(q_tokens_set.union(eq_keywords_set))
        similarity = intersection / union if union > 0 else 0

        if similarity > best_similarity:
            best_similarity = similarity
            matched_id = eq['id']

    if matched_id and best_similarity >= 0.35:
        cursor.execute("""
            UPDATE repeated_questions 
            SET frequency = frequency + 1, last_asked = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (matched_id,))
    else:
        lower_q = question_text.lower()
        category = "General Nursing Informatics"
        if any(k in lower_q for k in ["dikw", "data", "wisdom", "knowledge", "هرم", "بيانات", "حكمة"]):
            category = "Core Concepts (DIKW)"
        elif any(k in lower_q for k in ["nanda", "nic", "noc", "icnp", "snomed", "loinc", "terminology", "مصطلحات", "تشخيص"]):
            category = "Standardized Terminologies"
        elif any(k in lower_q for k in ["ehr", "emr", "cpoe", "emar", "cdss", "decision support", "alert", "سجل", "دعم القرار"]):
            category = "Clinical Systems & CDSS"
        elif any(k in lower_q for k in ["hipaa", "privacy", "security", "ethical", "legal", "خصوصية", "أمان"]):
            category = "Ethics & Healthcare Laws"
        elif any(k in lower_q for k in ["telehealth", "telemedicine", "remote", "wearable", "عن بعد"]):
            category = "Telehealth & Innovation"
        elif any(k in lower_q for k in ["nmds", "minimum data", "dataset", "الحد الأدنى"]):
            category = "Nursing Minimum Data Set"

        cursor.execute("""
            INSERT INTO repeated_questions (canonical_question, normalized_keywords, category, frequency)
            VALUES (?, ?, ?, 1)
        """, (question_text.strip(), " ".join(q_keywords), category))

    conn.commit()
    conn.close()

def synthesize_cognitive_understanding(query, context_chunks, style, past_ideas):
    """
    Synthesizes what the AI actually understood from the context & inquiry,
    addressing exactly what the researcher intended to ask.
    """
    lower_q = query.lower()
    
    # 1. Identify Core Intent & Topic
    concepts = []
    if any(k in lower_q for k in ["هدف", "الهدف", "أهداف", "objectiv", "goal"]):
        concepts.append("الأهداف التعليمية والسريرية المحددة في المحاضرة/المرجع المرفوع")
    if any(k in lower_q for k in ["دور", "أدوار", "مسؤوليات", "role", "responsibilit"]):
        concepts.append("أدوار ومسؤوليات ممرض المعلوماتية السريرية")
    if any(k in lower_q for k in ["dikw", "بيانات", "معلومات", "معرفة", "حكمة"]):
        concepts.append("هرمية DIKW (تحويل البيانات الأولية لمؤشرات رعاية ثم حكمة سريرية)")
    if any(k in lower_q for k in ["cdss", "قرار", "alert", "إنذار", "تنبيه", "fatigue"]):
        concepts.append("نظم دعم القرار الطبي والتوازن مع إجهاد التنبيهات (Alert Fatigue)")
    if any(k in lower_q for k in ["ehr", "emr", "سجل", "ملف", "cpoe"]):
        concepts.append("توثيق السجل الصحي الإلكتروني وأثر إدخال الأوامر حاسوبياً")
    if any(k in lower_q for k in ["nanda", "nic", "noc", "icnp", "snomed", "مصطلحات"]):
        concepts.append("المصطلحات الموحدة لضمان التوافقية ومنع تضارب بيانات التمريض")
    if any(k in lower_q for k in ["safety", "سلامة", "أخطاء", "error"]):
        concepts.append("حماية المريض وتقليل الأخطاء الدوائية عبر التحقق المزدوج والباركود")

    if not concepts:
        concepts.append("المبادئ التكاملية بين الممارسة التمريضية والأنظمة الحاسوبية")

    return concepts

def generate_local_response(query, context_chunks, preferred_lang=None, researcher_profile=None):
    """
    Cognitive Reasoning Engine:
    Does NOT merely copy book text. Instead, it explains:
    1. 'ما فهمه المساعد من سؤالك والمراجع' (Cognitive Understanding).
    2. 'التحليل والاستنتاج النقدي' (Critical Synthesis & Clinical Impact).
    3. 'ربط الفكرة بفرضيات الباحث السابقة' (Research Continuity).
    4. 'تطبيق ومسار بحثي مقترح' (Actionable Future Inquiries).
    """
    is_ar = (preferred_lang == 'ar') if preferred_lang in ['ar', 'en'] else is_arabic_text(query)

    style = researcher_profile.get("style", "تحليلي أكاديمي منطقي") if researcher_profile else "تحليلي أكاديمي منطقي"
    past_ideas = researcher_profile.get("ideas", []) if researcher_profile else []

    concepts = synthesize_cognitive_understanding(query, context_chunks, style, past_ideas)

    # Detect if user is asking about lecture goals / objectives
    is_asking_objective = any(k in query.lower() for k in ["هدف", "الهدف", "أهداف", "objectiv", "goal"])

    if is_ar:
        response = f"### 🧠 فهم واستنتاج المساعد الذكي (نظام الحوار: {style}):\n\n"

        if is_asking_objective and context_chunks:
            response += f"📌 **ما فهمته من طلبك بخصوص (الهدف):**\n\n"
            response += f"أنت تطلب توضيح وشرح **الأهداف التعليمية والسريرية (Learning Objectives)** المحددة في المحاضرة/المرجع المرفوع.\n\n"
            response += f"المغزى هنا هو معرفة المخرجات التي يُتوقع من الممرض أو الباحث إتقانها بعد دراسة هذه المادة، وتحديداً: تعريف تخصص معلوماتية التمريض، واستيعاب الأدوار والمسؤوليات المهنية، والفرص التعليمية المتاحة.\n\n"
            
            response += f"📖 **النص المباشر لأهداف المحاضرة من المرجع (صفحة {context_chunks[0]['page_number']}):**\n\n"
            response += f"> {context_chunks[0]['content']}\n\n"

            response += "🔬 **التفصيل والشرح السريري لهذه الأهداف:**\n\n"
            response += "1. **تعريف معلوماتية التمريض (Define NI):** الانتقال من مجرد استخدام الحاسوب إلى الفهم المتكامل لدمج علوم التمريض مع علوم الحاسوب والبيانات لدعم القرار.\n\n"
            response += "2. **تعداد الأدوار والمسؤوليات (Roles & Responsibilities):** تحديد هل دورك كممرض معلوماتي هو محلل نظم سريرية (Clinical Analyst)، أم منسق تدريب (Trainer)، أم مطور سياسات رقمية وحماية بيانات.\n\n"
            response += "3. **استثمار الفرص والمسار التعليمي (Opportunities & Education):** التعرف على الشهادات المهنية المعتمدة وكيفية توظيف التكنولوجيا في الترقية الأكاديمية والمهنية داخل المستشفى.\n\n"
            response += "💡 **سؤال للمتابعة:** هل تود أن نتعمق في شرح أيٍ من هذه الأدوار بالتفصيل؟ أو ننتقل للنقطة التالية في المحاضرة؟\n"
            return response

        # Section 1: What the AI understood
        response += f"📌 **ما استخلصه وفهمه المساعد من طرحك:**\n\n"
        response += f"فهمت من استفسارك أنك تبحث في: **{', '.join(concepts)}**.\n\n"
        response += f"المغزى الجوهري هنا ليس مجرد نصوص عامة، بل **كيف ينعكس هذا المفهوم على الممارسة التمريضية العملية عند سرير المريض (Bedside Decision Making)**، وتجنب الخطأ البشري قبل وقوعه.\n\n"

        if past_ideas:
            response += f"- 💡 *ربطاً بأفكارك المسجلة سابقاً:* أرى أن هذا يتكامل بشكل مباشر مع فرضيتك السابقة حول: `{past_ideas[0][:75]}...`.\n\n"

        # Section 2: Reference Evidence (Concise and clearly framed as proof)
        if context_chunks:
            response += f"📖 **الدليل المستخلص من المرجع لدعم هذا الفهم (صفحة {context_chunks[0]['page_number']}):**\n\n"
            response += f"> {context_chunks[0]['content']}\n\n"

        # Section 3: Critical Analysis & Deep Thinking
        response += "🔬 **التحليل المنطقي والرؤية السريرية (Clinical & Critical Insights):**\n\n"
        response += "1. **الأثر المباشر على التمريض:** توحيد لغة التوثيق (مثل SNOMED CT و ICNP) ينقل التمريض من مجرد مهام روتينية إلى علم بيانات تراكمي يثبت فاعلية الرعاية التمريضية في سرعة شفاء المريض.\n\n"
        response += "2. **العقبة السريرية الحقيقية (Challenge):** أكبر تحدٍ يواجه الممرضين مع هذه النظم هو *إجهاد الإنذارات (Alert Fatigue)*؛ إذا كانت التنبيهات كثيرة وغير حرجة، يتجاهلها الممرض لا إرادياً، والحل يكمن في تصنيف التنبيهات الذكية حسب خطورتها.\n\n"
        response += "3. **مسار يمكنك سؤالي عنه أو اختباره:** هل تود أن نناقش كيفية صياغة هذه الفكرة في استبيان أو بحث ميداني؟ أو نسأل عن آلية برمجية معينة للربط بين الأقسام؟ يمكنك سؤالي في أي زاوية تريدها!\n"

    else:
        response = f"### 🧠 AI Synthesis & Cognitive Interpretation (Style: {style}):\n\n"
        response += "📌 **What I Inferred from Your Inquiry:**\n\n"
        response += f"Your inquiry investigates: **{', '.join(concepts)}**.\n\n"
        response += "Beyond technical definitions, the core objective is understanding how structured health informatics empowers bedside nursing decisions, reduces cognitive load, and safeguards patient outcomes.\n\n"

        if context_chunks:
            response += f"📖 **Supporting Textbook Evidence (Page {context_chunks[0]['page_number']}):**\n\n"
            response += f"> {context_chunks[0]['content']}\n\n"

        response += "🔬 **Clinical & Methodological Synthesis:**\n\n"
        response += "1. **Data-Driven Nursing Impact:** Standardized terminologies convert unstructured bedside notes into actionable, measurable clinical outcomes.\n\n"
        response += "2. **Clinical Friction & Alert Fatigue:** High-frequency, non-actionable alarms desensitize clinicians; effective CDSS requires intelligent severity tiering.\n\n"
        response += "3. **Next Inquiries You Can Explore:** You can ask me how to translate this into a quantitative study, explore clinical algorithms, or contrast competing terminologies.\n"

    return response

def call_gemini_api(api_key, query, context_chunks, preferred_lang=None, researcher_profile=None):
    """
    Open-domain, highly synthesized Gemini reasoning:
    Instructs Gemini to deeply interpret and explain what it understood,
    think critically, debate, and respond to ANY open question without bounds.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    is_ar = (preferred_lang == 'ar') if preferred_lang in ['ar', 'en'] else is_arabic_text(query)
    lang_instruction = "Respond in fluent, articulate Arabic." if is_ar else "Respond in fluent, precise English."

    style = researcher_profile.get("style", "تحليلي أكاديمي منطقي") if researcher_profile else "تحليلي أكاديمي منطقي"
    past_ideas = researcher_profile.get("ideas", []) if researcher_profile else []
    ideas_summary = f"Researcher's recorded ideas & past thoughts: {', '.join(past_ideas[:3])}" if past_ideas else "No past recorded thoughts yet."

    context_str = ""
    for idx, c in enumerate(context_chunks, 1):
        context_str += f"\n--- Reference Excerpt {idx} (Page {c['page_number']}) ---\n{c['content']}\n"

    system_instruction = (
        "You are an Advanced Autonomous Nursing Informatics Research Partner, Academic Mentor, and Intelligent Intellectual Peer. "
        "CRITICAL INSTRUCTION: Do NOT just quote or dump textbook definitions. "
        "The researcher specifically demands that you EXPLAIN WHAT YOU UNDERSTOOD from their question and the references. "
        "Synthesize the deeper clinical meaning, provide critical reasoning, and engage in an open-ended dialogue. "
        "You are capable of discussing ANY open scientific or general question the researcher asks. "
        f"The researcher's detected thinking style is: '{style}'. Adapt your tone to match. "
        f"{ideas_summary} "
        "Format your answer with clear section titles:\n"
        "1. 📌 ما فهمته من سؤالك وسياق البحث (What I Understood)\n"
        "2. 📖 الدليل من المراجع (Supporting Evidence - brief)\n"
        "3. 🔬 التحليل السريري والنقدي (Critical & Clinical Synthesis)\n"
        "4. 💡 أسئلة ومسارات مقترحة للنقاش (Next Questions to Explore)\n"
        f"{lang_instruction}"
    )

    user_prompt = f"""Available Textbook Knowledge (Use if relevant, or rely on your broader intelligence):
{context_str}

Researcher's Inquiry / Open Question:
{query}

Please provide your thoughtful, synthesized response explaining your understanding and insights."""

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": system_instruction + "\n\n" + user_prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 1500
        }
    }

    headers = {"Content-Type": "application/json"}
    
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=20)
        if res.status_code == 200:
            data = res.json()
            generated_text = data['candidates'][0]['content']['parts'][0]['text']
            return generated_text, "Gemini AI (Deep Reasoning Engine)"
        else:
            err_msg = f"Gemini API returned status {res.status_code}: {res.text}"
            return None, err_msg
    except Exception as e:
        return None, str(e)
