import re
from .pdf_utils import extract_text_from_pdf, detect_language  # ✅ sửa dòng này
from models.cv_model import CVParsedData

def extract_email(text: str) -> str | None:
    match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    return match.group() if match else None

def extract_phone(text: str) -> str | None:
    match = re.search(r"(0|\+84)[0-9]{8,10}", text)
    return match.group() if match else None

def extract_skills(text: str) -> list[str]:
    keywords = ['HTML', 'CSS', 'Angular', 'JavaScript', 'C#', 'Java', 'SQL', 'SQL Server', 'Python', '.NET', 'Django']
    found = []
    for kw in keywords:
        pattern = rf'\b{re.escape(kw)}\b'
        if re.search(pattern, text, re.IGNORECASE):
            found.append(kw)
    return found

def extract_certifications(text: str) -> list[str]:
    certs = []
    text_lower = text.lower()
    if "coursera" in text_lower:
        certs.append("Coursera")
    if "agile" in text_lower:
        certs.append("Agile Software Development")
    if "aws certified" in text_lower:
        certs.append("AWS Certified")
    if "microsoft certified" in text_lower:
        certs.append("Microsoft Certified")
    return certs

def extract_projects(text: str) -> list[str]:
    lines = text.splitlines()
    projects = [line.strip() for line in lines if 'github' in line.lower() or 'dự án' in line.lower()]
    return list(set(projects))

def extract_job_titles(text: str) -> list[str]:
    titles = ['INTERN', 'BACKEND', 'FRONTEND', 'FULL-STACK', 'LEADER', 'ENGINEER', 'DEVELOPER']
    return [t for t in titles if re.search(rf"\b{re.escape(t)}\b", text, re.IGNORECASE)]

def extract_years_of_experience(text: str) -> int | None:
    patterns = [
        r"(\d{1,2})\s+năm\s+kinh nghiệm",              # 5 năm kinh nghiệm
        r"(\d{1,2})\+?\s+years?\s+experience",         # 3+ years experience
        r"kinh nghiệm.*?(\d{1,2})\s+năm",              # kinh nghiệm lập trình 4 năm
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None
