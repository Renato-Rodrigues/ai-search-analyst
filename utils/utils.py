import re
import importlib

class Utils:
    def __init__(self):
        pass  # You can initialize any instance variables here if needed

    def replace_placeholders(self, item, variables, listMode='array_str', replaced_items=None):
        """
        Replaces placeholders in the text or dictionary values with corresponding variable values.
        
        :param item: The text or dictionary containing placeholders
        :param variables: A dictionary of variable names and their values
        :param listMode: array_str, converts lists to a string in array format, list_str, converts lists to a comma separated list
        :param replaced_items: A dictionary to store the replaced items
        :return: A tuple containing the text or dictionary with placeholders replaced and a dictionary of replaced items
        """

        if replaced_items is None:
            replaced_items = {}  # Initialize only once for the top-level call

        def replace_match(match):
            key = match.group(1)
            value = variables.get(key, f"[[{key}]]")
            replaced_items[key] = value
            if isinstance(value, list):  # Convert lists to a string representation
                if listMode == 'array_str':
                    value = "[" + ", ".join(f'"{str(v)}"' if isinstance(v, str) else str(v) for v in value) + "]"
                else:
                    value = ', '.join(value)
            elif isinstance(value, str):
                value = value.replace('\\"', '"')
            return value

        if isinstance(item, str):
            modified_item = re.sub(r'\[\[(.*?)\]\]', replace_match, item)
            return modified_item, replaced_items

        elif isinstance(item, dict):
            modified_dict = {}
            for k, v in item.items():
                if isinstance(v, tuple):
                    replaced_value, replaced_nested = self.replace_placeholders(v[1], variables, listMode, replaced_items)
                    modified_dict[k] = (v[0], replaced_value)
                else:
                    modified_dict[k], _ = self.replace_placeholders(v, variables, listMode, replaced_items)
            return modified_dict, replaced_items

        else:
            return item, replaced_items

    def reload_module(self, module_name):
        """
        Reload a module and return its updated functions.
        
        :param module_name: The name of the module to reload (e.g., 'io_utils.google_sheets')
        :return: A dictionary of the module's updated functions
        """
        # Import the module
        module = importlib.import_module(module_name)
        
        # Reload the module
        importlib.reload(module)
        
        # Get all functions from the module
        functions = {name: func for name, func in module.__dict__.items() if callable(func) and not name.startswith('_')}
        
        return functions
    

    def flatten_json(self, data):
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

utils = Utils()

# Usage:
#updated_functions = reload_module('io_utils.google_sheets')

# Clear invalid cache entries
# from cache_utils import clear_invalid_cache
# #clear_invalid_cache()
