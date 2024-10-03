
import json
import re
import pandas as pd
import itertools
from ai_utils.ai_services import ai_query
from search_utils.search_engine import perform_search
from utils.utils import utils

class QueryProcessor:
    def __init__(self, inputs, llm_queries, search_queries, config):
        self.inputs = inputs
        self.llm_queries = llm_queries
        self.search_queries = search_queries
        self.config = config
        
        # Initialize AI service and model
        self.ai_service = self.config['default_ai_service']
        self.model = self.config['ai_services'][self.ai_service]['model']
        self.search_engine = self.config['default_search_engine']

    @staticmethod
    def parse_dynamic_var(dynamic_var):
        """Parse dynamic variables from a string."""
        if isinstance(dynamic_var, str):
            return [var.strip() for var in dynamic_var.split(',') if var.strip()]
        return []

    def analyze_dependencies(self):
        """Analyze dependencies among queries and sort them."""
        all_queries = self.llm_queries + self.search_queries
        
        dependency_graph = {}
        available_variables = set()

        # Add input-based variables
        for input_dict in self.inputs:
            for header in input_dict.keys():
                available_variables.add(header.strip())
                available_variables.add(f"{header.strip()}_set")

        for i, query in enumerate(all_queries):
            query_str = json.dumps(query)
            dependencies = set(dep.strip() for dep in re.findall(r'\[\[(.*?)\]\]', query_str))
            dependency_graph[i] = dependencies
            if 'dependency' in query and query['dependency']:
                dependencies.add(query['dependency'].strip())

        sorted_indices = []
        remaining_indices = set(range(len(all_queries)))

        while remaining_indices:
            independent_indices = [
                i for i in remaining_indices 
                if not (dependency_graph[i] - available_variables)
            ]
            if not independent_indices:
                print("Circular dependency detected for the following queries:")
                for i in remaining_indices:
                    query = all_queries[i]
                    print(f" - Title: {query.get('title')}, unsolved dependencies: {(dependency_graph[i] - available_variables)}")
                raise ValueError("Circular dependency detected in queries")
            sorted_indices.extend(independent_indices)
            remaining_indices -= set(independent_indices)

            # Update available variables
            for i in independent_indices:
                query = all_queries[i]
                dynamic_vars = self.parse_dynamic_var(query['dynamic_var'])
                new_dynamic_vars = list(set(var if var.endswith('_set') else f"{var}_set" for var in dynamic_vars)) + dynamic_vars  # Concatenate original dynamic_vars
                available_variables.update(new_dynamic_vars)
                available_variables.add(query.get('title').strip())

        # Create a mapping from original index to sorted index
        index_mapping = {original: sorted for sorted, original in enumerate(sorted_indices)}

        # Update dependency_graph keys to reflect new order
        updated_dependency_graph = {index_mapping[i]: deps for i, deps in dependency_graph.items()}

        return [all_queries[i] for i in sorted_indices], updated_dependency_graph

    def process_single_query(self, query, replace_vars, chat=None):
        """Process a single query and return results."""
        listMode = 'array_str' if query in self.llm_queries else 'list_str' if query in self.search_queries else None
        out, replaced_items = utils.replace_placeholders(query, replace_vars, listMode)

        flatten_processed_query = utils.flatten_json({**replaced_items, **out})
        processed_query_df = pd.DataFrame(flatten_processed_query)
        
        if query in self.llm_queries:
            out['result'], out['chat_history'] = ai_query(query=out['query'], role=out.get('role', False), format=out.get('format', False), chat_history=chat, ai_service=self.ai_service, model=out.get('model', self.model), disable_cache=out.get('disable_cache', False))
        elif query in self.search_queries:
            out['num_results'] = max(10,min(self.config['test']['search_results'], int(out['num_results'])) if self.config['test_mode'] else int(out['num_results']))
            out['result'] = perform_search(out['search_query'], out['exactTerms'], out['orTerms'], out['num_results'], out['dateRestrict'], self.search_engine, disable_cache=out.get('disable_cache', False))
            out['chat_history'] = []
            for index in range(len(out['result'])):
                out['result'][index] = {**replaced_items, **out['result'][index]} 

        # Update placeholders_variables with query results based on dynamic_var
        if 'dynamic_var' in query:
            dynamic_vars = self.parse_dynamic_var(query['dynamic_var'])
            for var in dynamic_vars:
                items = []
                if isinstance(out['result'], list):
                    for item in out['result']:
                        if var in item:
                            items.append(item[var])
                if items:
                    replace_vars[f"{var}_set"] = items
        
        # Create a new DataFrame for this query results
        try:
            flatten_results = utils.flatten_json(out['result'])
            results_df = pd.DataFrame(flatten_results)
        except json.JSONDecodeError:  # Added exception handling
            results_df = out['result']
            pass 

        return results_df, processed_query_df, replace_vars, out['chat_history']

    def process_queries(self):
        """
        Analyze dependencies, determine which queries to process, and execute them.

        :param config: Configuration dictionary.
        :return: Processed queries and query results.
        """
        # Analyze dependencies and sort queries
        sorted_queries, dependency_graph = self.analyze_dependencies()

        # Determine which queries to process based on test_mode
        queries_to_process = sorted_queries if self.config['test_mode'] else sorted_queries
        #queries_to_process = sorted_queries[:3] if self.config['test_mode'] else sorted_queries
        
        # Initialize a dictionary to store DataFrames for each query
        query_results = {}
        chat_history = {}
        query_results['queries'] = []

        # Initialize placeholders_variables with values directly obtained from inputs data
        input_placeholder = {f"{k}_set": v for item in self.inputs for k, v in item.items()}
        placeholders_variables = input_placeholder.copy()  # Initialize placeholders_variables

        for query_index, query in enumerate(queries_to_process):
            dependencies = dependency_graph.get(query_index, set())
            tmp_placeholders_variables = {}
            query_results[query['title']] = []
            placeholders = {**tmp_placeholders_variables, **placeholders_variables}
            #chat_history[query['title']] = {}
            curr_chat_history = []
            for dep in dependencies:
                if isinstance(dep, str) and ',' in dep:  # Check for comma-separated values
                    dep_titles = [title.strip() for title in dep.split(',')]
                    for title in dep_titles:
                        if title in chat_history:
                            curr_chat_history.extend(chat_history[title])  # Append results for each title
                elif dep in query_results:
                    curr_chat_history.extend(chat_history[dep])  # Append results for the single dependency
            if all(dep in {**placeholders, **query_results} for dep in dependencies):  # Check if all dependencies are available
                print(f"Processing query: {query['title']}")
                df, processed_query, query_placeholders_variables, query_chat_history = self.process_single_query(query, replace_vars=placeholders, chat=curr_chat_history)
                query_results['queries'].append(processed_query)
                query_results[query['title']].append(df)
                chat_history[query['title']] = query_chat_history
                placeholders_variables = {**placeholders_variables, **query_placeholders_variables}
            else:
                found = False
                filtered_dependencies = [dep for dep in dependencies if not dep.endswith('_set')]
                keys_to_combine = [f"{key}_set" for key in filtered_dependencies]
                values = [placeholders_variables.get(key, []) for key in keys_to_combine]

                for combination in itertools.product(*values):
                    tmp_placeholders_variables = {key: value for key, value in zip(filtered_dependencies, combination)}
                    placeholders = {**placeholders_variables, **tmp_placeholders_variables}

                    if all(dep in {**placeholders, **query_results} for dep in dependencies):
                        found = True
                        print(f"Processing query: {query['title']}, for {combination}")
                        df, processed_query, query_placeholders_variables, query_chat_history = self.process_single_query(query, replace_vars=placeholders, chat=curr_chat_history)
                        query_results['queries'].append(processed_query)
                        query_results[query['title']].append(df)
                        chat_history[query['title']] = query_chat_history
                        placeholders_variables = {**placeholders_variables, **query_placeholders_variables}

                if not found:
                    print(f"Warning: Missing placeholders for query: {query['title']}")
                    print(f"Placeholders available: {placeholders.keys()} and {query_results.keys()}")

        return query_results

