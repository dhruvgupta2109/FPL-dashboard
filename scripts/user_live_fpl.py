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

def fetch_user_team(entry_id, gw):
    url = f"https://fantasy.premierleague.com/api/entry/{entry_id}/event/{gw}/picks/"
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(url, context=context) as response:
        return json.loads(response.read())

def fetch_user_leagues(entry_id):
    url = f"https://fantasy.premierleague.com/api/entry/{entry_id}/"
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(url, context=context) as response:
        return json.loads(response.read())

def search_team_in_league(league_id, team_name):
    url = f"https://fantasy.premierleague.com/api/leagues-classic/{league_id}/standings/"
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(url, context=context) as response:
        data = json.loads(response.read())

    matches = []
    for e in data["standings"]["results"]:
        if team_name.lower() in e["entry_name"].lower():
            matches.append((e["entry"], e["entry_name"]))
    return matches

def main():
    bootstrap = load_bootstrap()
    gw = get_current_gameweek(bootstrap)

    if gw is None:
        print("No active Gameweek right now.")
        return

    players = build_player_map(bootstrap)
    teams = build_team_map(bootstrap)

    entry_id = input("Enter your FPL Manager ID (TID): ").strip()
    entry_id = int(entry_id) 
    manager_info = fetch_user_leagues(entry_id)  # returns basic info about the manager
    team_name = manager_info["player_first_name"] + " " + manager_info["player_last_name"]

    user_team = fetch_user_team(entry_id, gw)
    user_leagues = fetch_user_leagues(entry_id)

    user_picks = {}
    for p in user_team["picks"]:
        user_picks[p["element"]] = {
            "is_captain": p["is_captain"],
            "is_vice": p["is_vice_captain"],
            "multiplier": p["multiplier"]
        }

    print(f"\nLive FPL Tracker — Gameweek {gw}")
    print(f"Tracking team: {team_name} (Entry ID: {entry_id})")
    print("Press CTRL+C to stop\n")

    previous_stats = {}

    while True:
        os.system("clear")
        live_data = fetch_live_gameweek(gw)

        print(f"LIVE EVENTS — Gameweek {gw}")
        print("-" * 60)

        events = []
        user_total = 0

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

            multiplier = user_picks.get(pid, {}).get("multiplier", 1)
            live_points = current["points"] * multiplier

            if pid in user_picks:
                user_total += live_points

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

        print(f"\nYOUR LIVE SCORE: {user_total}")

        time.sleep(60)

if __name__ == "__main__":
    main()