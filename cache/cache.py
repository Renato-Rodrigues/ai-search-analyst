import hashlib
import pickle
from functools import wraps
from cache.cache_database import CacheDatabase

# Initialize the cache database
cache_db = CacheDatabase()

def serialize_arguments(*args, **kwargs):
    """Serialize both list and non-list arguments for cache key creation."""
    def serialize(value):
        if isinstance(value, (list, dict)):
            return pickle.dumps(value)
        return str(value)
    
    serialized_args = [serialize(arg) for arg in args]
    serialized_kwargs = {k: serialize(v) for k, v in kwargs.items()}
    
    return serialized_args, serialized_kwargs

def generate_cache_key(func_name, serialized_args, serialized_kwargs):
    """Create a unique cache key based on function name and serialized arguments."""
    key_parts = [func_name]
    key_parts.extend(serialized_args)
    key_parts.extend([f"{k}:{v}" for k, v in serialized_kwargs.items()])
    cache_key = hashlib.md5("".join(key_parts).encode()).hexdigest()
    return cache_key

def cache_function(batch_mode=False, disable_cache=False):
    """Decorator to handle caching of function results."""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            #print(f"\n[Cache] Function '{func.__name__}' called with args: {args}, kwargs: {kwargs}")
            
            if disable_cache:
                print("[Cache] Cache is disabled. Executing function without loading or saving cache.")
                return func(*args, **kwargs)

            # Check if batch mode should be enabled based on any list in args or kwargs
            is_batch_mode = batch_mode or any(isinstance(arg, list) for arg in args) or any(isinstance(v, list) for v in kwargs.values())

            if is_batch_mode:
                # Find the longest list for batch mode (either from args or kwargs)
                list_lengths = [len(arg) for arg in args if isinstance(arg, list)]
                list_lengths.extend([len(v) for v in kwargs.values() if isinstance(v, list)])
                max_length = max(list_lengths) if list_lengths else 1

                print(f"[Cache] Batch mode enabled. Processing {max_length} items.")

                cache_results = [None] * max_length
                missing_indices = []

                # Check cache for each index
                for index in range(max_length):
                    current_args = list(args)
                    current_kwargs = kwargs.copy()

                    # Update current_args for batch mode (split list elements)
                    for i, arg in enumerate(current_args):
                        if isinstance(arg, list):
                            current_args[i] = arg[0] if len(arg) == 1 else arg[index]
                    #for i, arg in enumerate(current_args):
                    #    if isinstance(arg, list):
                    #        current_args[i] = arg[index]  # Pick the element at the current index

                    # Update current_kwargs for batch mode (split list elements)
                    for k, v in current_kwargs.items():
                        if isinstance(v, list):
                            current_kwargs[k] = v[0] if len(v) == 1 else v[index]
                    #for k, v in current_kwargs.items():
                    #    if isinstance(v, list):
                    #        current_kwargs[k] = v[index]  # Pick the element at the current index

                    # Generate cache key for current index
                    current_key = generate_cache_key(func.__name__,
                        serialize_arguments(*current_args)[0],
                        serialize_arguments(**current_kwargs)[1])

                    cached_result = cache_db.load_cache(current_key)
                    if cached_result:
                        print(f"[Cache] Cache hit for query {index} (key: {current_key})")
                        cache_results[index] = cached_result
                    else:
                        print(f"[Cache] Cache miss for query {index} (key: {current_key}). Marking for execution.")
                        missing_indices.append(index)

                # If there are cache misses, call the function for the missing inputs
                if missing_indices:
                    missing_args = list(args)
                    missing_kwargs = kwargs.copy()

                    for i in range(len(missing_args)):
                        if isinstance(missing_args[i], list):
                            missing_args[i] = [args[i][index] for index in missing_indices]

                    for k, v in missing_kwargs.items():
                        if isinstance(v, list):
                            missing_kwargs[k] = [kwargs[k][index] for index in missing_indices]

                    print(f"[Cache] Executing function for missing queries: {missing_indices}")
                    missing_results = func(*missing_args, **missing_kwargs)

                    # Handle the results based on whether the function returns a tuple
                    if isinstance(missing_results, tuple):
                        for i, index in enumerate(missing_indices):
                            new_results = []
                            for j, result_part in enumerate(missing_results):
                                if new_results is None:
                                    new_results = []
                                new_results.append(result_part[i])
                            cache_results[index] = tuple(new_results)

                            current_args = list(args)
                            current_kwargs = kwargs.copy()

                            # Update current_args and current_kwargs for cache saving
                            for k in range(len(current_args)):
                                if isinstance(current_args[k], list):
                                    current_args[k] = args[k][0] if len(args[k]) == 1 else args[k][index]
                            for kwarg_key in current_kwargs:
                                if isinstance(kwargs[kwarg_key], list):
                                    current_kwargs[kwarg_key] = kwargs[kwarg_key][0] if len(kwargs[kwarg_key]) == 1 else kwargs[kwarg_key][index]
                            #for k in range(len(current_args)):
                            #    if isinstance(current_args[k], list):
                            #        current_args[k] = args[k][index]
                            #for kwarg_key in current_kwargs:
                            #    if isinstance(kwargs[kwarg_key], list):
                            #        current_kwargs[kwarg_key] = kwargs[kwarg_key][index]

                            current_key = generate_cache_key(func.__name__,
                                serialize_arguments(*current_args)[0],
                                serialize_arguments(**current_kwargs)[1])
                            
                            if 'error' in cache_results[index]:
                                print(f"[Cache] Cache not saved because error keyword was found.")
                            else:
                                print(f"[Cache] Saving tuple results to cache for query {index} (key: {current_key})")
                                cache_db.save_cache(current_key, cache_results[index])

                        result = tuple([list(sum((item if isinstance(item, list) else [item] for item in group), [])) for group in zip(*cache_results)])
                        return result
                    else:
                        # Handle single-result functions
                        for i, index in enumerate(missing_indices):
                            cache_results[index] = missing_results[i]
                            current_args = list(args)
                            current_kwargs = kwargs.copy()

                            # Update current_args and current_kwargs for cache saving
                            for k in range(len(current_args)):
                                if isinstance(current_args[k], list):
                                    current_args[k] = args[k][0] if len(args[k]) == 1 else args[k][index]
                            for kwarg_key in current_kwargs:
                                if isinstance(kwargs[kwarg_key], list):
                                    current_kwargs[kwarg_key] = kwargs[kwarg_key][0] if len(kwargs[kwarg_key]) == 1 else kwargs[kwarg_key][index]

                            current_key = generate_cache_key(func.__name__,
                                serialize_arguments(*current_args)[0],
                                serialize_arguments(**current_kwargs)[1])

                            if 'error' in cache_results[index]:
                                print(f"[Cache] Cache not saved because error keyword was found.")
                            else:
                                print(f"[Cache] Saving result to cache for query {index} (key: {current_key})")
                                cache_db.save_cache(current_key, missing_results[i])
                        result = tuple([list(sum((item if isinstance(item, list) else [item] for item in group), [])) for group in zip(*cache_results)])
                        return result
                else:
                    result = tuple([list(sum((item if isinstance(item, list) else [item] for item in group), [])) for group in zip(*cache_results)])
                    return result
            
            else: # handling load and save cache for functions that are no batch calls
                current_args = list(args)
                current_kwargs = kwargs.copy()
                for i, arg in enumerate(current_args):
                    if isinstance(arg, list):
                        current_args[i] = arg[0] if len(arg) == 1 else arg[index]
                for k, v in current_kwargs.items():
                    if isinstance(v, list):
                        current_kwargs[k] = v[0] if len(v) == 1 else v[index]
                
                # Generate cache key for current index
                single_cache_key = generate_cache_key(func.__name__,
                    serialize_arguments(*current_args)[0],
                    serialize_arguments(**current_kwargs)[1])

                cached_result = cache_db.load_cache(single_cache_key)
                if cached_result:
                    print(f"[Cache] Cache hit for single query (key: {single_cache_key})")
                    return cached_result
                else:
                    print(f"[Cache] Cache miss for single query (key: {single_cache_key}). Executing function.")
                    result = func(*args, **kwargs)
                    if 'error' in result:
                        print(f"[Cache] Cache not saved because error keyword was found.")
                    else:
                        print(f"[Cache] Saving result to cache for query (key: {single_cache_key})")
                        cache_db.save_cache(single_cache_key, result)
                    return result
        
        return wrapper
    
    return decorator
