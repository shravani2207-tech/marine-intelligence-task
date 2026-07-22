import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

with open("spatial_truth_export.json") as f:
    data = json.load(f)

os.makedirs("screenshots", exist_ok=True)

# =====================================================================
# FIGURE 1: National River Network Map (all 10 rivers + infra + waterways)
# =====================================================================
fig, ax = plt.subplots(figsize=(12, 14))

river_colors = plt.cm.tab10.colors
for i, feature in enumerate(data["river_network"]["features"]):
    coords = feature["geometry"]["coordinates"]
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    ax.plot(xs, ys, linewidth=2, color=river_colors[i % 10], label=feature["properties"]["river_name"])

for feature in data.get("national_waterways", {}).get("features", []):
    coords = feature["geometry"]["coordinates"]
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    ax.plot(xs, ys, linewidth=1, linestyle="--", color="gray", alpha=0.6)

infra_types_seen = set()
type_markers = {
    "Dam": ("s", "red"), "Barrage": ("^", "orange"), "Port": ("o", "blue"),
    "Jetty": ("D", "green"), "Bridge": ("P", "purple"), "Inland Terminal": ("*", "brown"),
    "Lock": ("X", "black"), "Reservoir": ("h", "teal"), "Wetland": ("v", "darkgreen")
}
for feature in data["infrastructure_matrix"]["features"]:
    props = feature["properties"]
    coord = feature["geometry"]["coordinates"]
    itype = props["type"]
    marker, color = type_markers.get(itype, ("o", "gray"))
    ax.scatter(coord[0], coord[1], marker=marker, color=color, s=60, zorder=5)
    infra_types_seen.add(itype)

ax.set_title("National Multi-River Spatial Data Fabric\n10 River Basins + Infrastructure + Waterways", fontsize=14, fontweight="bold")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.legend(loc="upper left", fontsize=8, ncol=2)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("screenshots/01_national_river_network_map.png", dpi=150)
plt.close()
print("Saved: screenshots/01_national_river_network_map.png")

# =====================================================================
# FIGURE 2: Infrastructure Type Distribution (bar chart)
# =====================================================================
type_counts = {}
for feature in data["infrastructure_matrix"]["features"]:
    t = feature["properties"]["type"]
    type_counts[t] = type_counts.get(t, 0) + 1

fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(type_counts.keys(), type_counts.values(), color="steelblue")
ax.set_title("Infrastructure Node Distribution by Type", fontsize=14, fontweight="bold")
ax.set_ylabel("Count")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("screenshots/02_infrastructure_type_distribution.png", dpi=150)
plt.close()
print("Saved: screenshots/02_infrastructure_type_distribution.png")

# =====================================================================
# FIGURE 3: Flood Risk Overlay (bar chart, color coded)
# =====================================================================
risk_colors = {"HIGH": "red", "MEDIUM": "orange", "LOW": "green"}
rivers = [r["river"] for r in data["flood_risk_overlay"]]
risks = [r["flood_risk"] for r in data["flood_risk_overlay"]]
colors = [risk_colors[r] for r in risks]

fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(rivers, [1]*len(rivers), color=colors)
ax.set_title("Flood Risk Classification by River Basin", fontsize=14, fontweight="bold")
ax.set_xlabel("")
ax.set_xticks([])
legend_patches = [mpatches.Patch(color=c, label=l) for l, c in risk_colors.items()]
ax.legend(handles=legend_patches, loc="lower right")
plt.tight_layout()
plt.savefig("screenshots/03_flood_risk_overlay.png", dpi=150)
plt.close()
print("Saved: screenshots/03_flood_risk_overlay.png")

# =====================================================================
# FIGURE 4: Validation Results Summary (table-style image)
# =====================================================================
fig, ax = plt.subplots(figsize=(10, 8))
ax.axis("off")
val = data["validation_results"]
rows = [[k, str(v)] for k, v in val.items()]
table = ax.table(cellText=rows, colLabels=["Validation Check", "Result"], loc="center", cellLoc="left")
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 1.8)
ax.set_title("Dataset Validation Results Summary", fontsize=14, fontweight="bold", pad=20)
plt.tight_layout()
plt.savefig("screenshots/04_validation_results_summary.png", dpi=150)
plt.close()
print("Saved: screenshots/04_validation_results_summary.png")

# =====================================================================
# FIGURE 5: Convergence Status (table-style image)
# =====================================================================
fig, ax = plt.subplots(figsize=(10, 6))
ax.axis("off")
conv = data["convergence_status"]
rows = [[k, v.get("status", ""), v.get("reason", "")] for k, v in conv.items()]
table = ax.table(cellText=rows, colLabels=["Target System", "Status", "Reason"], loc="center", cellLoc="left")
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 1.8)
ax.set_title("GIS & TANTRA Convergence Status\n(Adapter stubs ready, live endpoints pending)", fontsize=13, fontweight="bold", pad=20)
plt.tight_layout()
plt.savefig("screenshots/05_convergence_status.png", dpi=150)
plt.close()
print("Saved: screenshots/05_convergence_status.png")

print("\nAll 5 proof visuals generated in screenshots/ directory.")
