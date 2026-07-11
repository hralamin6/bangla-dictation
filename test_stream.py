import g4f
from g4f.client import Client

client = Client()
try:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "count 1 to 5"}],
        stream=True
    )
    for chunk in response:
        content = chunk.choices[0].delta.content or ""
        print(f"CHUNK: {content}")
except Exception as e:
    print("Error:", e)
