# Anthropic AI Claude integration

import requests
from config import config

def anthropic_query(query):
    anthropic_api_url = config['ai_services']['anthropic']['api_url']
    anthropic_api_key = config['ai_services']['anthropic']['api_key']
    
    headers = {"Authorization": f"Bearer {anthropic_api_key}"}
    payload = {"prompt": f"Summarize the following content:\n{query}", "max_tokens": 150}

    response = requests.post(anthropic_api_url, headers=headers, json=payload)
    return response.json()['choices'][0]['text'].strip()
