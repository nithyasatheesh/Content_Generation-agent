from openai import OpenAI


class VoiceAgent:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def generate(self, script: str, output_file: str):
        response = self.client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=script,
        )

        response.stream_to_file(output_file)

        return output_file