import os
import requests
import traceback
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get('OPENROUTER_API_KEY')
print(f"KEY LOADED: {api_key is not None}")

try:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "nvidia/nemotron-3-super-120b-a12b:free",
        "messages": [
            { "role": "user", "content": "Test message" }
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        print("API RETURNED:", response.status_code, response.text)
    response.raise_for_status()
    
    response_data = response.json()
    reply = response_data['choices'][0]['message']['content']
    print("SUCCESS: AI RESPONDED")
    print(reply)
except Exception as e:
    print("AI FAILED:")
    traceback.print_exc()
