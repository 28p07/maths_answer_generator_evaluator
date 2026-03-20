import os
import base64
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)


def generate_image_description(image_bytes: bytes) -> str:
    try:
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert CBSE examiner and diagram interpreter. "
                        "Analyze academic diagrams from questions or student answers.\n\n"

                        "Write a single clear paragraph of approximately 100 words describing:\n"
                        "- What the diagram represents\n"
                        "- Key components and labels\n"
                        "- Relationships or processes shown\n"
                        "- Any important values or annotations\n"
                        "- If the diagram appears incorrect or incomplete\n\n"

                        "Do NOT use bullet points, headings, or structured sections. "
                        "Output only one concise paragraph suitable for evaluation."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this diagram and describe it."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.2
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Image analysis failed: {str(e)}"