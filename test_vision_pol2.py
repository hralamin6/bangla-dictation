import g4f
from g4f.client import Client
import base64

tiny_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff\xff\x00\x05\xfe\x02\xfe\xa7\x35\x81\x84\x00\x00\x00\x00IEND\xaeB`\x82'

client = Client()
try:
    response = client.chat.completions.create(
        model="openai",
        messages=[{"role": "user", "content": "What is the color of this 1x1 image? Answer in one word."}],
        image=tiny_png, 
        provider=g4f.Provider.PollinationsAI
    )
    print("Output:", response.choices[0].message.content if hasattr(response, 'choices') else str(response))
except Exception as e:
    print("Error:", e)
