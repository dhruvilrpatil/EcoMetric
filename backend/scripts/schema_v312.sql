-- ============================================================
-- EcoMetric — Full AWS RDS PostgreSQL Schema v2
-- Supports complete EN 15804+A2 / ISO 14025 EPD inputs/outputs
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ─────────────────────────────────────────────────────────────
-- 1. Ecoinvent LCI Background Database (18,000+ processes)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS lci_database (
    id                      VARCHAR(128) PRIMARY KEY,
    activity_name           TEXT NOT NULL,
    geography               VARCHAR(20) DEFAULT 'GLO',
    reference_year          INT DEFAULT 2023,
    data_quality_score      INT DEFAULT 3,
    xml_file                VARCHAR(256),
    elementary_exchanges    JSONB NOT NULL,   -- { "Carbon dioxide, fossil": { "amount": 2.4, "unit": "kg" }, ... }
    intermediate_exchanges  JSONB NOT NULL,   -- { "Steel, low-alloyed": 0.5, ... }
    indexed_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_lci_activity_trgm ON lci_database USING gin (activity_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_lci_geography ON lci_database (geography);

-- ─────────────────────────────────────────────────────────────
-- 1b. LCIA Characterization Factors (ecoinvent 3.12 LCIA)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS lcia_factors (
    id                      SERIAL PRIMARY KEY,
    method                  VARCHAR(256) NOT NULL,
    category                VARCHAR(256),
    indicator               VARCHAR(256) NOT NULL,
    flow_name               TEXT NOT NULL,
    compartment             VARCHAR(100),
    subcompartment          VARCHAR(100),
    unit                    VARCHAR(50),
    characterization_factor DOUBLE PRECISION NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_lcia_method ON lcia_factors (method);
CREATE INDEX IF NOT EXISTS idx_lcia_flow ON lcia_factors (flow_name);
CREATE INDEX IF NOT EXISTS idx_lcia_method_flow ON lcia_factors (method, flow_name);



-- ─────────────────────────────────────────────────────────────
-- 2. Projects (top-level project metadata + LCA configuration)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS projects (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                 VARCHAR(256) NOT NULL,            -- Firebase UID
    project_name            VARCHAR(512) NOT NULL,
    -- Product details
    product_name            VARCHAR(512) NOT NULL,
    product_sku             VARCHAR(128),
    product_lifetime_years  NUMERIC(6,2) NOT NULL DEFAULT 75,
    product_configuration   VARCHAR(512),
    manufacturer_name       VARCHAR(512),
    manufacturing_country   VARCHAR(100),
    -- Functional unit
    functional_unit_quantity NUMERIC(12,4) NOT NULL DEFAULT 1.0,
    functional_unit_unit    VARCHAR(50) NOT NULL DEFAULT 'ton_chilling_capacity',
    -- LCA configuration
    epd_standard            VARCHAR(50)  DEFAULT 'EN_15804_A2',   -- EN_15804_A2 | ISO_21930 | ISO_14025
    system_boundary         VARCHAR(50)  DEFAULT 'cradle_to_grave',
    lcia_method             VARCHAR(50)  DEFAULT 'EF_3_1',        -- EF_3_1 | TRACI_2_1 | CML_IA | PEF
    lci_database            VARCHAR(50)  DEFAULT 'ecoinvent_3.12_cutoff',
    active_modules          TEXT[]       DEFAULT ARRAY['A1','A2','A3','A4','A5','B1','B6','C1','C2','C3','C4','D'],
    -- Narrative & Audit fields
    company_description     TEXT,
    product_narrative       TEXT,
    csi_division_code       VARCHAR(100),
    certifications          TEXT[],
    pcr_reviewer_names      TEXT[],
    lca_conductor_name      VARCHAR(256),
    verifier_name           VARCHAR(256),
    verifier_email          VARCHAR(256),
    program_operator_name   VARCHAR(256),
    program_operator_address TEXT,
    program_operator_website VARCHAR(256),
    program_operator_logo_url VARCHAR(512),
    -- Status
    status                  VARCHAR(30)  DEFAULT 'draft',         -- draft | in_progress | calculating | complete | published
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- ─────────────────────────────────────────────────────────────
-- 3. Bill of Materials (Material Inventory)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bom_items (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id              UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    lc_module               VARCHAR(10) NOT NULL,              -- A1, A2, A3, ...
    material_name           VARCHAR(512) NOT NULL,             -- e.g. "Steel, low-alloyed"
    mass_kg                 NUMERIC(14,4) NOT NULL,
    unit                    VARCHAR(50) DEFAULT 'kg',
    lci_dataset_id          VARCHAR(128) REFERENCES lci_database(id),
    data_quality             VARCHAR(20) DEFAULT 'SECONDARY',  -- PRIMARY | SECONDARY | PROXY
    gwp_factor              NUMERIC(12,6),                     -- kg CO2e per unit (from ecoinvent)
    is_cut_off              BOOLEAN DEFAULT FALSE,
    cut_off_reason          TEXT,
    sort_order              INT DEFAULT 0,
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_bom_project ON bom_items(project_id);
CREATE INDEX IF NOT EXISTS idx_bom_module ON bom_items(lc_module);


-- ─────────────────────────────────────────────────────────────
-- 4. Manufacturing Data (Module A3)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS manufacturing_data (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id              UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE UNIQUE,
    manufacturing_location  VARCHAR(256),
    electricity_use_kwh     NUMERIC(14,4) DEFAULT 0,           -- kWh per functional unit
    electricity_grid_region VARCHAR(20) DEFAULT 'GLO',
    assembly_process_desc   TEXT,
    product_mass_kg         NUMERIC(14,4),
    manufacturing_energy_mj NUMERIC(14,4) DEFAULT 0,           -- Total manufacturing energy in MJ
    other_energy_sources    JSONB,                             -- { "natural_gas_mj": 0, "steam_mj": 0 }
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- ─────────────────────────────────────────────────────────────
-- 5. Transportation Data (Modules A2, A4, C2)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS transportation_data (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id              UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    lc_module               VARCHAR(10) NOT NULL,              -- A2 | A4 | C2
    vehicle_type            VARCHAR(100),                      -- Heavy truck EURO5, Rail, Ship, Air
    product_weight_kg       NUMERIC(14,4),
    fuel_type               VARCHAR(50),
    fuel_efficiency_l_100km NUMERIC(8,4),
    road_distance_km        NUMERIC(10,2) DEFAULT 0,
    ocean_freight_km        NUMERIC(10,2) DEFAULT 0,
    capacity_utilization_pct NUMERIC(5,2) DEFAULT 100.0,
    lci_dataset_id          VARCHAR(128) REFERENCES lci_database(id),
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_transport_project ON transportation_data(project_id);


-- ─────────────────────────────────────────────────────────────
-- 6. Installation Data (Module A5)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS installation_data (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id              UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE UNIQUE,
    diesel_crane_liters     NUMERIC(10,4) DEFAULT 0,
    packaging_waste_kg      NUMERIC(10,4) DEFAULT 0,
    packaging_material       VARCHAR(100) DEFAULT 'cardboard',
    installation_assumptions TEXT,
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- ─────────────────────────────────────────────────────────────
-- 7. Use Phase Data (Modules B1–B7)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS use_phase_data (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id                  UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE UNIQUE,
    -- B6 Operational energy
    annual_electricity_kwh      NUMERIC(14,4) NOT NULL DEFAULT 0,
    electricity_grid_region     VARCHAR(20) DEFAULT 'US',
    lifetime_electricity_kwh    NUMERIC(16,4) GENERATED ALWAYS AS (annual_electricity_kwh * 75) STORED,
    electricity_per_func_unit   NUMERIC(16,4),
    -- B1 Refrigerant leakage
    refrigerant_type            VARCHAR(100) DEFAULT 'R-1233zd(E)',
    refrigerant_charge_kg       NUMERIC(10,4) DEFAULT 0,
    annual_leakage_rate_pct     NUMERIC(5,4) DEFAULT 0.01,     -- fraction per year
    refrigerant_gwp             NUMERIC(8,2) DEFAULT 1.0,      -- GWP100 of refrigerant
    -- Maintenance & replacement
    maintenance_cycles          INT DEFAULT 1,
    replacement_cycles          INT DEFAULT 0,
    maintenance_notes           TEXT,
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- ─────────────────────────────────────────────────────────────
-- 8. End-of-Life Data (Modules C1–C4, D)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS end_of_life_data (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id                  UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE UNIQUE,
    -- C4 Waste streams (must sum to 100%)
    waste_to_landfill_pct       NUMERIC(5,2) DEFAULT 30.0,
    waste_to_recycling_pct      NUMERIC(5,2) DEFAULT 60.0,
    waste_to_incineration_pct   NUMERIC(5,2) DEFAULT 10.0,
    waste_to_reuse_pct          NUMERIC(5,2) DEFAULT 0.0,
    -- C2 Disposal transport
    disposal_transport_km       NUMERIC(10,2) DEFAULT 50.0,
    disposal_vehicle_type       VARCHAR(100) DEFAULT 'Heavy truck EURO5',
    -- B1/C3 Refrigerant
    refrigerant_recovery_rate_pct NUMERIC(5,2) DEFAULT 95.0,
    -- D Beyond system boundary credits
    recycling_credit_included   BOOLEAN DEFAULT TRUE,
    energy_recovery_mj          NUMERIC(14,4) DEFAULT 0,
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- ─────────────────────────────────────────────────────────────
-- 9. LCA Results — All 4 Output Groups per module
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS lca_results (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id                  UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    run_id                      UUID NOT NULL,
    lcia_method                 VARCHAR(50) DEFAULT 'EF_3_1',
    run_timestamp               TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_final                    BOOLEAN DEFAULT FALSE,
    functional_unit             VARCHAR(256),

    -- ── GROUP 1: Environmental Impact Indicators ──────────────
    -- Values are JSONB maps: { "A1": val, "A2": val, ..., "total": val }
    gwp_total_kg_co2e           JSONB,   -- Global Warming Potential (total)
    gwp_fossil_kg_co2e          JSONB,   -- GWP fossil
    gwp_biogenic_kg_co2e        JSONB,   -- GWP biogenic
    gwp_luluc_kg_co2e           JSONB,   -- GWP land use & land use change
    odp_kg_cfc11e               JSONB,   -- Ozone Depletion Potential
    ap_mol_h_eq                 JSONB,   -- Acidification Potential
    ep_freshwater_kg_p_eq       JSONB,   -- Eutrophication Freshwater
    ep_marine_kg_n_eq           JSONB,   -- Eutrophication Marine
    ep_terrestrial_mol_n_eq     JSONB,   -- Eutrophication Terrestrial
    pocp_kg_nmvoc_eq            JSONB,   -- Photochemical Ozone Formation
    adpe_kg_sb_eq               JSONB,   -- Abiotic Depletion (minerals & metals)
    adpf_mj                     JSONB,   -- Abiotic Depletion (fossil fuels)
    wdp_m3_world_eq             JSONB,   -- Water Deprivation Potential
    pm_disease_incidence        JSONB,   -- Particulate Matter
    ir_kbq_u235_eq              JSONB,   -- Ionizing Radiation
    etox_ctue                   JSONB,   -- Freshwater Ecotoxicity
    htox_cancer_ctuh            JSONB,   -- Human Toxicity (Cancer)
    htox_noncancer_ctuh         JSONB,   -- Human Toxicity (Non-Cancer)
    lu_pt                       JSONB,   -- Land Use Impact

    -- ── GROUP 2: Resource Use Outputs ────────────────────────
    pere_mj                     JSONB,   -- Renewable primary energy (energy use)
    perm_mj                     JSONB,   -- Renewable primary energy (material use)
    pert_mj                     JSONB,   -- Renewable primary energy total
    penre_mj                    JSONB,   -- Non-renewable primary energy (energy)
    penrm_mj                    JSONB,   -- Non-renewable primary energy (material)
    penrt_mj                    JSONB,   -- Non-renewable primary energy total
    sm_kg                       JSONB,   -- Secondary material use
    rsf_mj                      JSONB,   -- Renewable secondary fuels
    nrsf_mj                     JSONB,   -- Non-renewable secondary fuels
    fw_m3                       JSONB,   -- Freshwater consumption

    -- ── GROUP 3: Waste & End-of-Life Outputs ─────────────────
    hwd_kg                      JSONB,   -- Hazardous waste disposed
    nhwd_kg                     JSONB,   -- Non-hazardous waste disposed
    rwd_kg                      JSONB,   -- Radioactive waste disposed
    cru_kg                      JSONB,   -- Components for reuse
    mfr_kg                      JSONB,   -- Materials sent for recycling
    mer_kg                      JSONB,   -- Materials for energy recovery
    ee_mj                       JSONB,   -- Exported energy

    -- ── GROUP 4: Product-Specific Operational Outputs ─────────
    annual_electricity_kwh      NUMERIC(16,4),
    lifetime_electricity_kwh    NUMERIC(16,4),
    electricity_per_fu_kwh      NUMERIC(16,4),
    refrigerant_leakage_kg      NUMERIC(12,6),
    direct_air_emissions_kg_co2 NUMERIC(14,4),
    packaging_waste_kg          NUMERIC(10,4),
    waste_to_landfill_kg        NUMERIC(14,4),
    waste_to_recycling_kg       NUMERIC(14,4),
    transport_distances_km      JSONB,   -- { "A2": 200, "A4": 500, "C2": 50 }
    maintenance_impact_kg_co2e  NUMERIC(14,4),

    -- ── AI EPD Summary (optional) ─────────────────────────────
    carbon_footprint_kg_co2e    NUMERIC(14,4),
    compliance_summary          JSONB,   -- { "ISO_14025": true, "EN_15804": true, "PCR": "..." }

    -- ── Audit ─────────────────────────────────────────────────
    matrix_A_dimensions         INT[],
    matrix_B_dimensions         INT[],
    condition_number            NUMERIC(20,6),
    hotspots                    JSONB
);
CREATE INDEX IF NOT EXISTS idx_results_project ON lca_results(project_id);
CREATE INDEX IF NOT EXISTS idx_results_run ON lca_results(run_id);

-- ─────────────────────────────────────────────────────────────
-- 8. NLP Pipeline tables for active learning & traceability
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS nlp_audit_logs (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id              UUID REFERENCES projects(id) ON DELETE CASCADE,
    event_type              VARCHAR(100) NOT NULL,
    file_name               VARCHAR(256),
    raw_text_preview        TEXT,
    extracted_materials     JSONB,
    matching_details        JSONB,
    timestamp               TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS nlp_feedback (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id              UUID REFERENCES projects(id) ON DELETE CASCADE,
    material_id             UUID,
    extracted_material_name VARCHAR(512) NOT NULL,
    selected_ecoinvent_id   VARCHAR(128) REFERENCES lci_database(id),
    user_feedback           VARCHAR(50) NOT NULL, -- 'correct', 'incorrect', 'needs_review'
    user_notes              TEXT,
    confidence_components   JSONB,
    timestamp               TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS nlp_model_weights (
    id                      SERIAL PRIMARY KEY,
    weights                 JSONB NOT NULL,
    brier_score             DOUBLE PRECISION,
    samples_used            INT,
    calibrated_at           TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

