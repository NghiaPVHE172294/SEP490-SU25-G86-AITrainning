import spacy

nlp = spacy.load("ner_training/model-last")  # hoặc model-best nếu có

def run_ner(text: str):
    doc = nlp(text)
    return [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
