import g4f

try:
    # Safely try to import the provider module dynamically
    provider_module = __import__(f"g4f.Provider.{'Blackbox'}", fromlist=['Blackbox'])
    provider_class = getattr(provider_module, 'Blackbox')
    print("Found class:", provider_class)
except Exception as e:
    print("Error:", e)
