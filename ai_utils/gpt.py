# OpenAI GPT integration

import json
from openai import OpenAI
from config import config
import datetime
import time

def gpt_query(queries, role=None, format=None, chat_history=None, model="gpt-4o-mini"):
    """
    Process queries in batch if there is more than one query in queries,
    otherwise handle them individually.
    
    Args:
        queries (list): List of queries to be processed.
        role (str): Role to be passed to the GPT model.
        format (dict): Format for the response.
        chat_history (list): Chat history to be sent to the model.
        model (str): The model to be used.
        
    Returns:
        tuple: A tuple containing:
            - responses (list): Results from the AI model, reordered to match the original input order.
            - current_chat_instance (list): List of user queries and corresponding AI responses.
            - full_history (list): Full history of the conversation without specific roles.
    """
    client = OpenAI(api_key=config['ai_services']['gpt']['api_key'])
    
    # Initialize chat_history if it is None or empty
    if chat_history is None:
        chat_history = []
        # Ensure chat_history has enough entries
        while len(chat_history) < len(queries):
            chat_history.append([])  # Append an empty list for each query

    # Convert prepared_queries to a list if it's a single string
    if isinstance(queries, str):
        queries = [queries]
    
    # Determine whether to process in batch or individually based
    batch_process = config['llm_batch_process']

    if batch_process:
        # Collect all messages for the batch request
        messages_batch = []
        for index, query in enumerate(queries):
            query_role = "Default system role" if not role else role[index] if isinstance(role, list) else role 
            query_format = {"type": "text"} if not format else json.loads(format[index]) if isinstance(format, list) else json.loads(format)
            # Prepare the system and user messages for the batch with custom_id
            task = {
                "custom_id": f"query_{index}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    # This is what you would have in your Chat Completions API call
                    "model": model,
                    "messages": chat_history[index] + [  # Append the chat history for this specific query
                        {"role": "system", "content": query_role},
                        {"role": "user", "content": query}
                    ],
                    #"temperature": 0.1,
                    "response_format": query_format
                }
            }
            json.loads(format[index])
            messages_batch.append(task)
        
        now = datetime.datetime.now()
        time_stamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"data/batch_requests/batch_tasks_{time_stamp}.jsonl"

        with open(file_name, 'w') as file:
            for obj in messages_batch:
                file.write(json.dumps(obj) + '\n')

        try:
            #upload batch file 
            batch_file = client.files.create(
                file=open(file_name, "rb"),
                purpose="batch"
                )
            
            batch_job = client.batches.create(
                input_file_id=batch_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h"
                )
            
            while True:
                batch_job = client.batches.retrieve(batch_job.id)
                if batch_job.status == "failed":
                    print(f"[OpenAI API] Job {batch_job.id} has failed with error {batch_job.errors}")
                    return [{'error': batch_job.errors}], None, None
                elif batch_job.status == 'in_progress':
                    print(f'[OpenAI API] Job {batch_job.id} is in progress, {batch_job.request_counts.completed}/{batch_job.request_counts.total} requests completed')
                elif batch_job.status == 'finalizing':
                    print(f'[OpenAI API] Job {batch_job.id} is finalizing, waiting for the output file id')
                elif batch_job.status == "completed":
                    print(f"[OpenAI API] Job {batch_job.id} has finished")
                    break
                time.sleep(int(config['batch_sleep']))
            
            result_file_id = batch_job.output_file_id
            if result_file_id:
                result = client.files.content(result_file_id).content
                result_file_name = f"data/batch_requests/batch_tasks_{time_stamp}_results.jsonl"
                with open(result_file_name, 'wb') as file:
                    file.write(result)
            else:
                print(f"[OpenAI API] Job {batch_job.id} has failed.")
                print(f"[OpenAI API] There was probably an error in the queries submited file {file_name}")
                error_file_id = batch_job.error_file_id
                error = client.files.content(error_file_id).content
                error_file_name = f"data/batch_requests/batch_tasks_{time_stamp}_error.jsonl"
                with open(error_file_name, 'wb') as file:
                    file.write(error)
                print(f"[OpenAI API] You can find more details at the file {error_file_name}")
                return [{'error': batch_job.errors}], None, None

            results = []
            with open(result_file_name, 'r') as file:
                for line in file:
                    json_object = json.loads(line.strip())
                    results.append(json_object)
            
            # Collect and reorder all responses from the batch based on custom_id
            response_dict = {batch['custom_id']: batch['response']['body']['choices'][0]['message']['content'].strip() for batch in results}
            ordered_responses = [response_dict[f"query_{index}"] for index in range(len(queries))]
        
        except Exception as e:
            return [{'error': str(e)}], None, None
        
        # Create current chat instance for batch calls
        current_chat_instance = []
        for index, query in enumerate(queries):
            current_chat_instance.append([
                {"role": "user", "content": query},
                {"role": "system", "content": ordered_responses[index]}
            ])
        
        # Create full history
        full_history = []
        for history in chat_history:
            full_history.extend(history)

        # Append current_chat_instance to full_history
        for chat in current_chat_instance:
            full_history.extend(chat)

        return ordered_responses, current_chat_instance, full_history

    else:
        # Process each query individually
        responses = []
        current_chat_instance = []
        query = queries[0]
        query_role = role[0] if isinstance(role, list) else role 
        query_format = {"type": "text"} if not format else json.loads(format[0]) if isinstance(role, list) else json.loads(format)
        query_chat_history = chat_history[0] if isinstance(chat_history[0], list) else chat_history 
        try:
            messages = query_chat_history + [  # Include the chat history for this specific query
                {"role": "system", "content": query_role or "Default system role"},
                {"role": "user", "content": query}
            ]
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format= query_format
            )
            assistant_response = response.choices[0].message.content.strip()
            responses.append(assistant_response)

            # Create current chat instance for individual calls
            current_chat_instance.append([
                {"role": "user", "content": query},
                {"role": "system", "content": assistant_response}
            ])
            
        except Exception as e:
            responses.append({'error': str(e)})
            current_chat_instance.append(None)
        
        # Create full history
        full_history = []
        for history in chat_history:
            full_history.extend(history)

        # Append current_chat_instance to full_history
        for chat in current_chat_instance:
            if chat:  # Ensure we only add valid chat instances
                full_history.extend(chat)
                
        return responses, current_chat_instance, full_history



