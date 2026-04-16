import requests

API_KEY = "ef4a137c57f94a8889360d179f0f7897"

def fetch_dubai_realestate_news(page=1):
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": '"Dubai" AND ("real estate" OR "property" OR "villa" OR "apartment")',
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 10,
        "page": page,
        "apiKey": API_KEY
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    print("Status:", data.get("status"))
    print("Total results:", data.get("totalResults"))
    
    articles = data.get("articles", [])
    
    for article in articles:
        print("Title  :", article["title"])
        print("URL    :", article["url"])
        print("Image  :", article["urlToImage"])
        print("---")
    
    return articles

# ✅ THIS is what was missing
fetch_dubai_realestate_news(page=3)