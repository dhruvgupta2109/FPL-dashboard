import urllib.request
import json
import os
import ssl
import certifi

FPL_API_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
OUTPUT_FILE = "data/raw/bootstrap_static.json"

def fetch_fpl_data():
    context = ssl.create_default_context(cafile=certifi.where())
    response = urllib.request.urlopen(FPL_API_URL, context=context)
    data = json.loads(response.read().decode())
    return data

def save_data(data):
    os.makedirs("data/raw", exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    data = fetch_fpl_data()
    save_data(data)
    print("FPL data saved to data/raw/bootstrap_static.json")