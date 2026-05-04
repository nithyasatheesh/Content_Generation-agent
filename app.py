import os
from dataclasses import dataclass
from typing import Callable, Dict, Optional

import fitz  # PyMuPDF
import openai
from docx import Document
from fastapi import FastAPI, File, UploadFile
from pptx import Presentation

app = FastAPI()
openai.api_key = "YOUR_API_KEY"


@dataclass
class GeneratedArtifacts:
    structured_content: str
    quiz_content: str
    slide_path: str
    video_path: Optional[str] = None


class ParserAgent:
    def detect_file_type(self, filename: str) -> Optional[str]:
        extension = os.path.splitext(filename)[1].lower()
        return {
            ".pdf": "pdf",
            ".docx": "docx",
            ".txt": "txt",
            ".pptx": "pptx",
        }.get(extension)

    def parse(self, file_type: str, path: str) -> str:
        parsers: Dict[str, Callable[[str], str]] = {
            "pdf": self._parse_pdf,
            "docx": self._parse_docx,
            "txt": self._parse_txt,
            "pptx": self._parse_pptx,
        }
        parser = parsers.get(file_type)
        if not parser:
            raise ValueError(f"Unsupported file type: {file_type}")
        return parser(path)

    def _parse_pdf(self, path: str) -> str:
        doc = fitz.open(path)
        return "".join(page.get_text() for page in doc)

    def _parse_docx(self, path: str) -> str:
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)

    def _parse_txt(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as file:
            return file.read()

    def _parse_pptx(self, path: str) -> str:
        prs = Presentation(path)
        text_blocks = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text:
                    text_blocks.append(shape.text)
        return "\n".join(text_blocks)


class ContentStructuringAgent:
    def structure(self, text: str) -> str:
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
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content


class QuizGeneratorAgent:
    def generate(self, text: str) -> str:
        prompt = f"""
        Create a quiz:
        - 5 MCQs
        - Include answers

        Content:
        {text[:2000]}
        """

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content


class SlideGeneratorAgent:
    def generate(self, structured_text: str, quiz_text: str) -> str:
        prs = Presentation()
        slides = [block for block in structured_text.split("\n\n") if block.strip()]

        for slide_text in slides:
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            lines = [line for line in slide_text.split("\n") if line.strip()]

            if lines:
                slide.shapes.title.text = lines[0]
                slide.placeholders[1].text = "\n".join(lines[1:])

        quiz_slide = prs.slides.add_slide(prs.slide_layouts[1])
        quiz_slide.shapes.title.text = "Quiz"
        quiz_slide.placeholders[1].text = quiz_text

        output_path = "output.pptx"
        prs.save(output_path)
        return output_path


class VideoGeneratorAgent:
    def generate(self, structured_text: str) -> str:
        output_path = "output_video.txt"
        with open(output_path, "w", encoding="utf-8") as file:
            file.write("Video generation placeholder\n")
            file.write("Input summary:\n")
            file.write(structured_text[:500])
        return output_path


class ContentGenerationOrchestrator:
    def __init__(self) -> None:
        self.parser_agent = ParserAgent()
        self.structuring_agent = ContentStructuringAgent()
        self.slide_agent = SlideGeneratorAgent()
        self.quiz_agent = QuizGeneratorAgent()
        self.video_agent = VideoGeneratorAgent()

    def process(self, filename: str, temp_path: str) -> GeneratedArtifacts:
        file_type = self.parser_agent.detect_file_type(filename)
        if not file_type:
            raise ValueError("Unsupported file type")

        raw_text = self.parser_agent.parse(file_type, temp_path)
        structured_content = self.structuring_agent.structure(raw_text)
        quiz_content = self.quiz_agent.generate(raw_text)

        slide_path = self.slide_agent.generate(structured_content, quiz_content)
        video_path = self.video_agent.generate(structured_content)

        return GeneratedArtifacts(
            structured_content=structured_content,
            quiz_content=quiz_content,
            slide_path=slide_path,
            video_path=video_path,
        )


orchestrator = ContentGenerationOrchestrator()


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as temp_file:
        temp_file.write(await file.read())

    try:
        artifacts = orchestrator.process(file.filename, temp_path)
    except ValueError as error:
        return {"error": str(error)}

    return {
        "message": "Content package created",
        "slides_file": artifacts.slide_path,
        "video_file": artifacts.video_path,
    }
