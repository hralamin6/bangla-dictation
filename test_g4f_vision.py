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
                    {"type": "text", "text": "What is in this image? Just a short sentence."},
                    {"type": "image_url", "image_url": {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wis-flying-pelican.jpg/320px-Gfp-wis-flying-pelican.jpg"}}
                ]
            }
        ]
    )
    print("Vision output:", response.choices[0].message.content)
except Exception as e:
    print("Error:", e)
