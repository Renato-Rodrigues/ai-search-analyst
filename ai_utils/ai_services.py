from utils.cache_utils import cache_result
from ai_utils.gpt import gpt_query
from ai_utils.azure import azure_query
from ai_utils.gemini import gemini_query
from ai_utils.aws import aws_query
from ai_utils.anthropic import anthropic_query

@cache_result
def ai_query(query, role, format, ai_service, model):
    """Summarize content based on the selected AI service."""
    if ai_service == 'azure':
        return azure_query(query)
    elif ai_service == 'gemini':
        return gemini_query(query)
    elif ai_service == 'aws':
        return aws_query(query)
    elif ai_service == 'anthropic':
        return anthropic_query(query)
    else:
        return gpt_query(query, role, format, model)
