__version__ = "1.0.2"

from config import config
from ai_utils.ai_services import ai_query
from search_utils.search_engine import perform_search
from io_utils.io_services import io_service
from utils.utils import utils
from utils.query_processor import QueryProcessor

def main():
    
    # Read user defined inputs
    inputs = io_service.get_value('inputs', output_mode='list_dict_column')
    inputs = [{k: [x for x in v if x] for k, v in entry.items()} for entry in inputs] # Remove empty string values in a single line
    if config['test_mode']:
        inputs = [{k: v[:config['test']['inputs']] for k, v in d.items()} for d in inputs]
    llm_queries = io_service.get_value('llm_queries', output_mode='list_dict')
    search_queries = io_service.get_value('search_queries', output_mode='list_dict')
    
    # initialize processor class
    processor = QueryProcessor(inputs, llm_queries, search_queries, config)
    query_results = processor.process_queries()

    # Save all query results to the same Excel file
    io_service.save_to_excel('data/query_results.xlsx', query_results)

if __name__ == "__main__":
    main()


#reload class
#import importlib
#import utils.query_processor

# Reload the module to reflect changes
#importlib.reload(utils.query_processor)

# Re-import the class after reloading
#from utils.query_processor import QueryProcessor

# Create a new instance of MyClass
#processor = QueryProcessor(inputs, llm_queries, search_queries, config)
#self = processor
