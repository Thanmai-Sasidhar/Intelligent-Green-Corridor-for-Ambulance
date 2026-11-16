# Intelligent Green Corridor System

A locally executable educational prototype of the proposed **Intelligent Green Corridor System for Real-Time Ambulance Traffic Management**.

It demonstrates:
- Ambulance journey creation
- Directed, weighted road graph
- Dijkstra route calculation
- Traffic-weight updates and road closures
- Route recalculation
- Intersection arrival-time estimates
- Simulated signal-priority requests with safety checks
- Journey/event logging in SQLite
- Browser dashboard

## Important scope and safety note

This is a **simulation/demo prototype**, not a live traffic-control product. The road network is illustrative. GPS, CCTV/YOLO, OpenStreetMap live ingestion, SUMO and real traffic-controller interfaces are not connected in this starter project. The priority endpoint only creates a simulated plan and does not change physical signals. Real deployment requires permission, validated controller interfaces, certified safety engineering, cybersecurity and traffic-authority approval.

## Requirements

- Python 3.10 or newer
- Internet is not required after dependencies are installed

## Run on macOS / Linux

```bash
cd intelligent_green_corridor
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Run on Windows

```powershell
cd intelligent_green_corridor
py -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

The SQLite database `green_corridor.db` is created automatically.

## How to demonstrate

1. Click **Create ambulance journey** (default A to H).
2. Inspect the route and ETA.
3. Change traffic on a road to HIGH, or block a road.
4. Click **Recalculate route** for the active journey.
5. Click **Request signal priority** to see the simulated safety-aware plan.
6. Click **Complete journey** to release simulated priority and log completion.

## API endpoints

- `GET /api/network`
- `GET /api/state`
- `POST /api/journey` JSON: `{"ambulance_id":"AMB-001","origin":"A","destination":"H"}`
- `POST /api/traffic` JSON: `{"edge":["B","D"],"traffic":"HIGH"}`
- `POST /api/block` JSON: `{"edge":["B","D"],"blocked":true}`
- `POST /api/recalculate/<journey_id>`
- `POST /api/priority/<journey_id>`
- `POST /api/complete/<journey_id>`

## Project structure

```text
intelligent_green_corridor/
├── app.py
├── config.py
├── routing.py
├── corridor.py
├── requirements.txt
├── README.md
├── templates/
│   └── index.html
└── static/
    ├── app.js
    └── style.css
```

## Mapping this prototype to the research proposal

| Proposal concept | Prototype implementation |
|---|---|
| Ambulance request | Journey creation form |
| GPS telemetry | Simulated node/location selection; GPS adapter is future work |
| Road network | Illustrative directed NetworkX graph |
| Dynamic road cost | Base travel time + traffic penalty |
| Route optimization | Dijkstra through NetworkX |
| Corridor planning | Ordered intersections and cumulative arrival estimates |
| Signal coordination | Simulated priority request and safety checklist |
| Monitoring | Dashboard and journey/event log |
| Evaluation | Exposed route, ETA and event data; add repeated SUMO experiments for formal results |

A* can be added as an alternative routing strategy after a validated admissible heuristic is selected. The current prototype deliberately uses Dijkstra to keep the route-cost behavior transparent.
