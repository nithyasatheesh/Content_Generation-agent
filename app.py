import os
from fastapi import FastAPI, UploadFile, File
from pptx import Presentation
from pptx.util import Inches
from docx import Document
import fitz  # PyMuPDF
import openai

app = FastAPI()

openai.api_key = "YOUR_API_KEY"

# -------------------------------
# 1. FILE TYPE DETECTION
# -------------------------------
def detect_file_type(filename):
    if filename.endswith(".pdf"):
        return "pdf"
    elif filename.endswith(".docx"):
        return "docx"
    elif filename.endswith(".txt"):
        return "txt"
    elif filename.endswith(".pptx"):
        return "pptx"
    else:
        return None

# -------------------------------
# 2. PARSERS
# -------------------------------
def parse_pdf(path):
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def parse_docx(path):
    doc = Document(path)
    return "\n".join([p.text for p in doc.paragraphs])

def parse_txt(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def parse_pptx(path):
    prs = Presentation(path)
    text = ""
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text += shape.text + "\n"
    return text

# -------------------------------
# 3. STRUCTURE CONTENT (LLM)
# -------------------------------
def structure_content(text):
    prompt = f"""
    Convert the following content into teaching slides.

    Rules:
    - Max 5 bullet points per slide
    - Each point under 12 words
    - Keep it simple and structured

    Content:
    {text[:4000]}
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

# -------------------------------
# 4. GENERATE QUIZ
# -------------------------------
def generate_quiz(text):
    prompt = f"""
    Create a quiz:
    - 5 MCQs
    - Include answers

    Content:
    {text[:2000]}
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

# -------------------------------
# 5. CREATE PPT
# -------------------------------
def create_ppt(structured_text, quiz_text):
    prs = Presentation()

    slides = structured_text.split("\n\n")

    for slide_text in slides:
        slide_layout = prs.slide_layouts[1]
        slide = prs.slides.add_slide(slide_layout)

        lines = slide_text.split("\n")
        if len(lines) > 0:
            slide.shapes.title.text = lines[0]
            slide.placeholders[1].text = "\n".join(lines[1:])

    # Add quiz slide
    slide_layout = prs.slide_layouts[1]
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = "Quiz"
    slide.placeholders[1].text = quiz_text

    output_path = "output.pptx"
    prs.save(output_path)

    return output_path

# -------------------------------
# 6. MAIN API
# -------------------------------
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_type = detect_file_type(file.filename)

    if not file_type:
        return {"error": "Unsupported file type"}

    temp_path = f"temp_{file.filename}"

    with open(temp_path, "wb") as f:
        f.write(await file.read())

    # Parse
    if file_type == "pdf":
        text = parse_pdf(temp_path)
    elif file_type == "docx":
        text = parse_docx(temp_path)
    elif file_type == "txt":
        text = parse_txt(temp_path)
    elif file_type == "pptx":
        text = parse_pptx(temp_path)

    # AI Processing
    structured = structure_content(text)
    quiz = generate_quiz(text)

    # Create PPT
    ppt_path = create_ppt(structured, quiz)

    return {"message": "PPT created", "file": ppt_path}
