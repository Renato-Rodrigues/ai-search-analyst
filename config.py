from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

config = {
    'test_mode': 'true',  # Set to True for test mode, False for production. THis limits the serach api calls to avoid excessive charges on testing phase

    'default_ai_service': 'gpt',  # Default AI service: 'gpt', 'azure', 'gemini', 'aws', 'anthropic'
    'default_search_engine': 'google',  # Default search engine: 'google', 'bing'

    # AI Service API keys loaded from environment variables
    'ai_services': {
        'gpt': {
            'api_key': os.getenv('GPT_API_KEY'),
            'model': 'gpt-3.5-turbo' # gpt-3.5-turbo, gpt-4o, gpt-4o-mini
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
    }
}
