import json
import functools
import os

def cache_result(func):
    @functools.wraps(func)
    def wrapper(*args, disable_cache=False, **kwargs):
        if isinstance(disable_cache, str):
            disable_cache = disable_cache.lower() == 'true'
        
        if disable_cache:
            return func(*args, **kwargs)

        # Generate a unique cache key
        cache_key = f"{func.__name__}:{json.dumps(args)}:{json.dumps({k: v for k, v in sorted(kwargs.items()) if k != 'disable_cache'})}"
        
        print(f"Debug: Cache key: {cache_key}")  # Debug print

        # Load the cache
        cache = load_cache()
        
        # Check if result is in cache and is not empty
        if cache_key in cache and is_valid_cache_value(cache[cache_key]):
            print(f"Cache hit for {cache_key}")
            return cache[cache_key]
        
        print(f"Cache miss for {cache_key}")  # Debug print
        
        # If not in cache or cache is empty, call the function
        result = func(*args, **kwargs)
        
        # Store the result in cache only if it's not an error message, not empty, and not an empty list
        if not isinstance(result, dict) or ('error' not in result and is_valid_cache_value(result) and result != []):
            cache[cache_key] = result
            save_cache(cache)
        else:
            print(f"Not caching result for {cache_key}")
        
        return result
    return wrapper

def is_valid_cache_value(value):
    """Check if the cache value is valid (not empty)."""
    if value is None:
        return False
    if isinstance(value, (dict, list, tuple, str)) and not value:
        return False
    return True

def clear_cache():
    """
    Clears the entire cache.
    """
    cache = load_cache()
    cache.clear()
    save_cache(cache)
    print("Cache cleared")

def load_cache():
    try:
        with open('api_cache.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_cache(cache):
    with open('api_cache.json', 'w') as f:
        json.dump(cache, f)

def clear_invalid_cache():
    """
    Clears invalid entries from the cache file.
    """
    cache_file = 'api_cache.json'
    if not os.path.exists(cache_file):
        print("Cache file does not exist.")
        return

    try:
        with open(cache_file, 'r') as f:
            cache = json.load(f)
    except json.JSONDecodeError:
        print("Error reading cache file. Clearing entire cache.")
        os.remove(cache_file)
        return

    original_size = len(cache)
    cache = {k: v for k, v in cache.items() if is_valid_cache_value(v)}
    new_size = len(cache)

    if new_size < original_size:
        with open(cache_file, 'w') as f:
            json.dump(cache, f)
        print(f"Cleared {original_size - new_size} invalid entries from cache.")
    else:
        print("No invalid entries found in cache.")