import inspect
from g4f.client import Client
print(inspect.signature(Client().chat.completions.create))
