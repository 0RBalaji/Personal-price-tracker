import requests

payload = { 'api_key': 'e639d1fa0eef650e618d3fd4c29b2a8e', 'url': 'https://www.amazon.in/', 'render': 'true' }
r = requests.get('https://api.scraperapi.com/', params=payload)
print(r.text)
