import networkx as nx

def build_network():
    """Small illustrative directed road graph. Coordinates are schematic, not geographic."""
    G = nx.DiGraph()
    coords = {
        "A": (0, 2), "B": (1, 3), "C": (1, 1), "D": (2, 2),
        "E": (3, 3), "F": (3, 1), "G": (4, 2), "H": (5, 2)
    }
    for node,(x,y) in coords.items():
        G.add_node(node,x=x,y=y)
    roads = [
        ("A","B",3),("A","C",4),("B","D",3),("C","D",2),
        ("B","E",4),("D","E",2),("D","F",3),("C","F",5),
        ("E","G",3),("F","G",2),("G","H",3),("E","H",7),
        ("B","A",3),("C","A",4),("D","B",3),("D","C",2),
        ("E","B",4),("E","D",2),("F","D",3),("F","C",5),
        ("G","E",3),("G","F",2),("H","G",3),("H","E",7)
    ]
    for u,v,w in roads:
        G.add_edge(u,v,base=float(w),weight=float(w),traffic="LOW",blocked=False)
    return G

def best_route(G, origin, destination):
    try:
        return nx.shortest_path(G, origin, destination, weight="weight", method="dijkstra")
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None

def estimate_route(G, route):
    return sum(G[u][v]["weight"] for u,v in zip(route,route[1:]))
