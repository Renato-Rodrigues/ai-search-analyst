from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

config = {
    'test_mode': 'true',  # Set to True for test mode, False for production. This limits the serach api calls to avoid excessive charges on testing phase

    'default_ai_service': 'gpt',  # Default AI service: 'gpt', 'azure', 'gemini', 'aws', 'anthropic'
    'default_search_engine': 'google',  # Default search engine: 'google', 'bing'

    'default_number_of_results': '10', # Default number of results in search queries
    'default_search_period': 'y1', # Default serach period
    'default_disable_cache': 'false', # Default serach period

    'llm_batch_process': 'true', # enable llam batch process request
    'batch_sleep':'30', # sleep time in seconds to check for batch results

    # AI Service API keys loaded from environment variables
    'ai_services': {
        'gpt': {
            'api_key': os.getenv('GPT_API_KEY'),
            'model': 'gpt-4o-mini' # gpt-4o, gpt-4o-mini (required to structured output)
        },
        'azure': {
            'api_key': os.getenv('AZURE_API_KEY'),
            'api_url': os.getenv('AZURE_API_URL'),
            'model': ''
        },
        'gemini': {
            'api_key': os.getenv('GEMINI_API_KEY'),
            'api_url': os.getenv('GEMINI_API_URL'),
            'model': ''
        },
        'aws': {
            'api_key': os.getenv('AWS_API_KEY'),
            'api_url': os.getenv('AWS_API_URL'),
            'model': ''
        },
        'anthropic': {
            'api_key': os.getenv('ANTHROPIC_API_KEY'),
            'api_url': os.getenv('ANTHROPIC_API_URL'),
            'model': ''
        }
    },

    # Search Engines API keys loaded from environment variables
    'search_engines': {
        'google': {
            'api_key': os.getenv('GOOGLE_SEARCH_API_KEY'),
            'search_engine_id': os.getenv('GOOGLE_SEARCH_CX')  # Google Custom Search Engine ID
        },
        'bing': {
            'api_key': os.getenv('BING_SEARCH_API_KEY')
        }
    },

    # IO sheet
    'io': {
        'googleSheets': {
            'spreadsheet_id': os.getenv('GOOGLE_SHEETS_ID')  # Load Google Sheets ID from environment variable
        }
    },

    # test mode
    'test': {
        'inputs': 1,
        'search_results': 10
    }
}

def convert_to_bool(value):
    """Convert string 'true'/'false' to boolean True/False."""
    if isinstance(value, str):
        if value.lower() == 'true':
            return True
        elif value.lower() == 'false':
            return False
    return value

def recursive_convert_to_bool(d):
    """Recursively convert 'true'/'false' strings to booleans in a dictionary."""
    for key, value in d.items():
        if isinstance(value, dict):
            # Recursively apply conversion to nested dictionaries
            d[key] = recursive_convert_to_bool(value)
        else:
            d[key] = convert_to_bool(value)
    return d

# Apply the conversion to boolean values
config = recursive_convert_to_bool(config)
