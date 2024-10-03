# OpenAI GPT integration

import json
from openai import OpenAI
from config import config

def gpt_query(query, role, format, model="gpt-4o-mini"):
    """
    Sends a query to the OpenAI GPT model and returns the processed result.

    Parameters:
    query (str): The main text prompt to send to the GPT model.
    role (str): The system role instruction for the GPT model.
    format (str): The desired format instruction or JSON schema for the GPT model's response.
    model (str, optional): The GPT model to use. Defaults to "gpt-4o-mini".
    
    Returns:
    dict or list: The processed result from the GPT model. If type is 'string', 
                  the result is wrapped in a list.

    Raises:
    Exception: If there's an error in making the API call or processing the response.
    """
    client = OpenAI(api_key=config['ai_services']['gpt']['api_key'])
    #print("asking gpt")
    #print("json")
    #print(format)
    
    try:
        messages = [
            {"role": "system", "content": role},
            {"role": "user", "content": query}
        ]

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format=json.loads(format)
        )
            #top_p=top_p,
            #frequency_penalty=frequency_penalty,
            #presence_penalty=presence_penalty,
            #temperature=temperature,
        
        contents = response.choices[0].message.content.strip()
        #print("Raw GPT response:")
        #print(result)  # Add this line to print the raw response
        
        result = json.loads(contents)

        # Format the result based on the type
        if isinstance(result, str):
            return [result]
        elif isinstance(result, dict) and 'result' in result:
            return result['result']
        else:
            return result
        
    except Exception as e:
        error_message = f"Error in GPT query: {str(e)}"
        print(error_message)
        return {'error': error_message}  # Return error in a format that won't be cached
