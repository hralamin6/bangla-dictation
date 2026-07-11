import g4f
from g4f.client import Client

provider_class = next((p for p in g4f.Provider.__providers__ if p.__name__ == "Blackbox"), None)
print(provider_class)
