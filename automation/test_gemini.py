"""Test Gemini API"""
import requests
import json

api_key = 'AIzaSyAUk76mSH-ZAfDbLM1dIyiMZBbEuvzVpwo'
url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent'

prompt = """For HDFC Top 100 Fund (a large cap Indian mutual fund), list the top 5 stock holdings.
Return ONLY a JSON object like: {"holdings": [{"company": "HDFC Bank", "percentage": 9.5}]}
No markdown, no explanation, just pure JSON."""

response = requests.post(
    f'{url}?key={api_key}',
    json={
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {'temperature': 0.1, 'maxOutputTokens': 2000}
    },
    timeout=60
)

print(f'Status: {response.status_code}')
if response.status_code == 200:
    data = response.json()
    text = data['candidates'][0]['content']['parts'][0]['text']
    print(f'Raw response:')
    print(text)
    print()
    
    # Try to parse
    import re
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            print('Parsed successfully!')
            print(json.dumps(parsed, indent=2))
        except Exception as e:
            print(f'Parse error: {e}')
else:
    print(response.text)
