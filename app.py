from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from routing import build_network, best_route, estimate_route
from corridor import plan_corridor, request_priority
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

class Journey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ambulance_id = db.Column(db.String(40), nullable=False)
    origin = db.Column(db.String(40), nullable=False)
    destination = db.Column(db.String(40), nullable=False)
    route = db.Column(db.Text, nullable=False)
    eta_minutes = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    journey_id = db.Column(db.Integer, db.ForeignKey("journey.id"))
    event_type = db.Column(db.String(60), nullable=False)
    message = db.Column(db.String(300), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

network = build_network()

def log_event(journey_id, event_type, message):
    db.session.add(Event(journey_id=journey_id, event_type=event_type, message=message))
    db.session.commit()

@app.route("/")
def index():
    return render_template("index.html")

@app.get("/api/network")
def api_network():
    nodes = [{"id": n, "x": network.nodes[n]["x"], "y": network.nodes[n]["y"]} for n in network.nodes]
    edges = [{"from": u, "to": v, "minutes": d["weight"], "base": d["base"], "blocked": d["blocked"], "traffic": d["traffic"]} for u,v,d in network.edges(data=True)]
    return jsonify(nodes=nodes, edges=edges)

@app.get("/api/state")
def api_state():
    journeys = Journey.query.order_by(Journey.id.desc()).limit(10).all()
    events = Event.query.order_by(Event.id.desc()).limit(15).all()
    return jsonify(
        journeys=[{"id": j.id, "ambulance_id": j.ambulance_id, "origin": j.origin, "destination": j.destination,
                   "route": j.route.split(","), "eta": round(j.eta_minutes,2), "status": j.status,
                   "created": j.created_at.isoformat()} for j in journeys],
        events=[{"type": e.event_type, "message": e.message, "created": e.created_at.isoformat()} for e in events]
    )

@app.post("/api/journey")
def create_journey():
    data = request.get_json(force=True)
    origin = data.get("origin", "A")
    destination = data.get("destination", "H")
    ambulance_id = data.get("ambulance_id", "AMB-001")
    if origin not in network or destination not in network:
        return jsonify(error="Unknown origin or destination node."), 400
    route = best_route(network, origin, destination)
    if not route:
        return jsonify(error="No feasible route is currently available."), 409
    eta = estimate_route(network, route)
    j = Journey(ambulance_id=ambulance_id, origin=origin, destination=destination,
                route=",".join(route), eta_minutes=eta)
    db.session.add(j)
    db.session.commit()
    log_event(j.id, "JOURNEY_CREATED", f"{ambulance_id}: route {' → '.join(route)}; estimated {eta:.1f} min")
    plan = plan_corridor(network, route, eta)
    return jsonify(journey_id=j.id, route=route, eta_minutes=round(eta,2), corridor=plan)

@app.post("/api/traffic")
def update_traffic():
    data = request.get_json(force=True)
    edge = data.get("edge", ["B","D"])
    u,v = edge[0],edge[1]
    if not network.has_edge(u,v):
        return jsonify(error="Unknown directed road segment."), 400
    traffic = data.get("traffic", "HIGH")
    penalty = {"LOW":0.0, "MEDIUM":2.0, "HIGH":5.0}.get(traffic)
    if penalty is None:
        return jsonify(error="traffic must be LOW, MEDIUM or HIGH"), 400
    d=network[u][v]
    d["traffic"]=traffic
    d["weight"]=d["base"]+penalty+(10000 if d["blocked"] else 0)
    return jsonify(message=f"Updated {u} → {v} traffic to {traffic}", new_weight=d["weight"])

@app.post("/api/block")
def block_road():
    data=request.get_json(force=True)
    u,v=data.get("edge",["B","D"])
    if not network.has_edge(u,v):
        return jsonify(error="Unknown directed road segment."),400
    blocked=bool(data.get("blocked",True))
    d=network[u][v]
    d["blocked"]=blocked
    d["weight"]=d["base"]+{"LOW":0,"MEDIUM":2,"HIGH":5}[d["traffic"]]+(10000 if blocked else 0)
    return jsonify(message=f"{u} → {v} {'blocked' if blocked else 'reopened'}",weight=d["weight"])

@app.post("/api/recalculate/<int:journey_id>")
def recalculate(journey_id):
    j=Journey.query.get_or_404(journey_id)
    route=best_route(network,j.origin,j.destination)
    if not route:
        return jsonify(error="No feasible route."),409
    old=j.route
    j.route=",".join(route)
    j.eta_minutes=estimate_route(network,route)
    db.session.commit()
    log_event(j.id,"REROUTED",f"Route changed from {old} to {j.route}")
    return jsonify(route=route,eta_minutes=round(j.eta_minutes,2),corridor=plan_corridor(network,route,j.eta_minutes))

@app.post("/api/priority/<int:journey_id>")
def priority(journey_id):
    j=Journey.query.get_or_404(journey_id)
    route=j.route.split(",")
    result=request_priority(route)
    log_event(j.id,"SIGNAL_PRIORITY",result["message"])
    return jsonify(result)

@app.post("/api/complete/<int:journey_id>")
def complete(journey_id):
    j=Journey.query.get_or_404(journey_id)
    j.status="COMPLETED"
    db.session.commit()
    log_event(j.id,"JOURNEY_COMPLETED","Journey completed; simulated priority released and normal plan restored.")
    return jsonify(message="Journey completed. Priority released; normal signal plan restored.")

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
