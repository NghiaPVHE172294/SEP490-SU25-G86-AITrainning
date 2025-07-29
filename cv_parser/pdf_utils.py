import pdfplumber
from langdetect import detect

def extract_text_from_pdf(file_path: str) -> str:
    """Trích xuất toàn bộ văn bản từ file PDF"""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

def detect_language(text: str) -> str:
    """Nhận diện ngôn ngữ của đoạn văn"""
    try:
        return detect(text)
    except Exception:
        return "unknown"
