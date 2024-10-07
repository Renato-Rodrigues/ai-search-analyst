from cache.cache_database import CacheDatabase
from cache.cache import cache_function





cache_db = CacheDatabase()

x = cache_db.load_all_cache()
x.keys()
cache_db.delete_cache("aaa")

cache_db.save_cache("aaa", ([{"aaa":"aaa"}],["bbb"]))

cache_db.load_cache("aaa")




cache_db.save_cache("aaa", "bbb")
cache_db.load_cache("aaa")
#cached_result = cache_db.load_cache("e5b278a859956e5cee382aa4a7e45c4e")
cache_db.load_cache("b95408b9409ad0769df1147be086e2ee")

tuple(cache_db.load_cache("0e16a4f0242642b348e2c420849a9cb6"))[3]

a= cache_db.load_cache("0e16a4f0242642b348e2c420849a9cb6")


len(cache_db.load_cache("0e16a4f0242642b348e2c420849a9cb6"))

a, b, c = cache_db.load_cache("0e16a4f0242642b348e2c420849a9cb6")



cache_db.save_cache("aaa", (["aaa"],["bbb"]))
cache_db.load_cache("aaa")

@cache_function(batch_mode=True)  # Batch mode for gpt_query
def gpt_query(queries, role=None, format=None, chat_history=None, model="gpt-4o-mini"):
    # Simulating the original logic
    ordered_responses = queries
    if isinstance(queries,list):
        current_chat_instance = [role + format for _ in queries]
    else: 
        current_chat_instance = role + format
    full_history = [None for _ in queries]  # Simulating None for each query
    print(ordered_responses)
    print(current_chat_instance)
    print(full_history)
    return ordered_responses, current_chat_instance, full_history

@cache_function()  # Non-batch mode for a simple function
def simple_function(x):
    return x * x  # Just return a single result

# Example calls for batch processing
results = gpt_query(
    queries=['Query1', 'Query2'],
    role='Expert',
    format='json',
    chat_history='Some chat history',
    model='gpt-4o-mini'
)


results2 = gpt_query(
    queries=['Query1'],
    role='Expert',
    format='json',
    chat_history='Some chat history',
    model='gpt-4o-mini'
)

results3 = gpt_query(
    queries='Query1',
    role='Expert',
    format='json',
    chat_history='Some chat history',
    model='gpt-4o-mini'
)

# Example calls for single result function
result4 = simple_function(5)
print(result4)  # Should output: 25

result5 = simple_function(5)
print(result5)  # Should load from cache: 25



cache_results = [ ([{"a":"1"}], ["ccc"]), (["bbb"], ["ddd"]) ]

# Generic way to combine them into a tuple of lists
result = tuple([list(sum((item if isinstance(item, list) else [item] for item in group), [])) for group in zip(*cache_results)])



# Example usage
db = CacheDatabase()

# Saving a dictionary
test_dict = {"key1": "value1", "key2": "value2"}
db.save_cache("test_dict_key", test_dict)

# Loading the dictionary
loaded_dict = db.load_cache("test_dict_key")
print(loaded_dict)  # Should output