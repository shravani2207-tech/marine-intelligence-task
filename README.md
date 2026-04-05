# Maritime Intelligence – Unified Data Layer
### Task 3 Deliverable | Shravani | Marine Intelligence Project

---

## Overview

This repository contains the **production-grade, normalized data layer** for the Marine Intelligence system. Raw geospatial datasets collected in Task 2 have been transformed into clean, schema-consistent, API-ready JSON files.

All datasets use **WGS84 (SRID 4326)** coordinate reference system.  
All files are **UTF-8 encoded, JSON arrays or objects** — directly ingestible by APIs, analytics engines, and validation layers.

---

## Folder Structure

```
maritime_data_layer/
├── data/
│   ├── ports.json               # 40 Indian ports (major + non-major)
│   ├── coastal_zones.json       # 10 Sagarmala coastal economic zones
│   ├── waterways.json           # 20 IWT terminals + 25 river monitoring stations
│   ├── environmental.json       # 15 environmental / ecological reference datasets
│   └── logistics.json           # 10 multimodal logistics parks (PM GatiShakti)
├── schemas/
│   └── schema_definitions.json  # Full schema spec for all datasets
├── review_packets/
│   └── REVIEW_PACKET.md         # Evaluation and engineering review packet
└── README.md                    # This file
```

---

## Dataset Summary

| File | Records | Domain | Source |
|---|---|---|---|
| `ports.json` | 40 | Maritime Infrastructure | shipmin.gov.in, sagarmala.gov.in, mmb.gov.in |
| `coastal_zones.json` | 10 | Coastal Economic Zones | sagarmala.gov.in |
| `waterways.json` | 20 + 25 | Inland Waterways | iwai.nic.in, indiawris.gov.in |
| `environmental.json` | 15 | Environmental / Ecology | bhuvan.nrsc.gov.in, unep.org, protectedplanet.net |
| `logistics.json` | 10 | Logistics Infrastructure | logistics.gov.in, nicdc.in |

---

## Schema Definitions

All schemas are documented in `/schemas/schema_definitions.json`.

### ports.json — record shape
```json
{
  "port_id":   1,
  "port_name": "Deendayal Port",
  "port_type": "Major Port",
  "state":     "",
  "latitude":  23.0333,
  "longitude": 70.2167,
  "source":    "http://shipmin.gov.in/",
  "notes":     "Major port in Gujarat handling bulk, container and petroleum cargo."
}
```

### coastal_zones.json — record shape
```json
{
  "zone_id":   1,
  "zone_name": "Kachchh Coastal Economic Zone",
  "state":     "Gujarat",
  "latitude":  23.7337,
  "longitude": 69.8597,
  "source":    "https://sagarmala.gov.in/coastal-economic-zones",
  "notes":     "Port-led industrial cluster focused on petrochemicals, cement, and heavy industries."
}
```

### waterways.json — record shape (two sub-arrays)
```json
{
  "iwt_terminals": [
    {
      "terminal_id":   1,
      "terminal_name": "Varanasi Multi-Modal Terminal",
      "waterway_name": "NW-1 (Ganga-Bhagirathi-Hooghly)",
      "terminal_type": "IWT Terminal",
      "latitude":  25.3176,
      "longitude": 82.9739,
      "source":    "https://iwai.nic.in",
      "notes":     "..."
    }
  ],
  "river_monitoring_stations": [
    {
      "station_id":          1,
      "station_name":        "Polavaram",
      "river_name":          "Godavari",
      "latitude":            17.2473,
      "longitude":           81.6466,
      "parameters_measured": ["pH", "DO", "BOD", "TDS"],
      "source":              "https://indiawris.gov.in/",
      "notes":               "monthly physio-chemical monitoring"
    }
  ]
}
```

### environmental.json — record shape
```json
{
  "dataset_id":    1,
  "dataset_name":  "Bhuvan Mangrove Forest Cover Map",
  "coverage_area": "India",
  "dataset_type":  "Spatial distribution and density of mangrove forests.",
  "source":        "https://bhuvan.nrsc.gov.in",
  "notes":         "Satellite-based map showing mangrove forest extent across India."
}
```

### logistics.json — record shape
```json
{
  "park_id":   1,
  "park_name": "Jogighopa",
  "state":     "Assam",
  "latitude":  26.24,
  "longitude": 90.9595,
  "source":    "https://logistics.gov.in/",
  "notes":     "Proposed MMLP in Assam to improve connectivity to Northeast India."
}
```

---

## How to Use

### Load a dataset (Python)
```python
import json

with open("data/ports.json") as f:
    ports = json.load(f)

# Filter major ports
major_ports = [p for p in ports if p["port_type"] == "Major Port"]
```

### Serve via REST API (Node.js / Express example)
```javascript
const ports = require('./data/ports.json');

app.get('/api/ports', (req, res) => {
  const { type } = req.query;
  const result = type ? ports.filter(p => p.port_type === type) : ports;
  res.json(result);
});
```

### Validate schema (Python + jsonschema)
```python
import json, jsonschema

schema = {
  "type": "object",
  "required": ["port_id", "port_name", "port_type", "latitude", "longitude", "source"],
  "properties": {
    "latitude":  {"type": "number", "minimum": -90,  "maximum": 90},
    "longitude": {"type": "number", "minimum": -180, "maximum": 180}
  }
}
with open("data/ports.json") as f:
    records = json.load(f)

for record in records:
    jsonschema.validate(record, schema)  # raises if invalid
```

---

## Integration Points

| System | Owner | Consumes |
|---|---|---|
| Validation Layer | Ankita | All JSON files in `/data/` — validates against schema definitions |
| Analytics Engine | Sanskar | All JSON files — runs spatial and domain analytics |
| Backend API | Soham | All JSON files — exposes via REST endpoints |

---

## Data Quality Notes

- **ports.json row 29** (`Kakinada Anchorage Port`): duplicate coordinates with row 28 (`Kakinada Seaport`). Flagged in `notes` field. Verify against source before production use.
- **environmental.json**: These are **reference/catalogue records** only — no lat/long fields because the datasets themselves are raster/vector layers obtained from external portals, not point features.
- `state` field in `ports.json` is left as empty string (`""`) — the source CSV did not include state per port. Can be enriched via reverse geocoding in a follow-up pass.

---

## Sources

- Ministry of Shipping: http://shipmin.gov.in/
- Sagarmala Programme: https://sagarmala.gov.in/
- Maharashtra Maritime Board: http://mmb.gov.in/
- IWAI (Inland Waterways): https://iwai.nic.in
- India-WRIS: https://indiawris.gov.in/
- NRSC Bhuvan: https://bhuvan.nrsc.gov.in
- PM GatiShakti Logistics: https://logistics.gov.in/
- Protected Planet (WDPA): https://www.protectedplanet.net
- UNEP: https://www.unep.org
