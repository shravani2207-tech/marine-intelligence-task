import json
from datetime import datetime, timezone

SCHEMA_VERSION = "1.0.0"
SPATIAL_REFERENCE = "EPSG:4326"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def load_json(path):
    with open(path, encoding="utf-8-sig") as f:
        data = json.load(f)
    if isinstance(data, dict) and "value" in data and "Count" in data:
        return data["value"]
    return data

def envelope(entity_id, entity_type, name, geometry, source, authority, properties, confidence, known_unknowns):
    return {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "name": name,
        "geometry": geometry,
        "spatial_reference": SPATIAL_REFERENCE,
        "source": source,
        "authority": authority,
        "timestamp": NOW,
        "schema_version": SCHEMA_VERSION,
        "provenance": {
            "origin": "marine-intelligence-task data layer",
            "added_by": "Shravani - BHIV Bharat Mala MMR extension",
            "method": "manual entry from cited public source"
        },
        "confidence": confidence,
        "known_unknowns": known_unknowns,
        "properties": properties
    }

def point_geom(lon, lat):
    return {"type": "Point", "coordinates": [lon, lat]}

def linestring_geom(coords):
    return {"type": "LineString", "coordinates": [[c[0], c[1]] for c in coords]}

def build_entities():
    waterways = load_json("waterways.json")
    ports = load_json("ports.json")
    environmental = load_json("environmental.json")
    logistics = load_json("logistics.json")

    entities = []

    # --- NW-53 waterway itself (new spatial entity, was missing before) ---
    nw53_coords = [(73.1305, 19.2403), (72.9944, 19.2515), (72.9899, 19.2411),
                   (72.9713, 19.1943), (72.95, 19.05), (72.84, 18.9474)]
    entities.append(envelope(
        entity_id="WATERWAY_NW53",
        entity_type="Waterway",
        name="NW-53 (Kalyan-Thane-Mumbai Waterway / Ulhas River)",
        geometry=linestring_geom(nw53_coords),
        source="https://iwai.nic.in",
        authority="Inland Waterways Authority of India (IWAI)",
        properties={"designation": "National Waterway 53"},
        confidence="MEDIUM",
        known_unknowns=["Route coordinates are representative/approximate, not surveyed centerline."]
    ))

    # --- IWT terminals on NW-53 ---
    terminals = waterways["iwt_terminals"] if isinstance(waterways, dict) else waterways
    for t in terminals:
        if "NW-53" in t.get("waterway_name", ""):
            entities.append(envelope(
                entity_id=f"TERMINAL_{t['terminal_id']}",
                entity_type=t.get("terminal_type", "IWT Terminal"),
                name=t["terminal_name"],
                geometry=point_geom(t["longitude"], t["latitude"]),
                source=t.get("source"),
                authority="Inland Waterways Authority of India (IWAI)",
                properties={"waterway_name": t.get("waterway_name")},
                confidence="HIGH",
                known_unknowns=[]
            ))

    # --- MMR ports ---
    for p in ports:
        if p["port_name"] in {"Mumbai Port", "Jawaharlal Nehru Port", "Rewas Port"}:
            entities.append(envelope(
                entity_id=f"PORT_{p['port_id']}",
                entity_type=p.get("port_type", "Port"),
                name=p["port_name"],
                geometry=point_geom(p["longitude"], p["latitude"]),
                source=p.get("source"),
                authority="Ministry of Shipping / Maharashtra Maritime Board",
                properties={"state": p.get("state", "")},
                confidence="HIGH",
                known_unknowns=[]
            ))

    # --- Thane Creek environmental constraint ---
    for e in environmental:
        if "Thane Creek" in e.get("dataset_name", ""):
            entities.append(envelope(
                entity_id=f"ENV_{e['dataset_id']}",
                entity_type="Environmental Constraint",
                name=e["dataset_name"],
                geometry=point_geom(72.97, 19.10),
                source=e.get("source"),
                authority="Ramsar Convention Secretariat",
                properties={"coverage_area": e.get("coverage_area")},
                confidence="LOW",
                known_unknowns=[
                    "Geometry is a representative centroid point only -- actual Ramsar site boundary polygon not yet sourced/digitized."
                ]
            ))

    # --- Bhiwandi logistics cluster ---
    for l in logistics:
        if "Bhiwandi" in l.get("park_name", ""):
            entities.append(envelope(
                entity_id=f"LOGISTICS_{l['park_id']}",
                entity_type="Logistics Cluster (Private, Non-MMLP)",
                name=l["park_name"],
                geometry=point_geom(l["longitude"], l["latitude"]),
                source=l.get("source"),
                authority="UNCONFIRMED - no official government authority found",
                properties={"state": l.get("state", "")},
                confidence="LOW",
                known_unknowns=[
                    "No confirmed official PM GatiShakti MMLP designation exists for Bhiwandi.",
                    "Coordinates are town-level, not park-specific.",
                    "Represents a cluster of private developer parks (ESR, Mapletree, IndoSpace), not a single facility."
                ]
            ))

    return entities

if __name__ == "__main__":
    entities = build_entities()
    output = {
        "contract_version": SCHEMA_VERSION,
        "generated_at": NOW,
        "entity_count": len(entities),
        "entities": entities
    }
    with open("mmr_canonical_envelope.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"Canonical envelope generated: {len(entities)} entities -> mmr_canonical_envelope.json")
