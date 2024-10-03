# OpenAI GPT integration

import json
from openai import OpenAI
from config import config

def gpt_query(query, role=None, format=None, chat_history=None, model="gpt-4o-mini"):
    client = OpenAI(api_key=config['ai_services']['gpt']['api_key'])
    
    try:
        # Initialize messages with chat history if provided
        messages = chat_history if chat_history else []

        # Add the current system and user messages
        messages.append(
            {"role": "system", "content": role} if role else {"role": "system", "content": "Default system role"}
        )
        messages.append({"role": "user", "content": query})

        # Use a default format if none is provided
        if format:
            response_format = json.loads(format)
        else:
            response_format = {"type": "text"}  # Set a default response format

        # Send the request to the GPT model
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format=response_format
        )

        # Extract the assistant's response
        assistant_response = response.choices[0].message.content.strip()

        # Include the assistant's response in the messages for future use
        messages.append({"role": "assistant", "content": assistant_response})

        try:
            assistant_response = json.loads(assistant_response)
        except json.JSONDecodeError:  # Added exception handling
            pass  # Do nothing if an error occurs
        
        return assistant_response, messages
        
    except Exception as e:
        error_message = f"Error in GPT query: {str(e)}"
        print(error_message)
        return {'error': error_message}, []  # Return error in a format that won't be cached
