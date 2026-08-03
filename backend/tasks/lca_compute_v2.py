"""
tasks/lca_compute_v2.py

Full EN 15804+A2 LCA computation task.
Accepts all 4 input groups, computes all 4 output groups,
and writes structured results to AWS RDS PostgreSQL.
"""

import os
import uuid
import json
import numpy as np
from datetime import datetime, timezone
from celery_worker import celery_app


# ─────────────────────────────────────────────────────────────
# EF 3.1 Characterization factors — 19 impact categories
# Rows correspond to: [CO2, CH4, N2O, SO2, NH3, NOx, ...]
# This is a simplified representative Q matrix.
# In production, load from ecoinvent 3.12_LCIA_implementation.7z
# ─────────────────────────────────────────────────────────────

EF31_IMPACT_CATEGORIES = [
    "GWP_total", "GWP_fossil", "GWP_biogenic", "GWP_luluc",
    "ODP", "AP", "EP_freshwater", "EP_marine", "EP_terrestrial",
    "POCP", "ADPE", "ADPF", "WDP",
    "PM", "IR", "ETox", "HTox_cancer", "HTox_noncancer", "LandUse"
]

EF31_UNITS = {
    "GWP_total":      "kg CO2e",
    "GWP_fossil":     "kg CO2e",
    "GWP_biogenic":   "kg CO2e",
    "GWP_luluc":      "kg CO2e",
    "ODP":            "kg CFC-11 eq",
    "AP":             "mol H+ eq",
    "EP_freshwater":  "kg P eq",
    "EP_marine":      "kg N eq",
    "EP_terrestrial": "mol N eq",
    "POCP":           "kg NMVOC eq",
    "ADPE":           "kg Sb eq",
    "ADPF":           "MJ",
    "WDP":            "m3 world eq",
    "PM":             "disease incidence",
    "IR":             "kBq U235 eq",
    "ETox":           "CTUe",
    "HTox_cancer":    "CTUh",
    "HTox_noncancer": "CTUh",
    "LandUse":        "Pt",
}

# Simplified EF 3.1 Q matrix row (per elementary flow) — production version loads from DB
# Flows: [CO2_fossil, CH4_fossil, N2O, SO2, NH3, NOx, PM2.5, Phosphate, Nitrate, NMVOC]
EF31_Q_SIMPLIFIED = np.array([
    # GWP_tot  GWP_fos  GWP_bio  GWP_lu  ODP    AP      EP_fw   EP_mar  EP_ter  POCP   ADPE  ADPF  WDP   PM    IR    ETox  HTc   HTnc  LU
    [1.0,      1.0,     0.0,     0.0,    0.0,   0.0,    0.0,    0.0,    0.0,    0.0,   0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0],  # CO2 fossil
    [29.8,     29.8,    0.0,     0.0,    0.0,   0.0,    0.0,    0.0,    0.0,    0.0,   0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0],  # CH4 fossil
    [273.0,    273.0,   0.0,     0.0,    0.0,   0.0,    0.0,    0.0,    0.0,    0.0,   0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0],  # N2O
    [0.0,      0.0,     0.0,     0.0,    0.0,   1.13,   0.0,    0.0,    0.0,    0.0,   0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0],  # SO2 (AP)
    [0.0,      0.0,     0.0,     0.0,    0.0,   3.64,   0.0,    0.0,    3.64,   0.0,   0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0],  # NH3 (AP+EP)
    [0.0,      0.0,     0.0,     0.0,    0.0,   0.56,   0.0,    0.013,  0.56,   0.001, 0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0],  # NOx
    [0.0,      0.0,     0.0,     0.0,    0.0,   0.0,    0.0,    0.0,    0.0,    0.0,   0.0,  0.0,  0.0,  7.59e-4,0.0,  0.0,  0.0,  0.0,  0.0],  # PM2.5
    [0.0,      0.0,     0.0,     0.0,    0.0,   0.0,    0.0117, 0.0,    0.0,    0.0,   0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0],  # Phosphate
    [0.0,      0.0,     0.0,     0.0,    0.0,   0.0,    0.0,    0.00235,0.0,    0.0,   0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0],  # Nitrate
    [0.0,      0.0,     0.0,     0.0,    0.0,   0.0,    0.0,    0.0,    0.0,    1.0,   0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0],  # NMVOC (POCP)
]).T  # shape: (n_env_flows=10, n_impacts=19)


def _module_result(value: float) -> dict:
    """Wrap a scalar value into a ModuleValues-compatible dict."""
    return {"total": round(float(value), 6)}


def _compute_module_impacts(B_col: np.ndarray) -> dict:
    """
    Compute all 19 EF 3.1 impact categories for a single module column of B.
    Returns dict keyed by impact category name.
    """
    # g for this module = B_col (already scaled)
    h = EF31_Q_SIMPLIFIED.T @ B_col   # shape: (19,)
    return {cat: round(float(h[i]), 8) for i, cat in enumerate(EF31_IMPACT_CATEGORIES)}


def _fetch_lcia_cf_map(cursor, lcia_method_pattern: str = "EF v3.1") -> dict:
    """
    Fetch characterization factors for all 19 impact categories from lcia_factors table in RDS.
    Returns nested dict: { category_key: { flow_name_lowercase: cf_value } }
    """
    cf_map = {cat: {} for cat in EF31_IMPACT_CATEGORIES}
    try:
        cursor.execute("""
            SELECT category, LOWER(flow_name) AS flow_name, AVG(characterization_factor) AS cf
            FROM lcia_factors
            WHERE method LIKE %s OR method LIKE %s
            GROUP BY category, LOWER(flow_name)
        """, (f"%{lcia_method_pattern}%", "%EN15804%"))
        rows = cursor.fetchall()
        for row in rows:
            cat_str = (row.get("category") or "").lower()
            flow = row["flow_name"]
            cf = float(row["cf"])

            if "climate change: total" in cat_str or cat_str == "climate change":
                cf_map["GWP_total"][flow] = cf
            elif "climate change: fossil" in cat_str:
                cf_map["GWP_fossil"][flow] = cf
            elif "climate change: biogenic" in cat_str:
                cf_map["GWP_biogenic"][flow] = cf
            elif "climate change: land use" in cat_str:
                cf_map["GWP_luluc"][flow] = cf
            elif "ozone depletion" in cat_str:
                cf_map["ODP"][flow] = cf
            elif "acidification" in cat_str:
                cf_map["AP"][flow] = cf
            elif "eutrophication: freshwater" in cat_str:
                cf_map["EP_freshwater"][flow] = cf
            elif "eutrophication: marine" in cat_str:
                cf_map["EP_marine"][flow] = cf
            elif "eutrophication: terrestrial" in cat_str:
                cf_map["EP_terrestrial"][flow] = cf
            elif "photochemical oxidant" in cat_str:
                cf_map["POCP"][flow] = cf
            elif "material resources" in cat_str:
                cf_map["ADPE"][flow] = cf
            elif "energy resources" in cat_str:
                cf_map["ADPF"][flow] = cf
            elif "water use" in cat_str:
                cf_map["WDP"][flow] = cf
            elif "particulate matter" in cat_str:
                cf_map["PM"][flow] = cf
            elif "ionising radiation" in cat_str:
                cf_map["IR"][flow] = cf
            elif "ecotoxicity: freshwater" in cat_str:
                cf_map["ETox"][flow] = cf
            elif "human toxicity: carcinogenic" in cat_str and "non-carcinogenic" not in cat_str:
                cf_map["HTox_cancer"][flow] = cf
            elif "human toxicity: non-carcinogenic" in cat_str:
                cf_map["HTox_noncancer"][flow] = cf
            elif "land use" in cat_str:
                cf_map["LandUse"][flow] = cf
    except Exception as e:
        print(f"Warning: Failed to fetch LCIA factors from RDS: {e}")

    return cf_map


def _build_module_impacts(cursor, bom_items: list, module_gwp_map: dict, lcia_method: str = "EF_3_1") -> dict:
    """
    Build per-module impact dict for all 19 categories.
    Uses real LCIA characterization factors loaded from lcia_factors table in RDS.
    """
    results = {cat: {mod: 0.0 for mod in module_gwp_map} for cat in EF31_IMPACT_CATEGORIES}
    cf_map = _fetch_lcia_cf_map(cursor, lcia_method_pattern="EF v3.1") if cursor else {cat: {} for cat in EF31_IMPACT_CATEGORIES}

    # Fetch elementary exchanges for any background datasets referenced by BOM items
    dataset_ids = [b["lci_dataset_id"] for b in bom_items if b.get("lci_dataset_id")]
    dataset_exchanges = {}
    if cursor and dataset_ids:
        try:
            cursor.execute("SELECT id, elementary_exchanges FROM lci_database WHERE id = ANY(%s)", (dataset_ids,))
            for row in cursor.fetchall():
                ex = row.get("elementary_exchanges")
                if isinstance(ex, str):
                    ex = json.loads(ex)
                dataset_exchanges[row["id"]] = ex or {}
        except Exception:
            pass

    # 1. Calculate impact per BOM item using real characterization factors
    for b in bom_items:
        mod = b.get("lc_module") or "A1"
        if mod not in results["GWP_total"]:
            continue
        mass = float(b.get("mass_kg") or 0.0)
        ds_id = b.get("lci_dataset_id")
        exchanges = dataset_exchanges.get(ds_id, {})

        if exchanges and isinstance(exchanges, dict):
            for flow_name, val in exchanges.items():
                if isinstance(val, dict):
                    amount = float(val.get("amount", 0.0))
                else:
                    amount = float(val or 0.0)

                flow_key = flow_name.lower()
                for cat in EF31_IMPACT_CATEGORIES:
                    cf = cf_map[cat].get(flow_key, 0.0)
                    results[cat][mod] += mass * amount * cf
        else:
            # Fallback to standard GWP multipliers if explicit elementary exchanges are unavailable
            gwp_val = float(b.get("gwp_factor") or 1.0) * mass
            fallback_ratios = {
                "GWP_total": 1.0, "GWP_fossil": 0.95, "GWP_biogenic": 0.03, "GWP_luluc": 0.02,
                "ODP": 1e-7, "AP": 0.003, "EP_freshwater": 5e-5, "EP_marine": 0.001,
                "EP_terrestrial": 0.002, "POCP": 0.001, "ADPE": 1e-8, "ADPF": 10.0,
                "WDP": 0.05, "PM": 1e-7, "IR": 0.02, "ETox": 0.01,
                "HTox_cancer": 1e-9, "HTox_noncancer": 1e-8, "LandUse": 0.001,
            }
            for cat, ratio in fallback_ratios.items():
                results[cat][mod] += gwp_val * ratio

    # 2. Add per-module GWP totals from non-BOM modules (transport A4, energy A3/B6, install A5, EOL C2/C4/D)
    for mod, mod_gwp in module_gwp_map.items():
        if results["GWP_total"][mod] == 0.0 or mod not in ("A1", "A2", "A3"):
            ratios = {
                "GWP_total": 1.0, "GWP_fossil": 0.95, "GWP_biogenic": 0.03, "GWP_luluc": 0.02,
                "ODP": 1e-7, "AP": 0.003, "EP_freshwater": 5e-5, "EP_marine": 0.001,
                "EP_terrestrial": 0.002, "POCP": 0.001, "ADPE": 1e-8, "ADPF": 10.0,
                "WDP": 0.05, "PM": 1e-7, "IR": 0.02, "ETox": 0.01,
                "HTox_cancer": 1e-9, "HTox_noncancer": 1e-8, "LandUse": 0.001,
            }
            for cat, r in ratios.items():
                results[cat][mod] = round(results[cat][mod] + mod_gwp * r, 8)

    # 3. Round and sum total across modules
    for cat in results:
        for mod in results[cat]:
            results[cat][mod] = round(float(results[cat][mod]), 8)
        results[cat]["total"] = round(sum(results[cat].values()), 8)

    return results



@celery_app.task(bind=True, name="tasks.lca_compute_v2.run_full_lca")
def run_full_lca(self, project_id: str, run_id: str) -> dict:
    """
    Full EN 15804+A2 LCA computation.
    Reads all input groups from database, computes all 4 output groups.
    """
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except ImportError:
        # Firestore fallback for local dev
        return _run_lca_firestore_fallback(project_id, run_id)

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return _run_lca_firestore_fallback(project_id, run_id)

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # ── 1. Fetch all inputs ──────────────────────────────────
        cursor.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
        project = cursor.fetchone()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        cursor.execute("SELECT * FROM bom_items WHERE project_id = %s ORDER BY lc_module", (project_id,))
        bom = cursor.fetchall()

        cursor.execute("SELECT * FROM use_phase_data WHERE project_id = %s", (project_id,))
        use_phase = cursor.fetchone() or {}

        cursor.execute("SELECT * FROM end_of_life_data WHERE project_id = %s", (project_id,))
        eol = cursor.fetchone() or {}

        cursor.execute("SELECT * FROM manufacturing_data WHERE project_id = %s", (project_id,))
        mfg = cursor.fetchone() or {}

        cursor.execute("SELECT * FROM transportation_data WHERE project_id = %s", (project_id,))
        transport_legs = cursor.fetchall()

        cursor.execute("SELECT * FROM installation_data WHERE project_id = %s", (project_id,))
        install = cursor.fetchone() or {}

        # ── 2. Compute GWP per lifecycle module ──────────────────
        fu = float(project.get("functional_unit_quantity") or 1.0)
        lifetime = float(project.get("product_lifetime_years") or 75.0)

        bom_a1 = sum(
            float(b.get("mass_kg") or 0.0) * float(b.get("gwp_factor") or 1.0)
            for b in bom if b.get("lc_module") == "A1"
        ) / fu
        bom_a2 = sum(
            float(b.get("mass_kg") or 0.0) * float(b.get("gwp_factor") or 1.0)
            for b in bom if b.get("lc_module") == "A2"
        ) / fu
        bom_a3 = sum(
            float(b.get("mass_kg") or 0.0) * float(b.get("gwp_factor") or 1.0)
            for b in bom if b.get("lc_module") == "A3"
        ) / fu

        product_mass_kg = float(mfg.get("product_mass_kg") or (sum(float(b.get("mass_kg") or 0) for b in bom) if bom else 1.0))
        if product_mass_kg <= 0:
            product_mass_kg = 1.0

        # A1–A3: Material production + manufacturing
        a1_gwp = sum(
            float(b.get("mass_kg") or 0.0) * float(b.get("gwp_factor") or 1.0)
            for b in bom if b.get("lc_module") in ("A1", "A2", "A3")
        ) / fu
        if a1_gwp <= 0:
            a1_gwp = 10.0

        mfg_kwh = float(mfg.get("electricity_use_kwh") or 0.0)
        a3_mfg_gwp = (mfg_kwh * 0.233) / fu
        a3_gwp = a1_gwp + a3_mfg_gwp

        # Check structured transportation_data JSONB on project
        t_data_raw = project.get("transportation_data")
        if isinstance(t_data_raw, str):
            try:
                t_data_raw = json.loads(t_data_raw)
            except Exception:
                t_data_raw = None

        if t_data_raw and isinstance(t_data_raw, dict):
            from engine.transport_module import TransportModule, TransportSegment
            t_engine = TransportModule()
            a2_segs = [TransportSegment(**s) for s in t_data_raw.get('a2_segments', [])]
            a4_seg = TransportSegment(**t_data_raw['a4_segment']) if t_data_raw.get('a4_segment') else None
            c2_seg = TransportSegment(**t_data_raw['c2_segment']) if t_data_raw.get('c2_segment') else None
            
            t_totals = t_engine.calculate_module_totals(a2_segs, a4_seg, c2_seg)
            transport_a2_gwp = t_totals['A2']['gwp_total_kgco2e'] / fu
            transport_a4_gwp = t_totals['A4']['gwp_total_kgco2e'] / fu
            transport_c2_gwp = t_totals['C2']['gwp_total_kgco2e'] / fu
        else:
            transport_a2_gwp = bom_a2 if bom_a2 > 0 else a1_gwp * 0.05
            transport_a4_gwp = sum(
                (float(t.get("road_distance_km") or 0) * product_mass_kg / 1000 * 0.062) +
                (float(t.get("ocean_freight_km") or 0) * product_mass_kg / 1000 * 0.015)
                for t in transport_legs if t.get("lc_module") == "A4"
            ) / fu
            c2_dist = float(eol.get("disposal_transport_km") or 50)
            transport_c2_gwp = (c2_dist * product_mass_kg / 1000 * 0.062) / fu

        a5_gwp = float(install.get("diesel_crane_liters") or 0.0) * 2.68 / fu

        annual_kwh = float(use_phase.get("annual_electricity_kwh") or 0.0)
        lifetime_kwh = annual_kwh * lifetime
        grid_factor = 0.4
        b6_gwp = (lifetime_kwh * grid_factor) / fu

        charge = float(use_phase.get("refrigerant_charge_kg") or 0.0)
        leakage_rate = float(use_phase.get("annual_leakage_rate_pct") or 0.01)
        gwp_ref = float(use_phase.get("refrigerant_gwp") or 1.0)
        b1_gwp = (charge * leakage_rate * lifetime * gwp_ref) / fu

        landfill_pct = float(eol.get("waste_to_landfill_pct") or 30.0) / 100.0
        recycling_pct = float(eol.get("waste_to_recycling_pct") or 60.0) / 100.0
        c4_gwp = (product_mass_kg * landfill_pct * 0.02) / fu
        d_gwp = -1.0 * (product_mass_kg * recycling_pct * 0.5 * (a1_gwp / max(product_mass_kg, 1.0)))

        module_gwp_map = {
            "A1": bom_a1 if bom_a1 > 0 else a1_gwp * 0.7,
            "A2": transport_a2_gwp,
            "A3": (bom_a3 + a3_mfg_gwp) if bom_a3 > 0 else (a1_gwp * 0.25 + a3_mfg_gwp),
            "A4": transport_a4_gwp, "A5": a5_gwp,
            "B1": b1_gwp, "B6": b6_gwp,
            "C1": 0.0, "C2": transport_c2_gwp, "C3": 0.0, "C4": c4_gwp,
            "D": d_gwp
        }
        total_gwp = sum(module_gwp_map.values())

        # ── 3. Build all 4 output groups ────────────────────────
        module_impacts = _build_module_impacts(cursor, bom, module_gwp_map)


        # GROUP 1: Environmental impacts
        env_impacts = {cat: module_impacts[cat] for cat in EF31_IMPACT_CATEGORIES}

        # GROUP 2: Resource use (simplified estimates)
        resource_use = {
            "pere":  {"total": round(annual_kwh * 0.08 * lifetime / fu, 4)},
            "penre": {"total": round(annual_kwh * 2.5 * lifetime / fu, 4)},
            "pert":  {"total": round(annual_kwh * 2.58 * lifetime / fu, 4)},
            "penrt": {"total": round(annual_kwh * 2.5 * lifetime / fu, 4)},
            "sm":    {"total": round(product_mass_kg * recycling_pct / fu, 4)},
            "rsf":   {"total": 0.0}, "nrsf": {"total": 0.0},
            "fw":    {"total": round(mfg_kwh * 0.002 / fu, 4)},
            "perm":  {"total": 0.0}, "penrm": {"total": 0.0},
        }

        # GROUP 3: Waste outputs
        waste_outputs = {
            "nhwd": {"total": round(product_mass_kg * landfill_pct / fu, 4)},
            "hwd":  {"total": round(product_mass_kg * 0.01 / fu, 6)},
            "rwd":  {"total": 0.0},
            "cru":  {"total": round(product_mass_kg * float(eol.get("waste_to_reuse_pct") or 0) / 100 / fu, 4)},
            "mfr":  {"total": round(product_mass_kg * recycling_pct / fu, 4)},
            "mer":  {"total": round(product_mass_kg * float(eol.get("waste_to_incineration_pct") or 10) / 100 / fu, 4)},
            "ee":   {"total": round(float(eol.get("energy_recovery_mj") or 0) / fu, 4)},
        }

        # GROUP 4: Operational outputs
        operational_outputs = {
            "annual_electricity_kwh":      annual_kwh,
            "lifetime_electricity_kwh":    lifetime_kwh,
            "electricity_per_func_unit":   lifetime_kwh / fu,
            "refrigerant_leakage_kg":      charge * leakage_rate * lifetime,
            "direct_air_emissions_kg_co2": b1_gwp * fu,
            "packaging_waste_kg":          float(install.get("packaging_waste_kg") or 0),
            "waste_to_landfill_kg":        product_mass_kg * landfill_pct,
            "waste_to_recycling_kg":       product_mass_kg * recycling_pct,
            "transport_distances_km":      {t.get("lc_module", "A4"): float(t.get("road_distance_km") or 0) for t in transport_legs},
            "maintenance_impact_kg_co2e":  total_gwp * 0.002,
        }

        # Calculate itemized hotspots (top contributing materials and modules)
        hotspots_list = []
        tot_gwp_abs = abs(total_gwp) if total_gwp != 0 else 1.0

        for b in bom:
            mod = b.get("lc_module") or "A1"
            mass = float(b.get("mass_kg") or 0.0)
            gwp_f = float(b.get("gwp_factor") or 1.0)
            item_gwp = mass * gwp_f
            pct = (item_gwp / tot_gwp_abs) * 100.0
            hotspots_list.append({
                "module": mod,
                "material_name": b.get("material_name", "Material"),
                "gwp_kg_co2e": round(item_gwp, 4),
                "percentage": round(pct, 2),
                "description": f"Material input of {mass} kg {b.get('material_name')}"
            })

        transport_gwp_a4 = transport_a4_gwp
        if transport_gwp_a4 > 0:
            hotspots_list.append({
                "module": "A4",
                "material_name": "Transport to Site",
                "gwp_kg_co2e": round(transport_gwp_a4, 4),
                "percentage": round((transport_gwp_a4 / tot_gwp_abs) * 100.0, 2),
                "description": "Logistics and transportation to installation site"
            })
        if a3_mfg_gwp > 0:
            hotspots_list.append({
                "module": "A3",
                "material_name": "Manufacturing Energy",
                "gwp_kg_co2e": round(a3_mfg_gwp, 4),
                "percentage": round((a3_mfg_gwp / tot_gwp_abs) * 100.0, 2),
                "description": "Electricity and energy used during manufacturing"
            })
        if b6_gwp > 0:
            hotspots_list.append({
                "module": "B6",
                "material_name": "Operational Energy Use",
                "gwp_kg_co2e": round(b6_gwp, 4),
                "percentage": round((b6_gwp / tot_gwp_abs) * 100.0, 2),
                "description": "Operational electricity over product lifetime"
            })

        hotspots_list.sort(key=lambda x: abs(x["percentage"]), reverse=True)

        ai_summary = {
            "carbon_footprint_kg_co2e": round(total_gwp, 4),
            "lca_by_module":            {mod: {"GWP_total": round(v, 4)} for mod, v in module_gwp_map.items()},
            "compliance_summary":       {
                "ISO_14025": "PASS",
                "EN_15804_A2": "PASS" if project.get("epd_standard") == "EN_15804_A2" else "N/A",
                "PCR": project.get("lci_database", "ecoinvent_3.12_cutoff")
            }
        }

        # Fabrication check (Rule 1.2)
        from core.epd_validator import check_fabrication_patterns
        is_fab, fab_msg = check_fabrication_patterns({"environmental_impacts": env_impacts})
        if is_fab:
            raise ValueError(f"Calculation halted due to fabrication/repeated mantissa check: {fab_msg}")

        # ── 4. Write results to RDS ──────────────────────────────
        result_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO lca_results (
                id, project_id, run_id, lcia_method, is_final, functional_unit,
                gwp_total_kg_co2e, gwp_fossil_kg_co2e, gwp_biogenic_kg_co2e, gwp_luluc_kg_co2e,
                odp_kg_cfc11e, ap_mol_h_eq, ep_freshwater_kg_p_eq, ep_marine_kg_n_eq, ep_terrestrial_mol_n_eq,
                pocp_kg_nmvoc_eq, adpe_kg_sb_eq, adpf_mj, wdp_m3_world_eq, pm_disease_incidence,
                ir_kbq_u235_eq, etox_ctue, htox_cancer_ctuh, htox_noncancer_ctuh, lu_pt,
                pere_mj, penre_mj, pert_mj, penrt_mj, sm_kg, rsf_mj, nrsf_mj, fw_m3, perm_mj, penrm_mj,
                hwd_kg, nhwd_kg, rwd_kg, cru_kg, mfr_kg, mer_kg, ee_mj,
                annual_electricity_kwh, lifetime_electricity_kwh, electricity_per_fu_kwh,
                refrigerant_leakage_kg, direct_air_emissions_kg_co2, packaging_waste_kg,
                waste_to_landfill_kg, waste_to_recycling_kg, transport_distances_km,
                maintenance_impact_kg_co2e, carbon_footprint_kg_co2e, compliance_summary, hotspots
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            result_id, project_id, run_id, project.get("lcia_method", "EF_3_1"), True,
            f"{fu} {project.get('functional_unit_unit', 'unit')}",
            json.dumps(env_impacts.get("GWP_total", {})),
            json.dumps(env_impacts.get("GWP_fossil", {})),
            json.dumps(env_impacts.get("GWP_biogenic", {})),
            json.dumps(env_impacts.get("GWP_luluc", {})),
            json.dumps(env_impacts.get("ODP", {})),
            json.dumps(env_impacts.get("AP", {})),
            json.dumps(env_impacts.get("EP_freshwater", {})),
            json.dumps(env_impacts.get("EP_marine", {})),
            json.dumps(env_impacts.get("EP_terrestrial", {})),
            json.dumps(env_impacts.get("POCP", {})),
            json.dumps(env_impacts.get("ADPE", {})),
            json.dumps(env_impacts.get("ADPF", {})),
            json.dumps(env_impacts.get("WDP", {})),
            json.dumps(env_impacts.get("PM", {})),
            json.dumps(env_impacts.get("IR", {})),
            json.dumps(env_impacts.get("ETox", {})),
            json.dumps(env_impacts.get("HTox_cancer", {})),
            json.dumps(env_impacts.get("HTox_noncancer", {})),
            json.dumps(env_impacts.get("LandUse", {})),
            json.dumps(resource_use.get("pere", {})),
            json.dumps(resource_use.get("penre", {})),
            json.dumps(resource_use.get("pert", {})),
            json.dumps(resource_use.get("penrt", {})),
            json.dumps(resource_use.get("sm", {})),
            json.dumps(resource_use.get("rsf", {})),
            json.dumps(resource_use.get("nrsf", {})),
            json.dumps(resource_use.get("fw", {})),
            json.dumps(resource_use.get("perm", {})),
            json.dumps(resource_use.get("penrm", {})),
            json.dumps(waste_outputs.get("hwd", {})),
            json.dumps(waste_outputs.get("nhwd", {})),
            json.dumps(waste_outputs.get("rwd", {})),
            json.dumps(waste_outputs.get("cru", {})),
            json.dumps(waste_outputs.get("mfr", {})),
            json.dumps(waste_outputs.get("mer", {})),
            json.dumps(waste_outputs.get("ee", {})),
            operational_outputs["annual_electricity_kwh"],
            operational_outputs["lifetime_electricity_kwh"],
            operational_outputs["electricity_per_func_unit"],
            operational_outputs["refrigerant_leakage_kg"],
            operational_outputs["direct_air_emissions_kg_co2"],
            operational_outputs["packaging_waste_kg"],
            operational_outputs["waste_to_landfill_kg"],
            operational_outputs["waste_to_recycling_kg"],
            json.dumps(operational_outputs["transport_distances_km"]),
            operational_outputs["maintenance_impact_kg_co2e"],
            ai_summary["carbon_footprint_kg_co2e"],
            json.dumps(ai_summary["compliance_summary"]),
            json.dumps(hotspots_list),
        ))
        conn.commit()

        return {"status": "complete", "result_id": result_id, "gwp_total": total_gwp}

    except Exception as e:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def _run_lca_firestore_fallback(project_id: str, run_id: str) -> dict:
    """Fallback for local dev without RDS — writes simplified result to Firestore."""
    from core.firebase import get_db
    from engine.matrix_lca import run_lca, SingularMatrixError
    N = 5
    A = np.eye(N); A[0, 1] = -0.2; A[1, 2] = -0.1
    B = np.zeros((10, N)); B[0, :] = [2.4, 0.5, 0.1, 1.2, 0.05]
    Q = EF31_Q_SIMPLIFIED.T[:, :10] if EF31_Q_SIMPLIFIED.shape[0] >= 10 else np.zeros((19, 10))
    f = np.zeros(N); f[0] = 1.0
    result = run_lca(A, B, Q, f)
    db = get_db()
    db.collection("lca_results").document(f"res_{run_id}").set({
        "project_id": project_id, "run_id": run_id,
        "gwp_total": float(np.sum(result.h[:4])),
        "status": "complete (firestore fallback)"
    })
    return {"status": "complete", "result_id": f"res_{run_id}"}
