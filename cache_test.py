from cache.cache_database import CacheDatabase
from cache.cache import cache_function


cache_db = CacheDatabase()

x = cache_db.load_all_cache()

cache_db.delete_cache(['cb0be629542a195cc3949f4d74383b2f'])

cache_db.load_cache('1b0cf888bed19f82ca4b946214e60979')

1b0cf888bed19f82ca4b946214e60979

'4de9c2437311062027ce62772ca1f01e'



cache_db.load_cache('50b262a8517920306b6ef9f9c0b9d7e4')

cache_db.delete_cache(['50b262a8517920306b6ef9f9c0b9d7e4'])


50b262a8517920306b6ef9f9c0b9d7e4

dictionary = {'7f1a0ca241a2e16bda1900915d0f91d9': ('{"result":[{"sector":"Manufacture of basic metals","topic":"Natural resources","publisher":"International Peace Information Service","year":"2023","source":"https://ipisresearch.be/home/natural-resources/","source_type":"Website","summary":"The International Peace Information Service examines the interplay between natural resources and human rights violations, particularly focusing on the mining and metals sectors. The document discusses various regions where the extraction of resources contributes to conflicts and human rights abuses.","sector_coverage":"High coverage of the sector Manufacture of basic metals","subject":"Empirical (direct) relevance","author":"International organizations (i.e., UN, ILO, WHO, OECD) or global NGOs (e.g., HRW, Amnesty International)","publish_period":"Published within the last 4 years (2023 - 2020)","humand_rights_infrigement":"yes","humand_rights_infrigement_description":"The report provides evidence of human rights abuses linked to the mining of metals, particularly in conflict zones where extractive industries operate without adequate oversight, leading to displacement of communities and environmental degradation.","countries":"Democratic Republic of the Congo, Angola, and other Central African countries","countries_mentions":"The report highlights that resource extraction in the Democratic Republic of the Congo has led to severe social and environmental impacts, with quotes discussing the displacement of individuals and communities detrimental to their rights and livelihoods."}]}', [{'role': 'user', 'content': 'Using the information from the link **https://ipisresearch.be/home/natural-resources/**, analyze and answer the questions in the provided JSON schema, focusing on the sector **Manufacture of basic metals** and the human rights and environmental topic **Natural resources**.\n\nYour goal is to produce a structured, high-quality report that summarizes the contents of the link, assesses the risk of human rights or environmental violations, and classifies the credibility and relevance of the information. Ensure your responses align with the provided source and contribute to a comprehensive risk analysis in the sector.\n\nFollow these steps:\n1. Review the provided link for sector and topic relevance.\n2. Summarize the key findings from the source.\n3. Classify the information according to the criteria provided in the JSON schema (sector coverage, topic relevance, author credibility, etc.).\n4. Identify and describe any human rights or environmental infringements discussed in the source.\n5. Mention the countries or regions referenced in the source and provide quotes where applicable.\n6. Make sure to reference the publication date and classify how recent and reliable the source is.'}, {'role': 'system', 'content': '{"result":[{"sector":"Manufacture of basic metals","topic":"Natural resources","publisher":"International Peace Information Service","year":"2023","source":"https://ipisresearch.be/home/natural-resources/","source_type":"Website","summary":"The International Peace Information Service examines the interplay between natural resources and human rights violations, particularly focusing on the mining and metals sectors. The document discusses various regions where the extraction of resources contributes to conflicts and human rights abuses.","sector_coverage":"High coverage of the sector Manufacture of basic metals","subject":"Empirical (direct) relevance","author":"International organizations (i.e., UN, ILO, WHO, OECD) or global NGOs (e.g., HRW, Amnesty International)","publish_period":"Published within the last 4 years (2023 - 2020)","humand_rights_infrigement":"yes","humand_rights_infrigement_description":"The report provides evidence of human rights abuses linked to the mining of metals, particularly in conflict zones where extractive industries operate without adequate oversight, leading to displacement of communities and environmental degradation.","countries":"Democratic Republic of the Congo, Angola, and other Central African countries","countries_mentions":"The report highlights that resource extraction in the Democratic Republic of the Congo has led to severe social and environmental impacts, with quotes discussing the displacement of individuals and communities detrimental to their rights and livelihoods."}]}'}], {'role': 'system', 'content': '{"result":[{"sector":"Growing of perennial crops","topic":"Trade union rights","publisher":"U.S. Department of Labor (DOL)","year":"2023","source":"https://www.dol.gov/agencies/whd/flsa/misclassification","source_type":"Website","summary":"The document discusses the classification of workers under the Fair Labor Standards Act (FLSA) and the implications of misclassification, including potential violations of trade union rights.","sector_coverage":"Limited overlap with the sector Growing of perennial crops, e.g., only the manufacturing of a specific product which is part of the sector Growing of perennial crops is mentioned","subject":"Causal (indirect) relevance","author":"International organizations (i.e., UN, ILO, WHO, OECD) or global NGOs (e.g., HRW, Amnesty International)","publish_period":"Published within the last 4 years (2023 - 2020)","humand_rights_infrigement":"yes","humand_rights_infrigement_description":"The document indicates that misclassification of workers can lead to violations of trade union rights, as misclassified workers may not have access to union benefits and protections.","countries":"United States","countries_mentions":"The source primarily references the United States in the context of labor law and worker rights."}]}'})}  

def search_partial_match(dictionary, search_term):
    return {key: value for key, value in dictionary.items() if search_term in str(value)}

next(iter(search_partial_match(x,'{"result":[{"sector":"Animal production","topic":"Child labour","topic_alias":"').items()))


search_partial_match(x,'{"result":[{"sector":"Animal production","topic":"Child labour","topic_alias":"').keys()

search_partial_match(x,'{"result":[{"sector":"Animal production","sector_alias":"').keys()

next(iter(search_partial_match(x,'{"result":[{"sector":"Animal production","topic":"Child labour","topic_alias":"').items()))



cache_db.load_cache('0e16a4f0242642b348e2c420849a9cb6')

a=cache_db.load_cache('e37b6d7f5d51d386d78cda0520fca54f')
b=cache_db.load_cache('60727e4751cab7b1a91c962a740371bb')


cache_db.load_cache('9f365fdcee06caed01bfae731d6b0f18')


cache_db.load_cache("d773ac651456f95f6eb9e16c2e0bf627")


cache_db.load_cache("0e16a4f0242642b348e2c420849a9cb6")

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