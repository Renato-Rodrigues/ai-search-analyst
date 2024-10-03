__version__ = "1.0.1"

from config import config
from ai_utils.ai_services import ai_query
from search_utils.search_engine import perform_search
from io_utils.io_services import io_service
from utils.utils import utils
import re
import json
import pandas as pd
import itertools

def parse_dynamic_var(dynamic_var):
    if isinstance(dynamic_var, str):
        return [var.strip() for var in dynamic_var.split(',') if var.strip()]
    return []

def analyze_dependencies(inputs, llm_queries, search_queries):
    all_queries = llm_queries + search_queries
    
    dependency_graph = {}
    available_variables = set()

    # Add input-based variables
    for input_dict in inputs:
        for header in input_dict.keys():
            available_variables.add(header.strip())
            available_variables.add(f"{header.strip()}_set")

    for i, query in enumerate(all_queries):
        query_str = json.dumps(query)
        dependencies = set(dep.strip() for dep in re.findall(r'\[\[(.*?)\]\]', query_str))
        dependency_graph[i] = dependencies

    sorted_indices = []
    remaining_indices = set(range(len(all_queries)))

    while remaining_indices:
        independent_indices = [
            i for i in remaining_indices 
            if not (dependency_graph[i] - available_variables)
        ]
        print(independent_indices)
        if not independent_indices:
            raise ValueError("Circular dependency detected in queries")

        sorted_indices.extend(independent_indices)
        remaining_indices -= set(independent_indices)

        # Update available variables
        for i in independent_indices:
            query = all_queries[i]
            #if 'dynamic_var' in query:
            dynamic_vars = parse_dynamic_var(query['dynamic_var'])
            new_dynamic_vars = list(set(var if var.endswith('_set') else f"{var}_set" for var in dynamic_vars)) + dynamic_vars  # Concatenate original dynamic_vars
            available_variables.update(new_dynamic_vars)
            #available_variables.update(f"{dynamic_vars}_set")
            #if query in search_queries:
            #    dynamic_vars = parse_dynamic_var(query.get('dynamic_var', ''))
            #    available_variables.update(f"{var.strip()}_link" for var in dynamic_vars)

    # Create a mapping from original index to sorted index
    index_mapping = {original: sorted for sorted, original in enumerate(sorted_indices)}

    # Update dependency_graph keys to reflect new order
    updated_dependency_graph = {index_mapping[i]: deps for i, deps in dependency_graph.items()}

    return [all_queries[i] for i in sorted_indices], updated_dependency_graph


def flatten_json(data):
    result = []

    # Recursive function to flatten the structure
    def recursive_flatten(current_data, current_dict):
        if isinstance(current_data, dict):
            # Iterate through key-value pairs in the dictionary
            for key, value in current_data.items():
                if isinstance(value, list):
                    # If the value is a list, recurse for each element in the list
                    for item in value:
                        recursive_flatten(item, current_dict.copy())  # Pass a copy of the current dict
                else:
                    # If it's not a list, add it to the current dictionary
                    current_dict[key] = value
            # Append the current dictionary if it's fully flattened
            if all(not isinstance(v, (list, dict)) for v in current_dict.values()):
                result.append(current_dict)
        elif isinstance(current_data, list):
            # If it's a list, iterate over its elements and recurse
            for item in current_data:
                recursive_flatten(item, current_dict.copy())

    # Start the flattening process with the top-level data
    recursive_flatten(data, {})

    return result

def process_single_query(query, replace_vars, ai_service, model, search_engine, config, llm_queries, search_queries):

    listMode = 'array_str' if query in llm_queries else 'list_str' if query in search_queries else None
    out, replaced_items = utils.replace_placeholders(query, replace_vars, listMode)

    flatten_processed_query = flatten_json(out)
    processed_query_df = pd.DataFrame(flatten_processed_query)

    if query in llm_queries:
        out['result'] = ai_query(out['query'], out['role'], out['format'], ai_service, model, disable_cache=out['disable_cache'])
    elif query in search_queries:
        out['num_results'] = min(config['test']['search_results'], int(out['num_results'])) if config['test_mode'] else int(out['num_results'])
        out['result'] = perform_search(out['search_query'], out['exactTerms'], out['orTerms'], out['num_results'], out['dateRestrict'], search_engine, disable_cache=out['disable_cache'])
        for index in range(len(out['result'])):
            out['result'][index] = {**replaced_items, **out['result'][index]} 

    #io_service.set_value(out['result'], out['output_sheet'], out['output_column'], value_type=out['output_type'])
    # Update placeholders_variables with query results based on dynamic_var
    if 'dynamic_var' in query:
        dynamic_vars = parse_dynamic_var(query['dynamic_var'])
        for var in dynamic_vars:
            items = []
            if isinstance(out['result'], list):
                for item in out['result']:
                    if var in item:
                        items.append(item[var])
            if items:
                replace_vars[f"{var}_set"] = items
    
    # Create a new DataFrame for this query results
    flatten_results = flatten_json(out['result'])
    results_df = pd.DataFrame(flatten_results)

    return results_df, processed_query_df, replace_vars

def main():
    ai_service = config['default_ai_service']
    model = config['ai_services'][ai_service]['model']
    search_engine = config['default_search_engine']
   
    # Read user defined inputs
    inputs = io_service.get_value('inputs', output_mode='list_dict_column')
    if config['test_mode']:
        inputs = [{k: v[:config['test']['inputs']] for k, v in d.items()} for d in inputs]
    
    llm_queries = io_service.get_value('llm_queries', output_mode='list_dict')
    search_queries = io_service.get_value('search_queries', output_mode='list_dict')

    # Initialize placeholders variables
    input_placeholder = {f"{k}_set": v for item in inputs for k, v in item.items()}
    
    # Analyze dependencies and sort queries
    sorted_queries, dependency_graph = analyze_dependencies(inputs, llm_queries, search_queries)

    # Determine which queries to process based on test_mode
    queries_to_process = sorted_queries[:2] if config['test_mode'] else sorted_queries
    #queries_to_process = sorted_queries

    # Initialize a dictionary to store DataFrames for each query
    query_results = {}
    processed_queries = pd.DataFrame()

    # Process queries based on their dependencies
    dependency_sets = input_placeholder.copy() # initialize dependency_sets with values directly obtained from inputs data
    placeholders_variables = input_placeholder.copy() # initialize placeholders_variables with values directly obtained from inputs data
    for query_index, query in enumerate(queries_to_process):
        #print(f"Running query index:{query_index}")
        dependencies = dependency_graph.get(query_index, set())
        tmp_placeholders_variables = {}
        # Check if all dependencies are satisfied
        if all(dep in placeholders_variables for dep in dependencies):
            print(f"Processing query: {query['title']}")
            df, processed_query, query_placeholders_variables = process_single_query(query, placeholders_variables, ai_service, model, search_engine, config, llm_queries, search_queries)
            processed_queries = pd.concat([processed_queries, processed_query], ignore_index=True)
            if query_index in query_results:
                query_results[query_index] = pd.concat([query_results[query_index], df], ignore_index=True)
            else:
                query_results[query_index] = df
            #dependency_sets.update(query_dependency_sets)
            placeholders_variables.update(query_placeholders_variables)
            # Create dependency_sets object with dynamic_vars as keys and corresponding placeholder values
            #query_dependency_sets = {
            #    f"{var}_set": placeholders_variables[var] for var in dynamic_vars if var in placeholders_variables
            #}
            #query_dependency_sets.update(replaced_items) # Merge replaced_items into dependency_sets
        else:
            found = False
            keys_to_combine = [f"{key}_set" for key in dependencies]
            values = [placeholders_variables.get(key, []) for key in keys_to_combine]
            for combination in itertools.product(*values):
                tmp_placeholders_variables = {f"{k}": v for v in combination for k in dependencies}
                if all(dep in {**tmp_placeholders_variables, **placeholders_variables} for dep in dependencies):
                    print(f"Processing query: {query['title']}, for {combination}")
                    df, processed_query, query_placeholders_variables = process_single_query(query, {**tmp_placeholders_variables, **placeholders_variables} , ai_service, model, search_engine, config, llm_queries, search_queries)
                    processed_queries = pd.concat([processed_queries, processed_query], ignore_index=True)
                    if query_index in query_results:
                        query_results[query_index] = pd.concat([query_results[query_index], df], ignore_index=True)
                    else:
                        query_results[query_index] = df
                    print(processed_queries)

                    #dependency_sets.update(query_dependency_sets)
                    placeholders_variables.update(query_placeholders_variables)
                    found = True
            if not found:
                print(f"Warning: Missing placeholders for query: {query['title']}")


    # Save all query results to the same Excel file
    excel_filename = 'query_results.xlsx'
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        processed_queries.to_excel(writer, sheet_name='queries', index=False)
        print(f"Results for processed queries saved to sheet in {excel_filename}")
        for query_index, df in query_results.items():
            query = sorted_queries[query_index]
            sheet_name = query.get('title', f'Query_{query_index}')
            # Ensure sheet name is valid (max 31 characters, no special characters)
            sheet_name = ''.join(c for c in sheet_name if c.isalnum() or c in (' ', '_'))[:31]
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"Results for query '{sheet_name}' saved to sheet in {excel_filename}")

    print(f"All query results saved to {excel_filename}")

    #todo 
    # fix: add sector, topic or other placeholder_variable replaced to the search result object
    # make sure the serach queries work
    # clean the code, move function to utils, make utils to be a package, move functions to the ai services, remove formatting from gpt function calls
    
    # features
    # adjust the risc_matrix to output country results
    # convert the results into Raquels output format
    # load raquels data as a embeeded data for including in the research queries, specially the risc_matrix
    # implement chat history
    # check better ways to make the questions to chatgpt, maybe use step by step instructions
    # do the serach per country
    # do questions to make the llm select the most relevant links
    # add last year links as inputs for the model to do a better assessment
    # add RAG for all embeeded information?


    # Process input-independent queries first
    #for query_index, query in enumerate(queries_to_process):
    #    if not any(f"[[{input_name}]]" in json.dumps(query) for input_dict in inputs for input_name in input_dict):
    #        print(f"Processing query: {query['title']}")
    #        dependencies = dependency_graph.get(query_index, set())
    #        df, placeholders_variables, query_dependency_sets = process_single_query(query, placeholders_variables, ai_service, model, search_engine, config, llm_queries, search_queries)
    #        #df, placeholders_variables = process_single_query(query, placeholders_variables, ai_service, model, search_engine, config, llm_queries, search_queries)
    #        query_results[query_index] = df

    # Process input-dependent queries
    #for input_dict in inputs:
    #    input_name, input_value = next(iter(input_dict.items()))
    #    for value in input_value:
    #        placeholders_variables[input_name] = value
    #        for query_index, query in enumerate(queries_to_process):
    #            if f"[[{input_name}]]" in json.dumps(query):
    #                print(f"Processing query: {query['title']} for {input_name}: {value}")
    #                dependencies = dependency_graph.get(query_index, set())
    #                df, placeholders_variables = process_single_query(query, placeholders_variables, ai_service, model, search_engine, config, llm_queries, search_queries, query_index, dependencies)
    #                if query_index in query_results:
    #                    query_results[query_index] = pd.concat([query_results[query_index], df], ignore_index=True)
    #                else:
    #                    query_results[query_index] = df

if __name__ == "__main__":
    main()

