import spacy
from spacy.tokens import DocBin
import json
import os
import sys
from tqdm import tqdm

# === Đường dẫn ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "..", "data", "train_data.jsonl")
OUTPUT_FILE_SPACY = os.path.join(BASE_DIR, "..", "ner_training", "train.spacy")
OUTPUT_FILE_JSONL = os.path.join(BASE_DIR, "..", "data", "train_data_fixed.jsonl")
SKIPPED_ENTITIES_FILE = os.path.join(BASE_DIR, "..", "data", "skipped_entities.jsonl")

# === Tạo tokenizer ===
try:
    nlp = spacy.blank("vi")
except:
    print("[!] Không có mô hình 'vi' — fallback dùng 'xx'")
    nlp = spacy.blank("xx")

# === Kiểm tra dữ liệu ===
if not os.path.exists(DATA_FILE):
    print(f"[X] Không tìm thấy file: {DATA_FILE}")
    sys.exit(1)

# === Chuẩn bị ===
doc_bin = DocBin()
fixed_data_lines = []
skipped_entities_all = []

# === Ưu tiên giữ các nhãn chính (chỉ gán 1 entity/đoạn) ===
PRIORITY_LABELS = {
    "FULLNAME": 1,
    "EMAIL": 1,
    "PHONE": 1,
    "ADDRESS": 1,
    "SKILL": 1,
    "JOBTITLE": 1,
    "COMPANY": 1,
    "EDUCATION": 1,
    "CERTIFICATIONS": 1,
    # Các nhãn phụ sẽ không gán vào SpaCy mà xử lý hậu kỳ
    "SUMMARY": 0,
    "WORKHISTORY": 0,
    "PROJECT": 0,
    "LANGUAGE": 1,
}

print(f"[✓] Đang xử lý: {DATA_FILE}")
with open(DATA_FILE, "r", encoding="utf-8") as f:
    for line_number, line in enumerate(tqdm(f, desc="Đang xử lý dữ liệu"), 1):
        data = json.loads(line)
        text = data["text"]
        doc = nlp.make_doc(text)
        ents = []
        span_set = set()
        fixed_entities = []
        skipped_entities = []

        for start, end, label in data.get("entities", []):
            span = doc.char_span(start, end, label=label, alignment_mode="expand")
            if span is None:
                # Thử điều chỉnh vị trí
                new_start, new_end = start, end
                for token in doc:
                    if token.idx <= start < token.idx + len(token):
                        new_start = token.idx
                    if token.idx < end <= token.idx + len(token):
                        new_end = token.idx + len(token)
                span = doc.char_span(new_start, new_end, label=label, alignment_mode="expand")

            if span:
                span_key = (span.start, span.end)
                if span_key not in span_set and PRIORITY_LABELS.get(label, 0) == 1:
                    ents.append(span)
                    span_set.add(span_key)
                    fixed_entities.append([span.start_char, span.end_char, span.label_])
                elif PRIORITY_LABELS.get(label, 0) == 0:
                    skipped_entities.append({"text": text[span.start_char:span.end_char], "start": start, "end": end, "label": label})
                else:
                    print(f"[!] Trùng span tại {span.start_char}-{span.end_char}, bỏ nhãn thứ hai ({label})")
                    skipped_entities.append({"text": text[span.start_char:span.end_char], "start": start, "end": end, "label": label})
            else:
                print(f"    → Không tạo được span cho ({start}, {end}, {label}) – giữ nguyên")
                fixed_entities.append([start, end, label])

        # Gán entity
        try:
            doc.ents = ents
            doc_bin.add(doc)
        except ValueError as ve:
            print(f"[!] Lỗi gán ents ở dòng {line_number}: {ve}")
            continue

        fixed_data_lines.append(json.dumps({
            "text": text,
            "entities": fixed_entities
        }, ensure_ascii=False))

        if skipped_entities:
            skipped_entities_all.append(json.dumps({
                "text": text,
                "skipped_entities": skipped_entities
            }, ensure_ascii=False))

# === Ghi file .spacy để train ===
os.makedirs(os.path.dirname(OUTPUT_FILE_SPACY), exist_ok=True)
doc_bin.to_disk(OUTPUT_FILE_SPACY)

# === Ghi file JSONL đã sửa ===
with open(OUTPUT_FILE_JSONL, "w", encoding="utf-8") as out_f:
    for line in fixed_data_lines:
        out_f.write(line + "\n")

# === Ghi file entity phụ để hậu xử lý nếu cần ===
with open(SKIPPED_ENTITIES_FILE, "w", encoding="utf-8") as out_f:
    for line in skipped_entities_all:
        out_f.write(line + "\n")

print(f"\n[✓] Đã hoàn tất xử lý dữ liệu:")
print(f"    → File SpaCy binary: {OUTPUT_FILE_SPACY}")
print(f"    → File JSONL đã fix: {OUTPUT_FILE_JSONL}")
print(f"    → File chứa entity phụ (nếu cần hậu xử lý): {SKIPPED_ENTITIES_FILE}")
