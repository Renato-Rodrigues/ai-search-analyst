from search_utils.google_search import perform_google_search
from search_utils.bing_search import perform_bing_search
from cache_utils import cache_result

@cache_result
def perform_search(search_query, exactTerms, orTerms, num_results, dateRestrict, search_service, disable_cache=False):
    """Perform search."""
    if search_service == 'bing':
        return perform_bing_search(search_query, exactTerms, orTerms, num_results, dateRestrict)
    else:
        return perform_google_search(search_query, exactTerms, orTerms, num_results, dateRestrict)

