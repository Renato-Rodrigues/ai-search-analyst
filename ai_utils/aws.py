# AWS AI integration

import requests
from config import config

def aws_query(query):
    aws_api_url = config['ai_services']['aws']['api_url']
    aws_api_key = config['ai_services']['aws']['api_key']
    
    headers = {"Authorization": f"Bearer {aws_api_key}"}
    payload = {"prompt": f"Summarize the following content:\n{query}", "max_tokens": 150}

    response = requests.post(aws_api_url, headers=headers, json=payload)
    return response.json()['choices'][0]['text'].strip()

