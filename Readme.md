# FPL Manager Dashboard

A Streamlit app for tracking your Fantasy Premier League team in real time.

This project connects to the official FPL API, loads your squad from a manager ID, and shows a modern dashboard with live points, fixtures, and gameweek trends.

Live app: https://fplmanager.streamlit.app

## Features

- Connect using your FPL manager ID.
- Live gameweek points for your active XI.
- Captain/vice-captain handling and multipliers.
- Current gameweek context (average and highest points).
- Visual pitch layout and bench overview.
- Fixtures page with match stats and player stat chips.
- Graphs page for:
	- your points vs gameweek average
	- overall rank trend
- Lightweight local data utilities for bootstrap and player processing.

## Tech Stack

- Python 3.10+
- Streamlit
- FPL public API (fantasy.premierleague.com)
- Chart.js (embedded in Streamlit components)

## Project Structure

```text
fpl/
├── live_dashboard.py           # App entry page (manager ID connect)
├── pages/
│   ├── home.py                 # Main dashboard view
│   ├── points.py               # Detailed points + pitch/chips view
│   ├── fixtures.py             # Fixture cards and match stats
│   ├── graphs.py               # Trend charts for points/rank
│   └── leagues.py              # Reserved/placeholder page
├── scripts/
│   ├── fetch_fpl_data.py       # Downloads bootstrap static data
│   ├── read_players.py         # Processes player value metrics
│   ├── live_fpl.py             # CLI live event tracker
│   └── user_live_fpl.py        # CLI tracker for a specific manager
├── data/
│   ├── raw/
│   │   └── bootstrap_static.json
│   └── processed/
│       └── players_processed.json
├── assets/
│   └── players/                # Player/team image assets
└── README.md
```

## Getting Started

### 1. Clone and enter the project

```bash
git clone <your-repo-url>
cd fpl
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install streamlit certifi
```

### 4. Run the app

```bash
streamlit run live_dashboard.py
```

Then open the local URL shown by Streamlit (usually http://localhost:8501).

## How To Find Your Manager ID

1. Open https://fantasy.premierleague.com.
2. Go to your team and open a gameweek points page.
3. In a URL like:
	 `https://fantasy.premierleague.com/entry/1637221/event/26`
	 the value `1637221` is your manager ID.

## Utility Scripts

Run these from the project root.

Fetch and store latest FPL bootstrap data:

```bash
python scripts/fetch_fpl_data.py
```

Generate processed player metrics (value, ppg, form):

```bash
python scripts/read_players.py
```

Track live GW events in terminal:

```bash
python scripts/live_fpl.py
```

Track live events for your own team:

```bash
python scripts/user_live_fpl.py
```

## Data Sources

This app uses public Fantasy Premier League API endpoints, including:

- `/api/bootstrap-static/`
- `/api/event/{gw}/live/`
- `/api/entry/{manager_id}/`
- `/api/entry/{manager_id}/history/`
- `/api/entry/{manager_id}/event/{gw}/picks/`
- `/api/fixtures/?event={gw}`

## Notes

- The app depends on live FPL API availability and may show temporary errors during outages/rate limits.
- Cached calls are used in key sections to reduce repeated requests.
- Some utility scripts expect `data/raw/bootstrap_static.json` to exist (run `fetch_fpl_data.py` first).

## License

No license file is currently included.
Add a `LICENSE` file if you plan to open-source or redistribute this project.