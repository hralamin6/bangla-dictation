from g4f.client import Client
client = Client()
try:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "hi"}],
        provider="BraveSearch"
    )
    print("Success")
except Exception as e:
    print(e)
