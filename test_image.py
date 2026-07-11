import g4f
from g4f.client import Client

client = Client()
try:
    response = client.images.generate(
        model="flux",
        prompt="a white siamese cat",
    )
    print("URL:", response.data[0].url)
except Exception as e:
    print("Error:", e)
