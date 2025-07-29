from cv_parser.extractor import (
    extract_text_from_pdf,
    extract_email,
    extract_phone,
    extract_skills,
    extract_certifications,
    extract_projects,
    extract_job_titles,
    extract_years_of_experience,
)
from cv_parser.ner_inference import run_ner
from models.cv_model import CVParsedData

# === Hậu xử lý: lọc các entity rác theo rule ===
def clean_entities(fields: dict) -> dict:
    def is_valid(text: str):
        return 3 <= len(text) <= 100 and not any(c in text for c in ["...", "\u0000", "\n", "Link Github"])

    # --- Làm sạch skills ---
    allowed_skills = [
        "HTML", "CSS", "Angular", "JavaScript", "C#", "Java", "SQL", "SQL Server", "Python", ".NET", "Django", "Asp.NetCore"
    ]
    fields["SKILL"] = list({
        skill for skill in fields["SKILL"]
        if is_valid(skill) and any(kw.lower() in skill.lower() for kw in allowed_skills)
    })

    # --- Làm sạch job titles ---
    job_keywords = ["intern", "developer", "engineer", "lead", "leader"]
    fields["JOBTITLE"] = list({
        job for job in fields["JOBTITLE"]
        if is_valid(job) and any(kw in job.lower() for kw in job_keywords)
    })

    # --- Làm sạch languages ---
    lang_keywords = ["tiếng", "english", "japanese", "vietnamese", "trung", "hàn"]
    fields["LANGUAGE"] = list({
        lang for lang in fields["LANGUAGE"]
        if is_valid(lang) and any(kw in lang.lower() for kw in lang_keywords)
    })

    return fields

# === Hàm chính ===
def parse_cv(file_path: str) -> dict:
    text = extract_text_from_pdf(file_path)
    if not text.strip():
        return {"error": "CV trống hoặc không thể đọc nội dung."}

    clean_text = text.replace("\u0000", "").replace("...", "").strip()
    ner_result = run_ner(clean_text)

    filtered_ner = [
        ent for ent in ner_result
        if 3 <= len(ent["text"]) <= 100
        and not any(c in ent["text"] for c in ["...", "\u0000", "Link Github", "\n"])
        and not ent["text"].strip().lower().startswith("dự án")
    ]

    fields = {
        "FULLNAME": None,
        "EMAIL": None,
        "PHONE": None,
        "SKILL": [],
        "EDUCATION": None,
        "JOBTITLE": [],
        "LANGUAGE": [],
        "CERTIFICATIONS": [],
        "ADDRESS": None,
        "SUMMARY": [],
        "PROJECT": [],
        "WORKHISTORY": []
    }

    for ent in filtered_ner:
        label = ent["label"]
        value = ent["text"].strip()

        if label in ["FULLNAME", "EMAIL", "PHONE", "EDUCATION", "ADDRESS"]:
            fields[label] = fields[label] or value
        elif label in ["SKILL", "LANGUAGE", "CERTIFICATIONS", "JOBTITLE", "PROJECT", "WORKHISTORY", "SUMMARY"]:
            fields[label].append(value)

    # Ưu tiên regex cho Email, Phone
    fields["EMAIL"] = extract_email(clean_text) or fields["EMAIL"]
    fields["PHONE"] = extract_phone(clean_text) or fields["PHONE"]

    # === Bước làm sạch hậu xử lý ===
    fields = clean_entities(fields)

    return CVParsedData(
        FullName=fields["FULLNAME"],
        Email=fields["EMAIL"],
        Phone=fields["PHONE"],
        YearsOfExperience=extract_years_of_experience(clean_text),
        Skills=list(set(fields["SKILL"] + extract_skills(clean_text))),
        EducationLevel=fields["EDUCATION"],
        JobTitles=fields["JOBTITLE"],
        Languages=fields["LANGUAGE"],
        Certifications=list(set(fields["CERTIFICATIONS"] + extract_certifications(clean_text))),
        WorkHistory=fields["WORKHISTORY"],
        Projects=list(set(fields["PROJECT"] + extract_projects(clean_text))),
        Summary=" ".join(fields["SUMMARY"])
    ).dict()
