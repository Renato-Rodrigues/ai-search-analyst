import json
import functools
import os

# Ensure the data folder exists
if not os.path.exists('data'):
    os.makedirs('data')

def cache_result(func):
    @functools.wraps(func)
    def wrapper(*args, disable_cache=False, **kwargs):
        if isinstance(disable_cache, str):
            disable_cache = disable_cache.lower() == 'true'
        
        if disable_cache:
            return func(*args, **kwargs)

        # Generate a unique cache key
        cache_key = f"{func.__name__}:{json.dumps(args)}:{json.dumps({k: v for k, v in sorted(kwargs.items()) if k != 'disable_cache'})}"
        
        # Load the cache specific to this function
        cache = load_cache(func.__name__)
        
        # Check if result is in cache and is not empty
        if cache_key in cache and is_valid_cache_value(cache[cache_key]):
            print("Cache hit")
            return cache[cache_key]
        
        print("Cache miss")
        
        # If not in cache or cache is empty, call the function
        result = func(*args, **kwargs)
        
        # Store the result in cache only if it's valid
        if not isinstance(result, dict) or ('error' not in result and is_valid_cache_value(result) and result != []):
            cache[cache_key] = result
            save_cache(func.__name__, cache)
        else:
            print("Not caching results")
        
        return result
    return wrapper

def is_valid_cache_value(value):
    """Check if the cache value is valid (not empty)."""
    if value is None:
        return False
    if isinstance(value, (dict, list, tuple, str)) and not value:
        return False
    return True

def clear_cache(func_name=None):
    """
    Clears the cache for a specific function or all caches if no function name is provided.
    """
    if func_name:
        cache_file = f'data/{func_name}_cache.json'
        if os.path.exists(cache_file):
            os.remove(cache_file)
            print(f"Cache cleared for function: {func_name}")
        else:
            print(f"No cache found for function: {func_name}")
    else:
        for file in os.listdir('data'):
            if file.endswith('_cache.json'):
                os.remove(os.path.join('data', file))
        print("All caches cleared")

def load_cache(func_name):
    cache_file = f'data/{func_name}_cache.json'
    try:
        with open(cache_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_cache(func_name, cache):
    cache_file = f'data/{func_name}_cache.json'
    with open(cache_file, 'w') as f:
        json.dump(cache, f)

def clear_invalid_cache(func_name=None):
    """
    Clears invalid entries from the cache file for a specific function, or all cache files if no function name is provided.
    """
    if func_name:
        cache_file = f'data/{func_name}_cache.json'
        clear_invalid_entries(cache_file)
    else:
        for file in os.listdir('data'):
            if file.endswith('_cache.json'):
                clear_invalid_entries(os.path.join('data', file))

def clear_invalid_entries(cache_file):
    if not os.path.exists(cache_file):
        print(f"Cache file {cache_file} does not exist.")
        return

    try:
        with open(cache_file, 'r') as f:
            cache = json.load(f)
    except json.JSONDecodeError:
        print(f"Error reading cache file {cache_file}. Clearing entire cache.")
        os.remove(cache_file)
        return

    original_size = len(cache)
    cache = {k: v for k, v in cache.items() if is_valid_cache_value(v)}
    new_size = len(cache)

    if new_size < original_size:
        with open(cache_file, 'w') as f:
            json.dump(cache, f)
        print(f"Cleared {original_size - new_size} invalid entries from {cache_file}.")
    else:
        print(f"No invalid entries found in {cache_file}.")



# load cache and save only perform_serach to cache file
#import json

#cache_file = 'api_cache_2.json'
#with open(cache_file, 'r') as f:
#    cache_data = json.load(f)

#def filter_set_by_partial_match(a, c):
#    return {element for element in a if c in element}

#filteredCache = filter_set_by_partial_match(cache_data, "perform_search")

#class SetEncoder(json.JSONEncoder):
#    def default(self, obj):
#        if isinstance(obj, set):
#            return list(obj)
#        return json.JSONEncoder.default(self, obj)

#out = json.dumps(filteredCache, cls=SetEncoder)

#cache_file = f'data/perform_search_cache.json'
#with open(cache_file, 'w') as file:
#    file.write(out)


