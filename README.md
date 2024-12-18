# Satellite Routing Simulator
A 2D simulator built with matplotlib and NetworkX to prototype satellite routing algorithms. The simulator finds paths between ground stations through a satellite network, with support for spare capacity zones.
Project Structure
```
satellite-routing/
├── snapshots/           # Network snapshot files
│   └── snapshot0.02s.txt
├── src/
│   └── satrouting/     # Main package
│       ├── init.py
│       ├── config.py   # Configuration constants
│       ├── graph_utils.py
│       ├── position_utils.py
│       ├── path_finding.py
│       ├── zone_utils.py
│       └── visualisation.py
├── scripts/
│   └── run_routing.py  # Main execution script
├── setup.py
├── requirements.txt
└── README.md
```

## Setup
Create and activate a virtual environment:

Create virtual environment
`python -m venv venv`
Activate virtual environment
On Linux/Mac:
`source venv/bin/activate`
On Windows:
`venv\Scripts\activate`

Install dependencies:
```
pip install -r requirements.txt
pip install -e .
```

Running the Simulator

Ensure you have a network snapshot file in the snapshots directory.
Run the main script:
```
python scripts/run_routing.py
```

## Network Structure
### Ground Stations
The network includes two ground stations:

- `Node -1`: Ground station in London (LDN)
- `Node -2`: Ground station in New York City (NYC)

### Spare Capacity Zones
The network includes designated spare capacity zones where alternative routing paths can be explored. These zones are defined by their corner nodes in the configuration.

### Features
- Finds shortest paths between ground stations
- Identifies paths through spare capacity zones
- Calculates path weights and ensures minimum weight requirements
- Visualizes network topology and paths
- Supports wrapped coordinate system for satellite positions

### Output
The simulator will:
1. Find and display regular shortest paths between ground stations
2. Find paths that go through spare capacity zones
3. Show path weights and statistics
4. Generate a visualization of the network with:
    - Ground stations (red)
    - Regular path nodes (blue)
    - Spare zone path nodes (green)
    - Other nodes (light blue)
    - Path edges with weights



## Dependencies
- NetworkX
- Matplotlib
- Python 3.8+