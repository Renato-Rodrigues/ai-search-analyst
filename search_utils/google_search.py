# Google Custom Search API integration
import requests
from config import config
import warnings

#search_query = out['search_query']
#exactTerms = out['exactTerms']
#orTerms = out['orTerms']
#num_results = out['num_results']
#dateRestrict = out['dateRestrict']

#https://console.cloud.google.com/apis/api/customsearch.googleapis.com/quotas?project=searchandprocess

def perform_google_search(search_query, exactTerms, orTerms, num_results, dateRestrict):
    # Limit num_results to 100
    if num_results > 100:
        warnings.warn("Google Search API limits results to 100. Limiting num_results to 100.", UserWarning)
        num_results = 100

    api_key = config['search_engines']['google']['api_key']
    search_engine_id = config['search_engines']['google']['search_engine_id']
    url = 'https://www.googleapis.com/customsearch/v1'
    all_results = []

    #https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list
    #siteSearch = config['search_engines']['google']['siteSearch']
    #siteSearchFilter = config['search_engines']['google']['siteSearchFilter']

    for start_index in range(1, num_results + 1, 10):
        params = {
            'q': search_query,
            'exactTerms': [exactTerms],
            'orTerms': [orTerms],
            'key': api_key,
            'cx': search_engine_id,
            'start': start_index,
            'num': min(10, num_results - start_index + 1),
            'dateRestrict': dateRestrict
        }

        response = requests.get(url, params=params)
        #https://cloud.google.com/storage/docs/json_api/v1/status-codes
        
        error_messages = {
            400: "Bad request to Google API.",
            401: "Unauthorized access to Google API.",
            403: "Forbidden access to Google API.",
            404: "Google API endpoint not found.",
            405: "Method not allowed for Google API request.",
            408: "Request timeout for Google API.",
            409: "Conflict in Google API request.",
            410: "Google API resource is gone.",
            411: "Length required for Google API request.",
            412: "Precondition failed for Google API request.",
            413: "Payload too large for Google API request.",
            416: "Requested range not satisfiable for Google API.",
            429: "Too Many Requests. Google API quota may have been exceeded.",
            499: "Client closed request to Google API.",
            500: "Internal server error in Google API.",
            502: "Bad gateway error from Google API.",
            503: "Google API service unavailable.",
            504: "Gateway timeout from Google API."
        }
        if response.status_code in error_messages:
            error_message = f"{error_messages[response.status_code]} Status code: {response.status_code}"
            warnings.warn(error_message, UserWarning)
            return {'error': error_message}  # Return error in a format that won't be cached
        
        print(f"Performing search for: {params['q']}, exactTerms: {params['exactTerms']}, orTerms: {params['orTerms']}") # Log the search parameters
            
        search_results = response.json().get('items', [])
        
        if not search_results:
            error_message = "No search results found. There might be an error in the formulation of the search query."
            warnings.warn(error_message, UserWarning)
            return {'error': error_message}  # Return error in a format that won't be cached

        all_results.extend([{
            'title': item['title'],
            'displayLink': item['displayLink'],
            'link': item['link'],
            'snippet': item.get('pagemap', {}).get('metatags', [{}])[0].get('og:description', item['snippet'])
        } for item in search_results])

        if len(search_results) < 10:
            break

    return all_results[:num_results]

