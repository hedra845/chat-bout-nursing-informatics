import re
from deep_translator import MyMemoryTranslator, GoogleTranslator

def clean_and_chunk_text(text):
    """Splits into manageable sentences/paragraphs for the translator."""
    lines = text.split('\n')
    return [l for l in lines]

def translate_with_package(text):
    """
    Translates text to Arabic using deep-translator.
    First tries MyMemoryTranslator (which does not block or return TooManyRequests),
    with GoogleTranslator as a fallback.
    """
    if not text or not text.strip():
        return ""

    lines = text.split('\n')
    translated_lines = []

    # Initialize MyMemoryTranslator (Free, high quota, reliable, no IP rate limiting)
    memory_tr = MyMemoryTranslator(source='en-US', target='ar-SA')

    for line in lines:
        stripped = line.strip()
        if not stripped:
            translated_lines.append("")
            continue

        prefix = ""
        content = stripped
        if stripped.startswith("### "):
            prefix = "### "
            content = stripped[4:]
        elif stripped.startswith("## "):
            prefix = "## "
            content = stripped[3:]
        elif stripped.startswith("- "):
            prefix = "- "
            content = stripped[2:]
        elif stripped.startswith("• "):
            prefix = "• "
            content = stripped[2:]
        elif stripped.startswith("> "):
            prefix = "> "
            content = stripped[2:]
        elif re.match(r'^\d+\.\s+', stripped):
            match = re.match(r'^(\d+\.\s+)(.*)$', stripped)
            prefix = match.group(1)
            content = match.group(2)

        # Strip bold stars for translation clarity
        clean_chunk = content.replace('**', '').strip()
        if not clean_chunk:
            translated_lines.append("")
            continue

        translated_chunk = clean_chunk
        try:
            # 1. Primary: MyMemory from deep_translator
            translated_chunk = memory_tr.translate(clean_chunk)
        except Exception:
            try:
                # 2. Fallback: GoogleTranslator
                translated_chunk = GoogleTranslator(source='auto', target='ar').translate(clean_chunk)
            except Exception:
                translated_chunk = clean_chunk

        translated_lines.append(prefix + translated_chunk)

    return "\n\n".join(translated_lines)

def translate_to_arabic(text, api_key=None):
    """
    Unified translation endpoint utilizing the deep-translator package
    with optional Gemini API enhancement.
    """
    if not text or not str(text).strip():
        return "لا يوجد محتوى للترجمة.", "Package Translator"

    raw_text = str(text).strip()

    # 1. If Gemini API key is provided, use neural translation
    if api_key:
        try:
            import requests
            prompt = (
                "You are an expert medical translator. Translate the ENTIRE text below into formal Arabic. "
                "Ensure that 100% of the sentences are translated into Arabic, with NO remaining English sentences.\n\n"
                f"{raw_text}"
            )
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 2048}
            }
            res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=8)
            if res.status_code == 200:
                data = res.json()
                translated = data['candidates'][0]['content']['parts'][0]['text']
                return f"🌐 **الترجمة العربية المعتمدة:**\n\n{translated}", "Google Gemini Neural Translation"
        except Exception:
            pass

    # 2. Use deep-translator package (MyMemory + Google)
    try:
        translated_arabic = translate_with_package(raw_text)
        return f"🌐 **الترجمة العربية الشاملة (باكدج deep-translator):**\n\n{translated_arabic}", "deep-translator package"
    except Exception as err:
        return f"خطأ في الترجمة: {err}", "Error"
