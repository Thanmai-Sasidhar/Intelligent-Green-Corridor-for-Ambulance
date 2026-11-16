let activeJourney=null, networkData=null, selectedRoute=[];
const $=id=>document.getElementById(id);
async function api(url,method="GET",body=null){
  const opts={method,headers:{"Content-Type":"application/json"}};
  if(body) opts.body=JSON.stringify(body);
  const r=await fetch(url,opts); const data=await r.json();
  if(!r.ok) throw new Error(data.error||"Request failed");
  return data;
}
function toast(msg){const el=$("toast");el.textContent=msg;el.classList.add("show");setTimeout(()=>el.classList.remove("show"),2600)}
function populate(){
  const nodes=networkData.nodes;
  ["origin","destination"].forEach(id=>{$(id).innerHTML=nodes.map(n=>`<option value="${n.id}">${n.id}</option>`).join("")});
  $("origin").value="A";$("destination").value="H";
  $("edgeSelect").innerHTML=networkData.edges.map(e=>`<option value="${e.from},${e.to}">${e.from} → ${e.to}</option>`).join("");
}
function draw(){
  if(!networkData)return;
  const svg=$("networkSvg"),pos={};
  networkData.nodes.forEach(n=>pos[n.id]={x:55+n.x*100,y:35+(3-n.y)*78});
  let html="";
  networkData.edges.forEach(e=>{
    const a=pos[e.from],b=pos[e.to],isRoute=selectedRoute.some((n,i)=>i<selectedRoute.length-1&&n===e.from&&selectedRoute[i+1]===e.to);
    html+=`<line x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}" class="road ${e.blocked?"blocked":""} ${isRoute?"route":""}"/>`;
  });
  networkData.nodes.forEach(n=>{const p=pos[n.id];html+=`<g class="node"><circle cx="${p.x}" cy="${p.y}" r="17"/><text x="${p.x}" y="${p.y}">${n.id}</text></g>`});
  svg.innerHTML=html;
}
async function refresh(){
  const [net,state]=await Promise.all([api("/api/network"),api("/api/state")]);
  networkData=net;draw();
  $("activeCount").textContent=state.journeys.length;
  $("events").innerHTML=state.events.length?state.events.map(e=>`<div class="event"><strong>${e.type}</strong><p>${e.message}</p><time>${new Date(e.created).toLocaleString()}</time></div>`).join(""):'<p class="muted">No events yet.</p>';
  $("journeys").innerHTML=state.journeys.length?state.journeys.map(j=>`<tr><td>${j.ambulance_id}</td><td>${j.route.join(" → ")}</td><td>${j.eta} min</td><td><span class="pill ${j.status==="COMPLETED"?"done":""}">${j.status}</span></td><td>#${j.id}</td></tr>`).join(""):'<tr><td colspan="5" class="muted">No journeys recorded.</td></tr>';
  if(activeJourney){
    const current=state.journeys.find(j=>j.id===activeJourney.id);
    if(current) activeJourney=current;
  }
}
function showJourney(data){
  activeJourney={id:data.journey_id,route:data.route,eta:data.eta_minutes};
  selectedRoute=data.route;draw();
  $("routeSummary").innerHTML=`<span>Recommended route: <b>${data.route.join(" → ")}</b></span><strong>${data.eta_minutes} min ETA</strong>`;
  $("corridor").classList.remove("empty");
  $("corridor").innerHTML=data.corridor.map(c=>`<div class="intersection"><strong>${c.intersection}</strong><span>Arrival +${c.estimated_arrival_minutes} min</span><small>${c.action}</small></div>`).join("");
  ["recalcBtn","priorityBtn","completeBtn"].forEach(id=>$(id).disabled=false);
}
async function create(){
  const data=await api("/api/journey","POST",{ambulance_id:$("ambulanceId").value||"AMB-001",origin:$("origin").value,destination:$("destination").value});
  showJourney(data);await refresh();toast("Journey created successfully");
}
async function updateTraffic(){
  const [u,v]=$("edgeSelect").value.split(",");
  const data=await api("/api/traffic","POST",{edge:[u,v],traffic:$("traffic").value});
  toast(data.message);await refresh();
}
async function toggleBlock(){
  const [u,v]=$("edgeSelect").value.split(",");
  const edge=networkData.edges.find(e=>e.from===u&&e.to===v);
  const data=await api("/api/block","POST",{edge:[u,v],blocked:!edge.blocked});
  toast(data.message);await refresh();
}
async function recalc(){
  const data=await api(`/api/recalculate/${activeJourney.id}`,"POST",{});
  showJourney({journey_id:activeJourney.id,...data});await refresh();toast("Route recalculated");
}
async function priority(){
  const data=await api(`/api/priority/${activeJourney.id}`,"POST",{});
  $("priorityResult").innerHTML=`<div class="priority-box"><b>${data.mode} PRIORITY PLAN</b><br>${data.message}<ul>${data.safety_checks.map(s=>`<li>${s}</li>`).join("")}</ul></div>`;
  await refresh();toast("Simulated priority plan generated");
}
async function complete(){
  const data=await api(`/api/complete/${activeJourney.id}`,"POST",{});
  toast(data.message);activeJourney=null;selectedRoute=[];draw();
  $("routeSummary").innerHTML="<span>Journey completed</span><strong>—</strong>";
  $("corridor").innerHTML="Journey completed. Create another journey to continue.";
  ["recalcBtn","priorityBtn","completeBtn"].forEach(id=>$(id).disabled=true);
  await refresh();
}
async function safe(fn){try{await fn()}catch(e){toast(e.message)}}
async function init(){
  networkData=await api("/api/network");populate();draw();await refresh();
  $("createBtn").onclick=()=>safe(create);
  $("trafficBtn").onclick=()=>safe(updateTraffic);
  $("blockBtn").onclick=()=>safe(toggleBlock);
  $("recalcBtn").onclick=()=>safe(recalc);
  $("priorityBtn").onclick=()=>safe(priority);
  $("completeBtn").onclick=()=>safe(complete);
  $("refreshBtn").onclick=()=>safe(refresh);
}
init().catch(e=>toast(e.message));
