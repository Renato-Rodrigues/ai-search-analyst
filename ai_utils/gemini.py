# Google Gemini integration

import requests
from config import config

def gemini_query(query):
    gemini_api_url = config['ai_services']['gemini']['api_url']
    gemini_api_key = config['ai_services']['gemini']['api_key']
    
    headers = {"Authorization": f"Bearer {gemini_api_key}"}
    payload = {"prompt": f"Summarize the following content:\n{query}", "max_tokens": 150}

    response = requests.post(gemini_api_url, headers=headers, json=payload)
    return response.json()['choices'][0]['text'].strip()
