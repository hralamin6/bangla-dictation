from g4f.client import Client

def test_model(model_name):
    client = Client()
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "hi"}],
        )
        print(f"✅ {model_name}: Working! (Output: {response.choices[0].message.content[:20]}...)")
    except Exception as e:
        print(f"❌ {model_name}: Failed - {type(e).__name__}")

models = ["gpt-4o", "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "llama-3-70b", "llama-3-8b", "mixtral-8x7b"]

for m in models:
    test_model(m)
