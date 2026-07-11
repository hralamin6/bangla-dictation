import g4f
try:
    model, provider = g4f.get_model_and_provider("gpt-4o", "Blackbox", False)
    print(provider)
except Exception as e:
    print(e)
