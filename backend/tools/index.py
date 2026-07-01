from langchain_core.tools import tool
import requests
import json

@tool
def get_jsonplaceholder_post(post_id: int) -> str:
    """Fetch a single post from JSONPlaceholder by its ID (1-100) and
    return the raw JSON as a string."""
    url = f"https://jsonplaceholder.typicode.com/posts/{post_id}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return json.dumps(resp.json(), indent=2)

