# Azure OpenAI integration

import requests
from config import config

def azure_query(query):
    azure_api_url = config['ai_services']['azure']['api_url']
    azure_api_key = config['ai_services']['azure']['api_key']

    headers = {"Ocp-Apim-Subscription-Key": azure_api_key}
    payload = {"prompt": f"Summarize the following content:\n{query}", "max_tokens": 150}

    response = requests.post(azure_api_url, headers=headers, json=payload)
    return response.json()['choices'][0]['text'].strip()
