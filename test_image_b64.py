import g4f
from g4f.client import Client

client = Client()
try:
    response = client.images.generate(
        model="flux",
        prompt="a cat",
        response_format="b64_json"
    )
    print("b64_json preview:", response.data[0].b64_json[:50] if response.data[0].b64_json else "None")
except Exception as e:
    print("Error:", e)
