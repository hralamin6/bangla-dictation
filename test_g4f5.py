import g4f
from g4f.client import Client

client = Client()
try:
    from g4f.Provider import __providers__
    names = [p.__name__ for p in __providers__]
    print(names)
    print("Blackbox in names:", "Blackbox" in names)
except Exception as e:
    print(e)
