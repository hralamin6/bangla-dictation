import g4f
from g4f.client import Client

client = Client()
try:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "What is in this image?"}],
        image=open("test.jpg", "rb"),
        provider=g4f.Provider.Blackbox
    )
    print("Vision output:", response.choices[0].message.content if hasattr(response, 'choices') else str(response))
except Exception as e:
    print("Error:", e)
