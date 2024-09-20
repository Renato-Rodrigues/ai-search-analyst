# Bing Search API integration
import requests
from config import config
import warnings

def perform_bing_search(search_query, exactTerms, orTerms, num_results, dateRestrict):
    api_key = config['search_engines']['bing']['api_key']
    endpoint = 'https://api.bing.microsoft.com/v7.0/search'
    all_results = []

    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }

    # Construct the query
    query = f"{search_query} {exactTerms} {' OR '.join(orTerms.split())}"

    # Handle date restriction
    if dateRestrict:
        # Convert Google's dateRestrict format to Bing's freshness parameter
        freshness = 'Day' if 'd' in dateRestrict else 'Week' if 'w' in dateRestrict else 'Month' if 'm' in dateRestrict else 'Year'
        params = {
            'q': query,
            'count': min(50, num_results),  # Bing allows up to 50 results per request
            'freshness': freshness
        }
    else:
        params = {
            'q': query,
            'count': min(50, num_results)
        }

    response = requests.get(endpoint, headers=headers, params=params)

    error_messages = {
        400: "Bad request to Bing API.",
        401: "Unauthorized access to Bing API.",
        403: "Forbidden access to Bing API.",
        429: "Too Many Requests. Bing API quota may have been exceeded.",
        500: "Internal server error in Bing API."
    }

    if response.status_code in error_messages:
        warnings.warn(f"{error_messages[response.status_code]} Status code: {response.status_code}", UserWarning)
        return all_results

    search_results = response.json().get('webPages', {}).get('value', [])

    all_results.extend([{
        'title': item['name'],
        'displayLink': item['url'],
        'link': item['url'],
        'snippet': item.get('snippet', '')
    } for item in search_results])

    return all_results[:num_results]
