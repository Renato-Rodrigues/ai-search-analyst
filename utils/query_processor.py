
import json
import re
import itertools
import math
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
        self.num_results = self.config['default_number_of_results']
        self.dateRestrict = self.config['default_search_period']
        self.disable_cache = self.config['default_disable_cache']
        self.batch_process = self.config['llm_batch_process']

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
                for value in query['dependency'].split(','):
                    dependencies.add(value.strip())

        sorted_indices = []
        remaining_indices = set(range(len(all_queries)))

        while remaining_indices:
            independent_indices = [
                i for i in remaining_indices 
                if not (dependency_graph[i] - available_variables)
            ]
            if not independent_indices:
                print("[Query Processor] Circular dependency detected for the following queries:")
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
                new_dynamic_vars = list(set(var if var.endswith('_set')  else f"{var}_set" for var in dynamic_vars)) + list(set(f"{var}_group" for var in dynamic_vars if not var.endswith('_set'))) + dynamic_vars
                available_variables.update(new_dynamic_vars)
                available_variables.add(query.get('title').strip())

        # Create a mapping from original index to sorted index
        index_mapping = {original: sorted for sorted, original in enumerate(sorted_indices)}

        # Update dependency_graph keys to reflect new order
        updated_dependency_graph = {index_mapping[i]: deps for i, deps in dependency_graph.items()}

        return [all_queries[i] for i in sorted_indices], updated_dependency_graph

    def process_prepared_queries(self, prepared_queries, batch_process=False):
        """
        Process queries, optionally in a batch if batch_process is set to True.
        
        Args:
            prepared_queries (list): List of queries to be processed.
            batch_process (bool): Whether to process the queries in a batch or individually.
            
        Returns:
            tuple: A tuple containing:
            - results (list), List of results for the queries
            - queries_made (list): List of queries as they were made
            - query_solved_dependencies (dictionary): Dictionary containing dependencies solved by results from the query solved to dynamic_vars
            - chat_history (list of dictionaries): list of dicitionaries containing the user question and the llm reply, besides dimensions that can help filtering relevant chat history items 
        """
        results = []
        queries_made = []
        chat_history = []
        query_solved_dependencies = {}

        if isinstance(batch_process, str):
            batch_process = batch_process.lower() == 'true'

        # replace placeholders in queries
        for query_index, query in enumerate(prepared_queries):
            # solving search queries sequentially
            if query['raw_query'] in self.search_queries:
                print(f"[Query Processor] {query['message']}")
                batch_process = False
                upd_query, replaced_items = utils.replace_placeholders(query["raw_query"], variables=query["replace_vars"], listMode='list_str') # replacing variable placeholders
                prepared_queries[query_index]['replaced_items'] = {**replaced_items}
                prepared_queries[query_index]['query'] = {**upd_query}
                queries_made.append({**replaced_items, **upd_query})
                number_of_results = self.config['test']['search_results'] if self.config['test_mode'] else int(query['query'].get('num_results') or self.num_results)
                number_of_results = min(max(math.ceil(number_of_results / 10) * 10, 10), 100) # multiples of 10, in between 10 and 100
                res = perform_search(upd_query.get('search_query') or '', upd_query.get('exactTerms') or '', upd_query.get('orTerms') or '', number_of_results, query['query'].get('dateRestrict') or self.dateRestrict, query['query'].get('search_engine') or self.search_engine, disable_cache=query['query'].get('disable_cache') or self.disable_cache)
                prepared_queries[query_index]['result'] = [{ **replaced_items, **e } for e in res]
                results.extend(prepared_queries[query_index]['result'])
            # solving llm queries either in batch mode or in sequential mode
            elif query['raw_query'] in self.llm_queries:
                upd_query, replaced_items = utils.replace_placeholders(query["raw_query"], variables=query["replace_vars"], listMode='array_str') # replacing variable placeholders
                prepared_queries[query_index]['replaced_items'] = {**replaced_items}
                prepared_queries[query_index]['query'] = {**upd_query}
                queries_made.append({**replaced_items, **upd_query})
                if not batch_process or len(prepared_queries)==1:
                    # Process queries individually
                    print(f"[Query Processor] {query['message']}")
                    responses, current_chat_instance, full_history = ai_query(queries=upd_query.get('query'), role=upd_query.get('role') or None, format=upd_query.get('format') or None, chat_history=query.get('chat') or None, ai_service=query['query'].get('model') or self.ai_service, model=query['query'].get('model') or self.model, disable_cache=query['query'].get('disable_cache') or self.disable_cache)
                    error_messages = [d['error'] for d in responses if isinstance(d, dict) and 'error' in d] if isinstance(responses, list) else []
                    if error_messages:
                        print(error_messages)
                    try:
                        res = json.loads(responses[0] if isinstance(responses, list) else responses)
                    except json.JSONDecodeError:  # Added exception handling
                        pass  # Do nothing if an error occurs 
                    if 'result' in res: #results are included in a result dicitionary due to the json schema I use
                        prepared_queries[query_index]['result'] = res['result']
                    else:
                        prepared_queries[query_index]['result'] = res
                    results.extend(prepared_queries[query_index]['result'])
                    chat_history.append({ **prepared_queries[query_index]['replaced_items'], 'chat_history': current_chat_instance[0] })
        
        if batch_process and len(prepared_queries)>1: 
            print("[Query Processor] Starting batch call to llm")
            queries = [d["query"].get("query", []) for d in prepared_queries]
            roles = [d["query"].get("role", []) for d in prepared_queries]
            formats = [d["query"].get("format", []) for d in prepared_queries] 
            chart_histories = [d["query"].get("chart_history", []) for d in prepared_queries]
            responses, current_chat_instance, full_history = ai_query(queries=queries, role=roles, format=formats, chat_history=chart_histories, ai_service=prepared_queries[0]['query'].get('ai_service') or self.ai_service, model=prepared_queries[0]['query'].get('model') or self.model, disable_cache=prepared_queries[0]['query'].get('disable_cache') or self.disable_cache)
            for query_index, query in enumerate(prepared_queries):
                try:
                    res = json.loads(responses[query_index])
                except json.JSONDecodeError:  # Added exception handling
                    pass  # Do nothing if an error occurs 
                if 'result' in res: #results are included in a result dicitionary due to the json schema I use
                    prepared_queries[query_index]['result'] = res['result']
                else:
                    prepared_queries[query_index]['result'] = res
                results.extend(prepared_queries[query_index]['result'])
                chat_history.append({ **prepared_queries[query_index]['replaced_items'], 'chat_history': current_chat_instance[query_index] })
        
        # Create new sets information from query results based on dynamic_vars
        query_solved_dependencies = {}
        for query_index, query in enumerate(prepared_queries):
            if 'dynamic_var' in query['query']:
                dynamic_vars = self.parse_dynamic_var(query['query']['dynamic_var'])
                for var in dynamic_vars:
                    items = []
                    if isinstance(query['result'], list):
                        for item in query['result']:
                            if var in item:
                                items.append(item[var])
                    if f"{var}_group" not in query_solved_dependencies:
                        query_solved_dependencies[f"{var}_group"] = []
                    if f"{var}_set" not in query_solved_dependencies:
                        query_solved_dependencies[f"{var}_set"] = []
                    if items:
                        query_solved_dependencies[f"{var}_set"] = list(set(query_solved_dependencies[f"{var}_set"]).union(items))
                        query_solved_dependencies[f"{var}_group"].append({**query['replaced_items'], **{f"{var}_set":items}}) 
        
        return results, queries_made, query_solved_dependencies, chat_history
        
    def process_queries(self):
        """
        Analyze dependencies, determine which queries to process, and execute them.

        :param config: Configuration dictionary.
        :return: Processed queries and query results.
        """
        # Analyze dependencies and sort queries
        sorted_queries, dependency_graph = self.analyze_dependencies()

        # Determine which queries to process based on test_mode
        queries_to_process = sorted_queries[:self.config['test']['queries_limit']] if self.config['test_mode'] else sorted_queries
        
        # Initialize values directly obtained from inputs data
        input_dict = {f"{k}_set": v for item in self.inputs for k, v in item.items()} 
        input_dependencies = list(input_dict.keys()) 
        input_loop_dependencies = [item[:-4] for item in input_dependencies]

        # start solving dependencies and running the queries
        query_results = {}
        query_results['queries'] = []
        chat_history = {}
        solved_queries = set()
        available_dependencies_set = input_dict
        
        for query_index, query in enumerate(queries_to_process):
            current_query = query['title']
            print(f"[Query Processor] Solving Query number: {query_index+1} of {len(queries_to_process)}, named: {current_query}")
            # intiliaze query dependable variables 
            prepared_queries = []  
            query_results[current_query] = []
            chat_history[current_query] = []
            curr_chat_history = []
            dependencies = list(dependency_graph.get(query_index, set())) # current dependencies
            # load full history
            for dep in dependencies:
                if isinstance(dep, str) and ',' in dep:  
                    dep_titles = [title.strip() for title in dep.split(',')]
                    for title in dep_titles:
                        if title in chat_history:
                            curr_chat_history.extend(chat_history[title])  
                elif dep in query_results:
                    curr_chat_history.extend(chat_history[dep]) 
            # solved dependencies list and groups
            solved_dependencies_set = {**available_dependencies_set}
            solved_dependencies = list(solved_dependencies_set.keys()) + list(solved_queries)
            if all(dep in solved_dependencies for dep in dependencies): # check if we can solve the query with the available dependencies
                prepared_queries.append({"message": f"Solving query: {current_query}", 
                                         "raw_query":query, 
                                         "replace_vars":solved_dependencies_set, 
                                         "chat": self.filter_chat_history(curr_chat_history, histType = query.get('histType'))})
                solved_queries.add(current_query)
            else:
                # input dependencies
                input_dependencies = [item for item in input_loop_dependencies if item in dependencies]
                input_sets = {k[:-4]: v for k, v in input_dict.items() if k[:-4] in input_dependencies}
                # initialize input variable dependencies 
                tmp_input_set = {}
                for input_combination in itertools.product(*list(input_sets.values())):
                    tmp_input_set = {k: v for k, v in zip(list(input_sets.keys()), input_combination)} # loop dependable input dependencies 
                    group_dependencies = [ dep.replace("_group", "") for dep in list(available_dependencies_set.keys()) if dep.endswith('_group') ]
                    group_sets = {}
                    if group_dependencies: # add _group dependency
                        for group in group_dependencies:
                            #filter_group = [item[f"{group}_set"] for item in available_dependencies_set if item.get(f"{group}_group") == f"{group}_group" and all(item.get(key) == value for key, value in tmp_input_set.items())]
                            current_group_sets = {k:v for k,v in available_dependencies_set.items() if k == f"{group}_group"}[f"{group}_group"]
                            filter_group_sets = [ item for item in current_group_sets if all(item.get(key) == value for key, value in tmp_input_set.items()) ]
                            filter_group = [item[f"{group}_set"] for item in filter_group_sets]
                            flattened_group = [item for sublist in filter_group for item in sublist]
                            group_sets.update({f"{group}_group": flattened_group})
                    solved_dependencies_set = {**available_dependencies_set, **tmp_input_set, **group_sets}
                    solved_dependencies = list(solved_dependencies_set.keys()) + list(solved_queries)
                    if all(dep in solved_dependencies for dep in dependencies): # check if we can solve the query with the available dependencies
                        prepared_queries.append({"message": f"Solving query: {current_query} with {input_combination}", 
                                                 "raw_query":query, 
                                                 "replace_vars":solved_dependencies_set, 
                                                 "chat": self.filter_chat_history(curr_chat_history, filter_set={**tmp_input_set}, histType = query.get('histType'))})
                        solved_queries.add(current_query)
                    else:
                        # loop over dynamic variable dependencies (_group elements)
                        if group_dependencies:
                            remaining_dependencies = [dep for dep in dependencies if not dep in solved_dependencies]
                            active_groups = list(set([f"{g}_group" for g in remaining_dependencies if f"{g}_group" in list(available_dependencies_set.keys())] + [g for g in remaining_dependencies if g.endswith('_group')]))
                            group_set = {k: v for k, v in group_sets.items() if k in active_groups}
                            tmp_group_set = {}
                            for group_combination in itertools.product(*list(group_set.values())):
                                tmp_group_set = {k: v for k, v in zip([key.replace("_group", "") for key in group_set.keys()], group_combination)}
                                solved_dependencies_set = {**available_dependencies_set, **tmp_input_set, **group_sets, **tmp_group_set}
                                solved_dependencies = list(solved_dependencies_set.keys()) + list(solved_queries)
                                if all(dep in solved_dependencies for dep in dependencies):
                                    prepared_queries.append({"message": f"Solving query: {current_query} with {group_combination}", 
                                                             "raw_query":query, 
                                                             "replace_vars":solved_dependencies_set, 
                                                             "chat": self.filter_chat_history(curr_chat_history, {**tmp_input_set, **tmp_group_set}, histType = query.get('histType'))})
                                    solved_queries.add(current_query)
            if current_query in solved_queries:
                results, queries_made, query_solved_dependencies, query_chat_history = self.process_prepared_queries(prepared_queries, batch_process=query.get('batch_process') or self.batch_process)
                query_results['queries'].extend(queries_made)
                query_results[current_query].extend(results)
                chat_history[current_query].extend(query_chat_history)
                available_dependencies_set = {**available_dependencies_set, **query_solved_dependencies}
            else:
                print(f"[Query Processor] Warning: Not capable of solving dependency for query {current_query}")
                missing = [dep for dep in dependencies if dep not in solved_dependencies]
                print(f"  - missing dependencies:   {missing}")
                print(f"  - required dependencies:  {dependencies}")
                print(f"  - available dependencies: {solved_dependencies}")
            
        return query_results


    def filter_chat_history(self, curr_chat_history, filter_set=None, histType = False):
        """
        Filter chat history based on placeholders and remove duplicates.

        Args:
            curr_chat_history (list): The current chat history to filter.
            filter_set (dict): The dictionary of placeholders to match against.

        Returns:
            list: A list of unique chat history entries that match the placeholders.
        """
        if not curr_chat_history:
            out = []
        elif filter_set is None:
            out = [ entry['chat_history'] for entry in curr_chat_history ]
            #out = [item for sublist in filtered_chat_history for item in sublist]
        else:
            filtered_history = list(filter(lambda entry: all(entry.get(key) == value for key, value in filter_set.items()), curr_chat_history))
            out = [ entry['chat_history'] for entry in filtered_history ] #chat_only

        if histType == 'systemOnly':
            out = [element for element in out if element.get('role') == 'system']

        #remove repeated elements
        if len(out) > 1:
            unique_data = []
            seen = set()
            for item in out:
                pair = (item['role'], item['content'])
                if pair not in seen:
                    unique_data.append(item)
                    seen.add(pair)
        else:
            unique_data = out
        #len(out) - len(unique_data)

        return unique_data  # Return the unique list
