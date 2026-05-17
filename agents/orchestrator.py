import os

from agents.quiz_agent import QuizAgent
from agents.script_agent import ScriptAgent
from agents.slide_agent import SlideAgent
from agents.video_agent import VideoAgent
from agents.voice_agent import VoiceAgent


class ContentOrchestrator:
    def __init__(self, api_key: str):
        self.script_agent = ScriptAgent(api_key)
        self.quiz_agent = QuizAgent(api_key)
        self.slide_agent = SlideAgent()
        self.voice_agent = VoiceAgent(api_key)
        self.video_agent = VideoAgent()

    def run(self, topic: str, category: str):
        os.makedirs("outputs", exist_ok=True)

        script = self.script_agent.generate(topic, category)

        quiz = self.quiz_agent.generate(script)

        ppt_path = "outputs/generated_slides.pptx"

        self.slide_agent.generate(
            topic,
            script,
            ppt_path,
        )

        audio_path = "outputs/narration.mp3"

        self.voice_agent.generate(
            script,
            audio_path,
        )

        video_path = "outputs/final_video.mp4"

        self.video_agent.generate(
            topic,
            audio_path,
            video_path,
        )

        return {
            "script": script,
            "quiz": quiz,
            "ppt": ppt_path,
            "audio": audio_path,
            "video": video_path,
        }