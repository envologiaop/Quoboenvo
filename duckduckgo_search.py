import requests
import json

def search(queries: list):
    """
    Performs a search using the DuckDuckGo Instant Answer API.
    Does not require an API key for basic use.

    Args:
        queries: A list of search queries (strings). Only the first query will be used.

    Returns:
        A list of dictionaries, where each dictionary might contain
        'title', 'link', 'snippet', 'answer', or 'related_topics'.
        Returns an empty list if no results or if an error occurs.
    """
    all_results = []
    base_url = "https://api.duckduckgo.com/"

    if not queries:
        return []

    # DuckDuckGo Instant Answer API usually processes one query at a time
    query = queries[0] 
    
    params = {
        "q": query,
        "format": "json",
        "nohtml": "1", # Do not include HTML in the text and Abstract fields
        "skip_disambig": "1" # Attempt to skip disambiguation pages
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        # Extract relevant fields
        if data.get("Abstract"):
            all_results.append({
                "title": data.get("Heading", query),
                "link": data.get("AbstractURL"),
                "snippet": data.get("Abstract")
            })
        elif data.get("Answer"): # Direct answer
            all_results.append({
                "title": data.get("Heading", query),
                "link": data.get("AnswerType"), # Often a URL or type
                "snippet": data.get("Answer")
            })
        elif data.get("RelatedTopics"):
            # Often a list of dictionaries with Text, FirstURL, etc.
            for topic in data["RelatedTopics"]:
                if isinstance(topic, dict):
                    all_results.append({
                        "title": topic.get("Text"),
                        "link": topic.get("FirstURL"),
                        "snippet": topic.get("Text") # Use text as snippet for brevity
                    })
                elif "topics" in topic and isinstance(topic["topics"], list):
                    # Handle grouped topics if they appear
                    for sub_topic in topic["topics"]:
                        all_results.append({
                            "title": sub_topic.get("Text"),
                            "link": sub_topic.get("FirstURL"),
                            "snippet": sub_topic.get("Text")
                        })
        
        # Add a fallback if no specific fields were matched but data exists
        if not all_results and data.get("Results"):
             for result in data["Results"]:
                 all_results.append({
                     "title": result.get("Text"),
                     "link": result.get("FirstURL"),
                     "snippet": result.get("Text")
                 })


    except requests.exceptions.RequestException as e:
        print(f"Error during DuckDuckGo API request for query '{query}': {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response from DuckDuckGo API for query '{query}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred for query '{query}': {e}")

    return all_results

if __name__ == '__main__':
    # Example usage:
    # print("Testing a simple query:")
    # results = search(queries=["What is the capital of France?"])
    # for r in results:
    #     print(f"Title: {r.get('title')}\nSnippet: {r.get('snippet')}\nLink: {r.get('link')}\n---")

    # print("\nTesting a definition query:")
    # results = search(queries=["define API"])
    # for r in results:
    #     print(f"Title: {r.get('title')}\nSnippet: {r.get('snippet')}\nLink: {r.get('link')}\n---")
    
    # print("\nTesting a query with related topics:")
    # results = search(queries=["artificial intelligence"])
    # for r in results:
    #     print(f"Title: {r.get('title')}\nSnippet: {r.get('snippet')}\nLink: {r.get('link')}\n---")
    pass
