# OpenAI GPT integration

import json
from openai import OpenAI
from config import config

def gpt_query(query, role, format, model="gpt-3.5-turbo", type="json"):
    """
    Sends a query to the OpenAI GPT model and returns the processed result.

    Parameters:
    query (str): The main text prompt to send to the GPT model.
    role (str): The system role instruction for the GPT model.
    format (str): The desired format instruction for the GPT model's response.
    model (str, optional): The GPT model to use. Defaults to "gpt-3.5-turbo".
    type (str, optional): The expected return type. Defaults to "json".

    Returns:
    dict or list: The processed result from the GPT model. If type is 'string', 
                  the result is wrapped in a list.

    Raises:
    Exception: If there's an error in making the API call or processing the response.
    """
    client = OpenAI(api_key=config['ai_services']['gpt']['api_key'])

    print("asking gpt")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": role + "\n" + format},
                {"role": "user", "content": query}
            ],
            response_format={ "type": "json_object" }
        )
        
        result = json.loads(response.choices[0].message.content.strip())
        
        # Format the result based on the type
        return [result] if type == 'string' else result
    except Exception as e:
        error_message = f"Error in GPT query: {str(e)}"
        print(error_message)
        return {'error': error_message}  # Return error in a format that won't be cached
