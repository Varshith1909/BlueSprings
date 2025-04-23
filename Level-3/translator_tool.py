from googletrans import Translator

class TranslationError(Exception):
    pass

def translate_to_german(text: str) -> str:
    try:
        translator = Translator()
        result = translator.translate(text, src='en', dest='de')
        return result.text
    except Exception as e:
        raise TranslationError(f"Translation error: {str(e)}")

def is_translation_request(question: str) -> bool:
    q = question.lower()
    translation_keywords = ['translate', 'translation', 'how do you say', 'how to say', 'in german']
    return any(keyword in q for keyword in translation_keywords)

def extract_text_to_translate(question: str) -> str:
    import re
    q = question.lower()

    quote_match = re.search(r'[\'"](.+?)[\'"]', question)
    if quote_match:
        return quote_match.group(1)

    patterns = [
        r'translate\s+(.+?)\s+(?:to|into)\s+german',
        r'translate\s+(.+?)\s+in\s+german',
        r'how\s+(?:do\s+you\s+say|to\s+say)\s+(.+?)\s+in\s+german'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            return match.group(1)

    if "translate" in q:
        parts = q.split("translate", 1)[1]
        parts = re.sub(r'\s+(?:to|into|in)\s+german', '', parts, flags=re.IGNORECASE)
        return parts.strip()
    
    return ""