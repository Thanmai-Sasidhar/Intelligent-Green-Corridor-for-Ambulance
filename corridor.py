def plan_corridor(graph, route, total_eta):
    """Create arrival estimates and a safe, simulated signal-priority plan."""
    if not route:
        return []
    elapsed=0.0
    result=[]
    for i,node in enumerate(route):
        if i>0:
            elapsed += graph[route[i-1]][node]["weight"]
        result.append({
            "intersection": node,
            "estimated_arrival_minutes": round(elapsed,2),
            "action": "PRIORITY_REQUEST" if i not in (0,len(route)-1) else "MONITOR",
            "safety": "Check conflicting phases, pedestrian clearance and intergreen intervals"
        })
    return result

def request_priority(route):
    # Demonstration only: this does not connect to real traffic controllers.
    return {
        "accepted": True,
        "mode": "SIMULATED",
        "message": f"Simulated priority plan generated for {len(route)} route nodes. No physical signal was changed.",
        "safety_checks": [
            "Conflicting movements must be cleared",
            "Minimum green and yellow intervals must be respected",
            "All-red clearance and pedestrian safety must be respected",
            "Controller acknowledgement is required in a real deployment"
        ]
    }
