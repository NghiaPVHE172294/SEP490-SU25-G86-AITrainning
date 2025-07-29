from fastapi import APIRouter, UploadFile, File
import tempfile
from cv_parser.parser import parse_cv

router = APIRouter()

@router.post("/parse-cv/")
async def parse_cv_endpoint(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        contents = await file.read()
        temp_file.write(contents)
        temp_file_path = temp_file.name

    result = parse_cv(temp_file_path)
    return result
