from config import config
from ai_utils.ai_services import ai_query
from search_utils.search_engine import perform_search
from io_utils.google_sheets_io import get_google_sheets_value, set_google_sheets_value, ensure_sheet_exists, replace_placeholders, find_row_with_content

def main():

    # load the default ai service, model and search engine from the config
    ai_service = config['default_ai_service'] # load the default ai service from the config
    model = config['ai_services'][ai_service]['model'] # load the model from the config
    search_engine = config['default_search_engine'] # load the default search engine from the config
   
    # read user defined inputs
    inputs = get_google_sheets_value('inputs', output_mode='list_dict_column') # get input lists  
    if config['test_mode']:
        inputs = [{k: v[:3] for k, v in d.items()} for d in inputs]
    llm_queries = get_google_sheets_value('llm_queries', output_mode='list_dict') # get large language model queries from spreadsheet
    search_queries = get_google_sheets_value('search_queries', output_mode='list_dict') # get search queries from spreadsheet

    # initialization
    placeholders_variables = {} # initialize placeholders variables to be replaced in the queries
    output_dict = {} # create dictionary to save all output results
    cleared_sheets = set() # Create a list of cleared sheets to track sheets that should be erased so new values are written
    placeholders_variables.update({f"all_{k}s": v for item in inputs for k, v in item.items()}) # Create placeholders for input items
    
    # Process input independent queries
    root_queries = [q for q in llm_queries if q.get('level') == '0']
    for query in root_queries:
        out = replace_placeholders(query, placeholders_variables) # Process the query, replacing placeholders in specific elements
        out['result'] = ai_query(out['query'], out['role'], out['format'], ai_service, model, disable_cache=out['disable_cache']) # Perform the AI query using the processed information
        out['output_sheet'] not in cleared_sheets and ensure_sheet_exists(out['output_sheet'], clear_if_exists=True) and cleared_sheets.add(out['output_sheet']) # ensure sheet exists and clear it only once per run
        out['output_row'] = 1  # Set the starting row to 1
        for key, value in out['result'].items(): # if more than two dimensionnal result
            out['output_row'] = 1 if (out_row := find_row_with_content(out['output_sheet'], out['output_column'])) == 0 else out_row + 2 # Determine the row to write to, based on the last row with content
            set_google_sheets_value(value, out['output_sheet'], out['output_column'], out['output_row'], out['output_type']) # Write the result to the sheet
            output_dict[out['title']] = out # Store the output in the output_dict
    
    # loop in first input values
    input_name, input_value = next(iter(inputs[0].items()))
    for value in input_value:
        output_dict[value] = {} # Initialize dictionary for the current input value
        placeholders_variables.update({input_name: value}) # Update placeholders with the current input 1 value
        # Process queries only dependent of first input (level 1)
        level_1_queries = [q for q in llm_queries if q.get('level') == '1']
        for query in level_1_queries:
            out = replace_placeholders(query, placeholders_variables) # Process the query, replacing placeholders in specific elements
            out['result'] = ai_query(out['query'], out['role'], out['format'], ai_service, model, disable_cache=out['disable_cache']) # Perform the AI query using the processed information
            out['output_sheet'] not in cleared_sheets and ensure_sheet_exists(out['output_sheet'], clear_if_exists=True) and cleared_sheets.add(out['output_sheet']) # ensure sheet exists and clear it only once per run
            out['output_row'] = 1 if (out_row := find_row_with_content(out['output_sheet'], out['output_column'])) == 0 else out_row + 2 # Determine the row to write to, based on the last row with content
            set_google_sheets_value(out['query'], out['output_sheet'], out['output_column'], out['output_row']) # Write the prompt to the Google Sheet
            set_google_sheets_value(out['result'], out['output_sheet'], out['output_column'], out['output_row']+1, out['output_type']) # Write the result to the sheet
            output_dict[value][out['title']] = out # Store the output in the output_dict
            if out['dynamic_var']:
                placeholders_variables.update({out['title']: ', '.join(next(iter(out['result'].values())))} if out['dynamic_var'] == 'first' else {k: ', '.join(v) for k, v in out['result'].items()}) # add placeholder variable based on query if the user choose to
        input_name2, input_value2 = next(iter(inputs[1].items()))
        for value2 in input_value2:
            output_dict[value][value2] = {} # Initialize dictionary for the current input value
            #output_dict[value][value2] = {'name':input_name2} # Initialize dictionary for the current input value
            placeholders_variables.update({input_name2: value2}) # Update placeholders with the current input 1 value
            # Process search queries dependent of first and second input (level 2)
            level_2_search_queries = [q for q in search_queries if q.get('level') == '2']
            for query in level_2_search_queries:
                out = replace_placeholders(query, placeholders_variables) # Process the query, replacing placeholders in specific elements
                out['num_results'] = min(10, int(out['num_results'])) if config['test_mode'] else int(out['num_results'])  # Number of results to retrieve, limiting to 10 if in test mode to avoid API quota limits
                out['result'] = perform_search(out['search_query'], out['exactTerms'], out['orTerms'], out['num_results'], out['dateRestrict'], search_engine, disable_cache=out['disable_cache']) # Perform the search
                out['output_sheet'] not in cleared_sheets and ensure_sheet_exists(out['output_sheet'], clear_if_exists=True) and cleared_sheets.add(out['output_sheet']) # ensure sheet exists and clear it only once per run
                out['output_row'] = 1 if (out_row := find_row_with_content(out['output_sheet'], out['output_column'])) == 0 else out_row + 2 # Determine the row to write to, based on the last row with content
                set_google_sheets_value(value2, out['output_sheet'], out['output_column'], out['output_row']) # Write the input 2 value to the sheet
                set_google_sheets_value(out['result'], out['output_sheet'], out['output_column'], out['output_row']+1, out['output_type']) # Write the search results to the sheet
                output_dict[value][value2][out['title']] = out # Store the output in the output_dict
                # Process queries dependent of level 2 search results links
                for i, search_result in enumerate(output_dict[value][value2][out['title']]['result'][:1 if config['test_mode'] else None]): # Iterate through search results, limiting to the first item if in test mode to avoid API usage during test phase
                    placeholders_variables.update({'link': search_result['link']}) # Update placeholders with the current link
                    if out['dynamic_var']:
                        placeholders_variables.update({out['title']: next(iter(out['result'][i].values()))} if out['dynamic_var'] == 'first' else {k: v for k, v in out['result'][i].items()}) # add placeholder variable based on query if the user choose to
                    link_row = out['output_row']+i+2
                    level_2_queries = [q for q in llm_queries if q.get('level') == '2']
                    for query in level_2_queries:
                        out = replace_placeholders(query, placeholders_variables) # Process the query, replacing placeholders in specific elements
                        out['result'] = ai_query(out['query'], out['role'], out['format'], ai_service, model, disable_cache=out['disable_cache']) # Perform the AI query using the processed information
                        out['output_row'] = link_row #find_row_with_content(out['output_sheet'], 'C', search_result['link'])
                        set_google_sheets_value(out['result'], out['output_sheet'], out['output_column'], out['output_row'] - (1 if i == 0 else 0), out['output_type'], write_headers=(i == 0))

if __name__ == "__main__":
    main()


# Clear invalid cache entries
# from cache_utils import clear_invalid_cache
# #clear_invalid_cache()

import importlib

def reload_module(module_name):
    """
    Reload a module and return its updated functions.
    
    :param module_name: The name of the module to reload (e.g., 'io_utils.google_sheets_io')
    :return: A dictionary of the module's updated functions
    """
    # Import the module
    module = importlib.import_module(module_name)
    
    # Reload the module
    importlib.reload(module)
    
    # Get all functions from the module
    functions = {name: func for name, func in module.__dict__.items() if callable(func) and not name.startswith('_')}
    
    return functions

# Usage:
#updated_functions = reload_module('io_utils.google_sheets_io')
