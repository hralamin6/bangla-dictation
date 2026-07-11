import g4f
from g4f.client import Client

client = Client()
try:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What color is the sky in this image?"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wis-carlsbad-caverns.jpg/1024px-Gfp-wis-carlsbad-caverns.jpg"
                        }
                    }
                ]
            }
        ]
    )
    print("Response:", response.choices[0].message.content)
except Exception as e:
    print("Error:", e)
