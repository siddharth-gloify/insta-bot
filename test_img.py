import requests

API_KEY = "4iyXClWlf2H72jf3ABKfGqDZ67bTzPV7F4Yztj0wGZ7OqCAmcPLtI96B"

url = "https://api.pexels.com/v1/search"

params = {
    "query": "dubai real estate",
    "per_page": 5
}

headers = {
    "Authorization": API_KEY
}

response = requests.get(url, headers=headers, params=params)
data = response.json()

for photo in data["photos"]:
    print(photo["src"]["large"])