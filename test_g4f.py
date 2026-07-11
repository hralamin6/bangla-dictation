import g4f
from g4f.client import Client

client = Client()
try:
    provider_class = getattr(g4f.Provider, "Blackbox", None)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "hi"}],
        provider=provider_class
    )
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Error: {e}")
