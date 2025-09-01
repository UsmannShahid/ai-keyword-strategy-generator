import requests
from .env import get_serper_api_key, get_searchapi_api_key

SERPER_URL     = "https://google.serper.dev/search"      # Serper.dev
SEARCHAPI_URL  = "https://www.searchapi.io/api/v1/search" # SearchAPI.io

def fetch_serp_with_serper(keyword: str) -> dict:
    key = get_serper_api_key()
    if not key:
        return {"engine": "serper", "error": "Missing SERPER_API_KEY"}
    headers = {"X-API-KEY": key, "Content-Type": "application/json"}
    payload = {
        "q": keyword,
        # Optional targeting:
        # "gl": "us", "hl": "en", "location": "United States"
    }
    r = requests.post(SERPER_URL, json=payload, headers=headers, timeout=30)
    try:
        r.raise_for_status()
        return r.json()
    except requests.HTTPError as e:
        return {"engine": "serper", "error": f"HTTP {r.status_code}", "detail": str(e)}
    except requests.RequestException as e:
        return {"engine": "serper", "error": "network_error", "detail": str(e)}

def fetch_serp_with_searchapi(keyword: str) -> dict:
    key = get_searchapi_api_key()
    if not key:
        return {"engine": "searchapi", "error": "Missing SEARCHAPI_API_KEY"}
    params = {
        "engine": "google",
        "q": keyword,
        "api_key": key,
        # Optional targeting:
        # "gl": "us", "hl": "en", "location": "United States"
    }
    try:
        r = requests.get(SEARCHAPI_URL, params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.HTTPError as e:
        return {"engine": "searchapi", "error": f"HTTP {r.status_code}", "detail": str(e)}
    except requests.RequestException as e:
        return {"engine": "searchapi", "error": "network_error", "detail": str(e)}

def fetch_serp(keyword: str, provider: str) -> dict:
    # provider: "serper" for free, "searchapi" for paid
    if provider == "searchapi":
        return fetch_serp_with_searchapi(keyword)
    return fetch_serp_with_serper(keyword)
