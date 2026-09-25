def get_mmr_jetties(waterways_data):
    terminals = waterways_data["iwt_terminals"] if isinstance(waterways_data, dict) else waterways_data
    return [t for t in terminals if "NW-53" in t.get("waterway_name", "") and t.get("coordinate_verification") != "UNVERIFIED"]
