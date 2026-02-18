import json
import os

RAW_FILE = "data/raw/bootstrap_static.json"
PROCESSED_FILE = "data/processed/players_processed.json"

with open(RAW_FILE, "r") as f:
    data = json.load(f)

players = data["elements"]
teams = {team["id"]: team["name"] for team in data["teams"]}

processed_players = []

for player in players:
    name = f"{player['first_name']} {player['second_name']}"
    team = teams[player["team"]]
    price = player["now_cost"] / 10      
    total_points = player["total_points"]
    minutes = player["minutes"]
    form = float(player["form"])
    
    ppg = (total_points / minutes * 90) if minutes > 0 else 0
    value = total_points / price if price > 0 else 0

    processed_players.append({
    "name": name,
    "team": team,
    "price": price,
    "total_points": total_points,
    "ppg": round(ppg, 2),
    "value": round(value, 2),
    "form": form,
    "element_type": player["element_type"]
})

processed_players.sort(key=lambda x: x["value"], reverse=True)

positions = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}

print(f"{'Name':25} {'Team':20} {'Pos':4} {'Price':6} {'Points':6} {'PPG':6} {'Value':6} {'Form':6}")
print("-" * 90)

for player in processed_players:
    pos = positions.get(player.get("element_type"), "UNK")
    short_name = (player['name'][:22] + "...") if len(player['name']) > 25 else player['name']
    print(f"{short_name:25} {player['team']:20} {pos:4} "
          f"{player['price']:<6.1f} {player['total_points']:<6} "
          f"{player['ppg']:<6.2f} {player['value']:<6.2f} {player['form']:<6.1f}")

os.makedirs("data/processed", exist_ok=True)
with open(PROCESSED_FILE, "w") as f:
    json.dump(processed_players, f, indent=2)

print(f"\nProcessed player data saved to {PROCESSED_FILE}")