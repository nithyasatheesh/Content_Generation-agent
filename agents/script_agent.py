from openai import OpenAI


class ScriptAgent:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def generate(self, topic: str, category: str):
        prompt = f"""
        Create an educational YouTube video script.

        Topic:
        {topic}

        Category:
        {category}

        Requirements:
        - Beginner friendly
        - Clear explanations
        - Short paragraphs
        - Include examples
        - Add intro and conclusion
        - Maximum 800 words
        """

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return response.choices[0].message.content