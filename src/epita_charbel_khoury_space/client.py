from datetime import date, timedelta
import requests
from epita_charbel_khoury_space.config import config

def fetch_live_data() -> dict:
    config.validate()
    url = "https://api.nasa.gov/planetary/apod"
    headers = {"X-Api-Key": config.api_key}
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code == 500:
        # today's picture is sometimes not published yet, use yesterday
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        resp = requests.get(url, headers=headers, params={"date": yesterday}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return {
        "status": "LIVE_SUCCESS",
        "date": data.get("date"),
        "title": data.get("title"),
        "media_type": data.get("media_type"),
        "url": data.get("url"),
    }
