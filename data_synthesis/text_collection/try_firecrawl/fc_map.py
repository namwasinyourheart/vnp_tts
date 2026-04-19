from firecrawl import Firecrawl
from rich import print

app = Firecrawl(api_key="fc-c8a4be9f60b64d7e91bf83b144ee5d6b")

map_result = app.map("https://vnexpress.net/")

print(map_result)