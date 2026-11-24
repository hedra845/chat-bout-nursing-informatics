import os
import json
import uuid
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename

try:
    from whitenoise import WhiteNoise
    HAS_WHITENOISE = True
except ImportError:
    HAS_WHITENOISE = False

from database import get_db_connection, init_db
from book_analyzer import analyze_and_index_book
from ai_engine import search_relevant_chunks, record_or_update_question, generate_local_response, call_gemini_api
from translator import translate_to_arabic
from researcher_memory import analyze_and_update_researcher_profile, get_researcher_context

app = Flask(__name__, static_folder='static', template_folder='templates')

if HAS_WHITENOISE:
    app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/', prefix='static/')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'md'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- WEB PAGE ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

# --- API ROUTES ---

@app.route('/api/books', methods=['GET'])
def get_books():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.*, COUNT(c.id) as chunk_count 
        FROM books b 
        LEFT JOIN book_chunks c ON b.id = c.book_id 
        GROUP BY b.id 
        ORDER BY b.id DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    books = []
    for r in rows:
        books.append({
            "id": r['id'],
            "title": r['title'],
            "filename": r['filename'],
            "file_type": r['file_type'],
            "total_pages": r['total_pages'],
            "total_words": r['total_words'],
            "summary": r['summary'],
            "topics": json.loads(r['topics']) if r['topics'] else [],
            "chunks": r['chunk_count'],
            "created_at": r['created_at']
        })
    return jsonify({"success": True, "books": books})

@app.route('/api/books/upload', methods=['POST'])
def upload_book():
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "لم يتم اختيار أي ملف"}), 400
        
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({"success": False, "error": "اسم الملف فارغ"}), 400

        original_name = file.filename
        ext = os.path.splitext(original_name)[1].lower()

        if ext.replace('.', '') not in ALLOWED_EXTENSIONS:
            return jsonify({"success": False, "error": "صيغة غير مدعومة. يرجى رفع ملفات PDF أو TXT أو MD"}), 400

        # Preserve Arabic / Unicode filenames safely
        safe_base = secure_filename(os.path.splitext(original_name)[0])
        if not safe_base:
            safe_base = "book_reference"

        unique_name = f"{uuid.uuid4().hex[:8]}_{safe_base}{ext}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
        file.save(save_path)

        custom_title = request.form.get('title', '').strip()
        display_title = custom_title if custom_title else os.path.splitext(original_name)[0]

        result = analyze_and_index_book(save_path, original_name, display_title)

        return jsonify({
            "success": True,
            "message": f"تم بنجاح تحليل وفهرسة مرجع '{result['title']}'",
            "book": result
        })
    except Exception as e:
        print("Upload error:", e)
        return jsonify({"success": False, "error": f"حدث خطأ أثناء معالجة وحفظ الكتاب: {str(e)}"}), 500

@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM book_chunks WHERE book_id = ?", (book_id,))
    cursor.execute("DELETE FROM notes WHERE book_id = ?", (book_id,))
    cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Book and associated notes deleted"})

# --- CHAT & REPETITION TRACKING ROUTES ---

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json or {}
    message = data.get('message', '').strip()
    session_id = data.get('session_id', 'default_session')
    book_id = data.get('book_id') # Can be None (search all books) or int
    api_key = data.get('api_key', '').strip()
    mode = data.get('mode', 'auto') # 'local', 'gemini', or 'auto'
    preferred_lang = data.get('lang', 'auto') # 'auto', 'ar', or 'en'

    if not message:
        return jsonify({"success": False, "error": "Message is required"}), 400

    # 1. Track & record question repetition
    record_or_update_question(message)

    # 2. Analyze & Save Researcher's Thoughts, Hypotheses, and Speech Tone
    profile_update = analyze_and_update_researcher_profile(session_id, message)
    researcher_ctx = get_researcher_context(session_id)

    # 3. Retrieve recent conversation history for memory continuity
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role, content FROM chat_messages 
        WHERE session_id = ? 
        ORDER BY id DESC LIMIT 6
    """, (session_id,))
    recent_history = [dict(r) for r in reversed(cursor.fetchall())]

    # Check for server-configured Gemini API Key if not passed by client
    if not api_key:
        cursor.execute("SELECT value FROM system_settings WHERE key = 'gemini_api_key'")
        sys_key_row = cursor.fetchone()
        if sys_key_row and sys_key_row['value']:
            api_key = sys_key_row['value'].strip()
    conn.close()

    # 4. Retrieve relevant textbook knowledge chunks (RAG)
    relevant_chunks = search_relevant_chunks(message, book_id=book_id if book_id else None, limit=4)

    # 5. Model Generation Choice (Adapting to researcher style & memory)
    model_used = "Built-in Nursing Informatics AI"
    response_text = ""

    if (mode == 'gemini' or (mode == 'auto' and api_key)) and api_key:
        ai_resp, provider = call_gemini_api(api_key, message, relevant_chunks, preferred_lang=preferred_lang, researcher_profile=researcher_ctx, chat_history=recent_history)
        if ai_resp:
            response_text = ai_resp
            model_used = provider
        else:
            # Fallback to local
            response_text = generate_local_response(message, relevant_chunks, preferred_lang=preferred_lang, researcher_profile=researcher_ctx)
            model_used = f"Built-in AI (Gemini Fallback: {provider})"
    else:
        response_text = generate_local_response(message, relevant_chunks, preferred_lang=preferred_lang, researcher_profile=researcher_ctx)

    # 6. Save to Chat History
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_messages (session_id, book_id, role, content, model_used)
        VALUES (?, ?, 'user', ?, ?)
    """, (session_id, book_id, message, model_used))
    cursor.execute("""
        INSERT INTO chat_messages (session_id, book_id, role, content, sources, model_used)
        VALUES (?, ?, 'assistant', ?, ?, ?)
    """, (session_id, book_id, response_text, json.dumps(relevant_chunks), model_used))
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "response": response_text,
        "sources": relevant_chunks,
        "model_used": model_used,
        "researcher_profile": {
            "style": profile_update["style"],
            "interests": profile_update["interests"],
            "new_idea": profile_update["new_idea"]
        }
    })

# --- RESEARCHER PROFILE & MEMORY ENDPOINTS ---

@app.route('/api/dataset', methods=['GET'])
def get_reference_dataset():
    domain = request.args.get('domain', '').strip()
    search = request.args.get('search', '').strip().lower()

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM reference_dataset WHERE 1=1"
    params = []

    if domain:
        query += " AND domain = ?"
        params.append(domain)

    query += " ORDER BY id ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    dataset = []
    for r in rows:
        if search:
            combined = f"{r['concept_name_en']} {r['concept_name_ar']} {r['clinical_definition']} {r['standard_mapping']}".lower()
            if search not in combined:
                continue

        dataset.append({
            "id": r['id'],
            "code": r['concept_code'],
            "domain": r['domain'],
            "name_en": r['concept_name_en'],
            "name_ar": r['concept_name_ar'],
            "definition": r['clinical_definition'],
            "importance": r['clinical_importance'],
            "example": r['real_world_example'],
            "standard": r['standard_mapping'],
            "source": r['source_reference']
        })

    return jsonify({"success": True, "dataset": dataset, "count": len(dataset)})

@app.route('/api/researcher/profile', methods=['GET'])
def get_profile():
    session_id = request.args.get('session_id', 'default_session')
    ctx = get_researcher_context(session_id)
    return jsonify({"success": True, "profile": ctx})

@app.route('/api/researcher/ideas', methods=['GET'])
def get_ideas():
    session_id = request.args.get('session_id', 'default_session')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM researcher_ideas WHERE session_id = ? ORDER BY id DESC", (session_id,))
    rows = cursor.fetchall()
    conn.close()

    ideas = [{
        "id": r['id'],
        "type": r['idea_type'],
        "statement": r['raw_statement'],
        "meaning": r['inferred_meaning'],
        "direction": r['suggested_direction'],
        "created_at": r['created_at']
    } for r in rows]

    return jsonify({"success": True, "ideas": ideas})

@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    session_id = request.args.get('session_id', 'default_session')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM chat_messages 
        WHERE session_id = ? 
        ORDER BY id ASC
    """, (session_id,))
    rows = cursor.fetchall()
    conn.close()

    history = []
    for r in rows:
        history.append({
            "id": r['id'],
            "role": r['role'],
            "content": r['content'],
            "sources": json.loads(r['sources']) if r['sources'] else [],
            "model_used": r['model_used'],
            "created_at": r['created_at']
        })
    return jsonify({"success": True, "history": history})

# --- REPEATED QUESTIONS & ANALYTICS ---

@app.route('/api/translate', methods=['POST'])
def translate_content():
    data = request.json or {}
    text = data.get('text', '').strip()
    api_key = data.get('api_key', '').strip()

    if not text:
        return jsonify({"success": False, "error": "No content provided to translate"}), 400

    translated_text, provider = translate_to_arabic(text, api_key=api_key if api_key else None)
    return jsonify({
        "success": True,
        "translated_text": translated_text,
        "provider": provider
    })

@app.route('/api/analytics/repeated-questions', methods=['GET'])
def get_repeated_questions():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM repeated_questions 
        ORDER BY frequency DESC, last_asked DESC 
        LIMIT 20
    """)
    rows = cursor.fetchall()
    conn.close()

    questions = []
    for r in rows:
        questions.append({
            "id": r['id'],
            "question": r['canonical_question'],
            "category": r['category'],
            "frequency": r['frequency'],
            "first_asked": r['first_asked'],
            "last_asked": r['last_asked']
        })
    return jsonify({"success": True, "questions": questions})

# --- CLINICAL & STUDY NOTES ---

@app.route('/api/notes', methods=['GET'])
def get_notes():
    book_id = request.args.get('book_id')
    category = request.args.get('category')
    search = request.args.get('search', '').strip().lower()

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT n.*, b.title as book_title FROM notes n LEFT JOIN books b ON n.book_id = b.id WHERE 1=1"
    params = []

    if book_id:
        query += " AND n.book_id = ?"
        params.append(book_id)
    if category:
        query += " AND n.category = ?"
        params.append(category)

    query += " ORDER BY n.is_pinned DESC, n.updated_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    notes = []
    for r in rows:
        if search:
            if search not in r['title'].lower() and search not in r['content'].lower():
                continue

        notes.append({
            "id": r['id'],
            "book_id": r['book_id'],
            "book_title": r['book_title'] or "General Note",
            "title": r['title'],
            "content": r['content'],
            "category": r['category'],
            "tags": json.loads(r['tags']) if r['tags'] else [],
            "is_pinned": bool(r['is_pinned']),
            "created_at": r['created_at'],
            "updated_at": r['updated_at']
        })
    return jsonify({"success": True, "notes": notes})

@app.route('/api/notes', methods=['POST'])
def create_note():
    data = request.json or {}
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    book_id = data.get('book_id')
    category = data.get('category', 'General Note')
    tags = data.get('tags', [])

    if not title or not content:
        return jsonify({"success": False, "error": "Title and content are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notes (book_id, title, content, category, tags, is_pinned)
        VALUES (?, ?, ?, ?, ?, 0)
    """, (book_id if book_id else None, title, content, category, json.dumps(tags)))
    note_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({"success": True, "note_id": note_id, "message": "Note saved successfully"})

@app.route('/api/notes/<int:note_id>/pin', methods=['POST'])
def toggle_pin_note(note_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notes SET is_pinned = ((is_pinned | 1) - (is_pinned & 1)) WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/stats', methods=['GET'])
def get_dashboard_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total_books, SUM(total_pages) as total_pages FROM books")
    b_stat = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*) as total_messages FROM chat_messages")
    m_stat = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) as total_notes FROM notes")
    n_stat = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) as total_questions, SUM(frequency) as total_asked FROM repeated_questions")
    q_stat = cursor.fetchone()

    cursor.execute("SELECT category, COUNT(*) as count FROM notes GROUP BY category")
    notes_by_cat = {r['category']: r['count'] for r in cursor.fetchall()}

    conn.close()

    return jsonify({
        "success": True,
        "stats": {
            "books": b_stat['total_books'] or 0,
            "pages": b_stat['total_pages'] or 0,
            "messages": m_stat['total_messages'] or 0,
            "notes": n_stat['total_notes'] or 0,
            "unique_questions": q_stat['total_questions'] or 0,
            "total_queries_logged": q_stat['total_asked'] or 0,
            "notes_by_cat": notes_by_cat
        }
    })

# --- SYSTEM & ADMIN DASHBOARD ROUTES ---

@app.route('/api/admin/settings', methods=['GET', 'POST'])
def manage_settings():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        data = request.json or {}
        for k, v in data.items():
            cursor.execute("""
                INSERT INTO system_settings (key, value, updated_at) 
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
            """, (k, str(v)))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "تم حفظ الإعدادات بنجاح"})

    cursor.execute("SELECT key, value FROM system_settings")
    rows = cursor.fetchall()
    settings = {r['key']: r['value'] for r in rows}
    
    # Hide full Gemini key in GET response for security
    raw_key = settings.get('gemini_api_key', '')
    masked_key = (raw_key[:6] + "..." + raw_key[-4:]) if len(raw_key) > 10 else raw_key

    # System overview stats for Admin
    cursor.execute("SELECT COUNT(*) as c FROM books")
    total_books = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) as c FROM book_chunks")
    total_chunks = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) as c FROM reference_dataset")
    total_dataset = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) as c FROM chat_messages")
    total_chats = cursor.fetchone()['c']
    conn.close()

    return jsonify({
        "success": True,
        "settings": settings,
        "masked_gemini_key": masked_key,
        "is_gemini_connected": bool(raw_key),
        "system_status": {
            "total_books": total_books,
            "total_chunks": total_chunks,
            "total_dataset_entries": total_dataset,
            "total_chats": total_chats,
            "engine": "Hybrid (RAG + Gemini 1.5/2.0 Flash Fallback)",
            "status": "Online & Operational"
        }
    })

@app.route('/api/admin/test-gemini', methods=['POST'])
def test_gemini_connection():
    data = request.json or {}
    key = data.get('api_key', '').strip()
    if not key:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM system_settings WHERE key = 'gemini_api_key'")
        row = cursor.fetchone()
        conn.close()
        if row and row['value']:
            key = row['value'].strip()

    if not key:
        return jsonify({"success": False, "error": "لم يتم إدخال مفتاح Gemini API"}), 400

    test_prompt = "Say 'OK' in one word if connected."
    res_text, provider = call_gemini_api(key, test_prompt, [], preferred_lang='en')
    if res_text:
        return jsonify({"success": True, "message": "تم الاتصال بـ Google Gemini API بنجاح!", "provider": provider, "sample": res_text[:100]})
    else:
        return jsonify({"success": False, "error": f"فشل الاتصال: {provider}"}), 400

if __name__ == '__main__':
    init_db()
    print("Starting Nursing Informatics Chatbot & Analytics Server on http://localhost:5000 ...")
    app.run(host='0.0.0.0', port=5000, debug=False)
