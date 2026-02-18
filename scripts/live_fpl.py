import json
import time
import urllib.request
import os
import ssl
import certifi

BOOTSTRAP_FILE = "data/raw/bootstrap_static.json"

POSITIONS = {
    1: "GKP",
    2: "DEF",
    3: "MID",
    4: "FWD"
}

def load_bootstrap():
    with open(BOOTSTRAP_FILE, "r") as f:
        return json.load(f)

def get_current_gameweek(bootstrap):
    for event in bootstrap["events"]:
        if event["is_current"]:
            return event["id"]
    return None

def fetch_live_gameweek(gw):
    url = f"https://fantasy.premierleague.com/api/event/{gw}/live/"
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(url, context=context) as response:
        return json.loads(response.read())

def build_player_map(bootstrap):
    players = {}
    for p in bootstrap["elements"]:
        players[p["id"]] = {
            "name": f"{p['first_name']} {p['second_name']}",
            "team_id": p["team"],
            "price": p["now_cost"] / 10,
            "position": p["element_type"]
        }
    return players

def build_team_map(bootstrap):
    teams = {}
    for t in bootstrap["teams"]:
        teams[t["id"]] = t["short_name"]
    return teams

def main():
    bootstrap = load_bootstrap()
    gw = get_current_gameweek(bootstrap)

    if gw is None:
        print("No active Gameweek right now.")
        return

    players = build_player_map(bootstrap)
    teams = build_team_map(bootstrap)

    print(f"Live FPL Tracker — Gameweek {gw}")
    print("Press CTRL+C to stop")

    print("\nLIVE EVENTS")
    print("-" * 45)

    previous_stats = {}

    while True:
        live_data = fetch_live_gameweek(gw)
        events = []

        for p in live_data["elements"]:
            pid = p["id"]
            if pid not in players:
                continue

            s = p["stats"]

            current = {
                "minutes": s["minutes"],
                "goals": s["goals_scored"],
                "assists": s["assists"],
                "cs": s["clean_sheets"],
                "bonus": s["bonus"],
                "points": s["total_points"]
            }

            if pid in previous_stats:
                old = previous_stats[pid]
                name = players[pid]["name"]

                if current["goals"] > old["goals"]:
                    diff = current["goals"] - old["goals"]
                    events.append(f"⚽ GOAL — {name} (+{diff * 4})")

                if current["assists"] > old["assists"]:
                    diff = current["assists"] - old["assists"]
                    events.append(f"🅰️ ASSIST — {name} (+{diff * 3})")

                if current["cs"] > old["cs"]:
                    events.append(f"🧤 CLEAN SHEET — {name}")

                if current["bonus"] != old["bonus"]:
                    diff = current["bonus"] - old["bonus"]
                    sign = "+" if diff > 0 else ""
                    events.append(f"⭐ BONUS — {name} ({sign}{diff})")

            previous_stats[pid] = current

        if not events:
            print("No changes in the last minute.")
        else:
            for e in events:
                print(e)

        time.sleep(60)

if __name__ == "__main__":
    main()