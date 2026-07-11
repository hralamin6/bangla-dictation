from g4f.client import Client
client = Client()
try:
    response = client.chat.completions.create(
        model="claude-3-opus",
        messages=[{"role": "user", "content": "hi"}],
    )
    print("Content:", response.choices[0].message.content)
except Exception as e:
    print("Error:", e)
