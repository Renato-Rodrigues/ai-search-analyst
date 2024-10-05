
import json
import re
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
                new_dynamic_vars = list(set(var if var.endswith('_set')  else f"{var}_set" for var in dynamic_vars)) + list(set(f"{var}_group" for var in dynamic_vars if not var.endswith('_set'))) + dynamic_vars
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
        processed_query= utils.flatten_json({**replaced_items, **out})
        
        if query in self.llm_queries:
            out['result'], this_chat, full_chat_history = ai_query(query=out['query'], role=out.get('role', False), format=out.get('format', False), chat_history=chat, ai_service=self.ai_service, model=out.get('model', self.model), disable_cache=out.get('disable_cache', False))
            if 'result' in out['result']:
                out['result'] = out['result']['result'] #results are included in a result dicitionary due to the json schema I use
        elif query in self.search_queries:
            out['num_results'] = max(10,min(self.config['test']['search_results'], int(out['num_results'])) if self.config['test_mode'] else int(out['num_results']))
            out['result'] = perform_search(out['search_query'], out['exactTerms'], out['orTerms'], out['num_results'], out['dateRestrict'], self.search_engine, disable_cache=out.get('disable_cache', False))
            this_chat = []
            for index in range(len(out['result'])):
                out['result'][index] = {**replaced_items, **out['result'][index]} 

        # Update placeholders_variables with query results based on dynamic_var
        sets = {**replace_vars}
        if 'dynamic_var' in query:
            dynamic_vars = self.parse_dynamic_var(query['dynamic_var'])
            for var in dynamic_vars:
                if f"{var}_group" not in sets:
                    sets[f"{var}_group"] = []
                items = []
                if isinstance(out['result'], list):
                    for item in out['result']:
                        if var in item:
                            items.append(item[var])
                if items:
                    sets[f"{var}_set"] = items
                    sets[f"{var}_group"].append({**replaced_items, **{f"{var}_set":items}})
        
        # Create a new DataFrame for this query results
        try:
            results = utils.flatten_json(out['result'])
        except json.JSONDecodeError:  # Added exception handling
            results = out['result']
            pass 

        # chat history dictionary
        chat_dic = { **replaced_items, 'chat_history': this_chat }

        return results, processed_query, sets, chat_dic

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
        queries_to_process = sorted_queries[:4] if self.config['test_mode'] else sorted_queries
        
        # Initialize values directly obtained from inputs data
        input_sets = {f"{k}_set": v for item in self.inputs for k, v in item.items()} 
        input_dependencies = list(input_sets.keys()) 
        input_loop_dependencies = [item[:-4] for item in input_dependencies]

        # start solving dependencies and running the queries
        query_results = {}
        query_results['queries'] = []
        chat_history = {}
        solved_queries = set()
        available_dependencies_set = input_sets 
        
        for query_index, query in enumerate(queries_to_process):
            current_query = query['title']
            print(f"Solving Query number: {query_index} of {len(queries_to_process)}, named: {current_query}")
            dependencies = list(dependency_graph.get(query_index, set())) # list of dependencies
            query_results[current_query] = []
            chat_history[current_query] = []
            curr_chat_history = []
            for dep in dependencies:
                if isinstance(dep, str) and ',' in dep:  # Check for comma-separated values
                    dep_titles = [title.strip() for title in dep.split(',')]
                    for title in dep_titles:
                        if title in chat_history:
                            curr_chat_history.extend(chat_history[title])  # Append results for each title
                elif dep in query_results:
                    curr_chat_history.extend(chat_history[dep])  # Append results for the single dependency
            solved_dependencies = list(available_dependencies_set.keys()) + list(solved_queries)
            solved_dependencies_set = {**available_dependencies_set}
            if all(dep in solved_dependencies for dep in dependencies):
                print(f"Solving query: {current_query}") 
                res, processed_query, query_solved_dependencies, query_chat_history = self.process_single_query(query, replace_vars=solved_dependencies_set, chat=self.filter_chat_history(curr_chat_history))
                query_results['queries'].extend(processed_query)
                query_results[current_query].extend(res)
                chat_history[current_query].append(query_chat_history)
                filtered_set_dependencies = {k: v for k, v in query_solved_dependencies.items() if k not in [k for k in available_dependencies_set.keys() if k.endswith('_set')]} # do not redefine _set placeholders
                #available_dependencies_set.expand(filtered_set_dependencies)
                available_dependencies_set = {**available_dependencies_set, **filtered_set_dependencies}
                solved_queries.add(current_query)
            else:
                # loop input sets that are part of the current dependencies
                loop_dependencies = [item for item in input_loop_dependencies if item in dependencies]
                loop_sets = {k[:-4]: v for k, v in input_sets.items() if k[:-4] in loop_dependencies}
                tmp_set = {}
                tmp_group_set = {}
                for input_combination in itertools.product(*list(loop_sets.values())):
                    tmp_set = {k: v for k, v in zip(loop_sets.keys(), input_combination)}
                    group_dependencies = [ dep[:-6] for dep in dependencies if dep.endswith('_group') ]
                    if group_dependencies:
                        for group in group_dependencies:
                            #group = group_dependencies[0]
                            group_sets = {k:v for k,v in available_dependencies_set.items() if k == f"{group}_group"}[f"{group}_group"]
                            filter_group_sets = [ item for item in group_sets if all(item.get(key) == value for key, value in tmp_set.items()) ]
                            filter_group = [item[f"{group}_set"] for item in filter_group_sets]
                            flattened_group = [link for sublist in filter_group for link in sublist] 
                            tmp_group_set.append({f"{group}_group":flattened_group})
                    solved_dependencies = list(available_dependencies_set.keys()) + list(tmp_set.keys()) + list(tmp_group_set.keys())  + list(solved_queries)
                    solved_dependencies_set = {**available_dependencies_set, **tmp_set, **tmp_group_set}
                    if all(dep in solved_dependencies for dep in dependencies):
                        print(f"Solving query: {current_query} with {input_combination}") 
                        res, processed_query, query_solved_dependencies, query_chat_history = self.process_single_query(query, replace_vars=solved_dependencies_set, chat=self.filter_chat_history(curr_chat_history, tmp_set))
                        query_results['queries'].extend(processed_query)
                        query_results[current_query].extend(res)
                        chat_history[current_query].append(query_chat_history)
                        filtered_loop_set_dependencies = {k: v for k, v in query_solved_dependencies.items() if k not in list(loop_sets.keys())} #do not include for loop based values
                        filtered_set_dependencies = {k: v for k, v in filtered_loop_set_dependencies.items() if k not in [k for k in available_dependencies_set.keys() if k.endswith('_set')]} # do not redefine _set placeholders
                        #available_dependencies_set.expand(filtered_set_dependencies)
                        available_dependencies_set = {**available_dependencies_set, **filtered_set_dependencies}
                        solved_queries.add(current_query)
                    else:
                        # loop by remaining dependendencies sets
                        remaining_dependencies = [dep for dep in dependencies if not dep in input_dependencies+loop_dependencies+list(solved_queries)]
                        remaining_sets = {k[:-4]: v for k, v in available_dependencies_set.items() if k[:-4] in remaining_dependencies}
                        tmp2_set = {}
                        for remaining_combination in itertools.product(*list(remaining_sets.values())):
                            tmp2_set = {k: v for k, v in zip(remaining_sets.keys(), remaining_combination)}
                            solved_dependencies = list(available_dependencies_set.keys()) + list(tmp_set.keys()) + list(tmp_group_set.keys())  + list(tmp2_set.keys()) + list(solved_queries)
                            solved_dependencies_set = {**available_dependencies_set, **tmp_set, **tmp_group_set, **tmp2_set}
                            if all(dep in solved_dependencies for dep in dependencies):
                                print(f"Solving query: {current_query} with {input_combination} and {remaining_combination}") 
                                res, processed_query, query_solved_dependencies, query_chat_history = self.process_single_query(query, replace_vars=solved_dependencies_set, chat=self.filter_chat_history(curr_chat_history, {**tmp_set, **tmp2_set}))
                                query_results['queries'].extend(processed_query)
                                query_results[current_query].extend(res)
                                chat_history[current_query].append(query_chat_history)
                                filtered_remaining_set_dependencies = {k: v for k, v in query_solved_dependencies.items() if k not in list(remaining_sets.keys())} #do not include for loop based values
                                filtered_remaining_set_dependencies = {k: v for k, v in filtered_remaining_set_dependencies.items() if k not in [k for k in available_dependencies_set.keys() if k.endswith('_set')]} # do not redefine _set placeholders
                                #available_dependencies_set.expand(filtered_remaining_set_dependencies)
                                available_dependencies_set = {**available_dependencies_set, **filtered_remaining_set_dependencies}
                                solved_queries.add(current_query)
            if current_query not in solved_queries:
                print(f"Warning: Not capable of solving dependency for query {current_query}")
                missing = [dep for dep in dependencies if dep not in solved_dependencies]
                print(f"Missing dependencies: {missing} required ({dependencies}), available (solved_dependencies).")

        return query_results
    

    def filter_chat_history(self, curr_chat_history, filter_set=None):
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
            filtered_chat_history = [ entry['chat_history'] for entry in curr_chat_history ]
            out = [item for sublist in filtered_chat_history for item in sublist]
        else:
            filtered_history = list(filter(lambda entry: all(entry.get(key) == value for key, value in filter_set.items()), curr_chat_history))
            chat_only = [ entry['chat_history'] for entry in filtered_history ]
            out = [item for sublist in chat_only for item in sublist]

        #remove repeated elements
        unique_data = []
        seen = set()
        for item in out:
            pair = (item['role'], item['content'])
            if pair not in seen:
                unique_data.append(item)
                seen.add(pair)
        #len(out) - len(unique_data)

        return unique_data  # Return the unique list

