from cache.cache import cache_function
from ai_utils.gpt import gpt_query
from ai_utils.azure import azure_query
from ai_utils.gemini import gemini_query
from ai_utils.aws import aws_query
from ai_utils.anthropic import anthropic_query

@cache_function(batch_mode=True)  # Batch mode for ai_query
def ai_query(queries, role=None, format=None, chat_history=None, ai_service='openai', model='gpt-4o-mini', disable_cache=False):
    """Summarize content based on the selected AI service."""
    if ai_service == 'azure':
        return azure_query(queries)
    elif ai_service == 'gemini':
        return gemini_query(queries)
    elif ai_service == 'aws':
        return aws_query(queries)
    elif ai_service == 'anthropic':
        return anthropic_query(queries)
    else:
        return gpt_query(queries, role, format, chat_history, model)
