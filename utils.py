import re

def replace_placeholders(item, variables):
    """
    Replaces placeholders in the text or dictionary values with corresponding variable values.
    
    :param item: The text or dictionary containing placeholders
    :param variables: A dictionary of variable names and their values
    :return: The text or dictionary with placeholders replaced
    """
    if isinstance(item, str):
        return re.sub(r'\[\[(.*?)\]\]', lambda m: str(variables.get(m.group(1), m.group(0))), item)
    elif isinstance(item, dict):
        return {k: replace_placeholders(v, variables) for k, v in item.items()}
    else:
        return item

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

# Clear invalid cache entries
# from cache_utils import clear_invalid_cache
# #clear_invalid_cache()
