-- EcoMetric — AWS RDS PostgreSQL Schema for LCI Datasets & Vector Search

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector"; -- Enable pgvector for semantic search

-- LCI Datasets Table (Parsed .spold dataset metadata & LCIA GWP factors)
CREATE TABLE IF NOT EXISTS lci_datasets (
    id VARCHAR(128) PRIMARY KEY,
    name VARCHAR(512) NOT NULL,
    activity VARCHAR(512) NOT NULL,
    geography VARCHAR(10) DEFAULT 'GLO',
    reference_year INT DEFAULT 2023,
    data_quality_score NUMERIC(3,2) DEFAULT 1.2,
    unit VARCHAR(50) DEFAULT 'kg',
    gwp_factor NUMERIC(12,6) NOT NULL, -- kg CO2e per unit
    category VARCHAR(128) DEFAULT 'Materials',
    source_file VARCHAR(256),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    embedding vector(384) -- Semantic vector embedding for material search
);

-- Index for text and category search
CREATE INDEX IF NOT EXISTS idx_lci_name ON lci_datasets (name);
CREATE INDEX IF NOT EXISTS idx_lci_category ON lci_datasets (category);
CREATE INDEX IF NOT EXISTS idx_lci_geography ON lci_datasets (geography);
