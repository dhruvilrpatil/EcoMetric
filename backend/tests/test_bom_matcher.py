"""
backend/tests/test_bom_matcher.py

Unit and integration tests for BOM material extraction and context-aware dataset matching.
Validates:
- Positive matching for raw materials (Steel, Copper, Aluminum, Electronics)
- Negative semantic filtering against welding, scrap, waste, and used materials in Module A1
- Chemical/refrigerant validation (R-1233zd(E) vs used R12)
- Explicit process extraction (welding when specified)
- Physical mass in kg preservation
"""

import pytest
from core.db import get_connection
from nlp.bom_extractor import RobustBOMExtractorWithFallback
from nlp.matcher import DatabaseMaterialMatcher, classify_process_type, PROCESS_MATERIAL_PROD, PROCESS_MARKET, PROCESS_COMPONENT_PROD, PROCESS_MANUFACTURING, PROCESS_EOL_SCRAP


@pytest.fixture(scope="module")
def db_conn():
    with get_connection() as conn:
        yield conn


@pytest.fixture
def extractor():
    return RobustBOMExtractorWithFallback()


@pytest.fixture
def matcher(db_conn):
    return DatabaseMaterialMatcher(db_conn)


class TestBOMMatcher:
    """Test suite covering the 6 core BOM matching acceptance tests."""

    def test_1_steel_raw_material(self, extractor, matcher):
        """
        TEST 1:
        Input: Steel: 5000kg
        Expected: Steel material production/market dataset (e.g. steel production, converter, low-alloyed)
        Must NOT: welding, gas, steel
        """
        raw_text = "Steel: 5000kg"
        extraction = extractor.extract_materials(raw_text)
        assert len(extraction["extracted_materials"]) == 1
        item = extraction["extracted_materials"][0]
        assert item["quantity_base"] == 5000.0
        assert item["unit_base"] == "kg"
        assert item["intended_context"] == "material_procurement"
        assert item["module"] == "A1"

        candidates = matcher.find_matches(
            material_name=item["material_name"],
            category=item["material_category"],
            intended_context=item["intended_context"],
            module=item["module"]
        )
        assert len(candidates) > 0

        top_match, status, message = matcher.evaluate_top_match(candidates)
        assert top_match is not None
        assert status == "valid_match"
        assert "welding" not in top_match["ecoinvent_name"].lower()
        assert top_match["process_type"] in [PROCESS_MATERIAL_PROD, PROCESS_MARKET]
        assert any(k in top_match["ecoinvent_name"].lower() for k in ["steel production", "market for steel"])

    def test_2_copper_raw_material(self, extractor, matcher):
        """
        TEST 2:
        Input: Copper: 1200kg
        Expected: Copper material production/market dataset (e.g. market for copper, cathode)
        Must NOT: scrap, waste, copper cake, bottom ash, or end-of-life
        """
        raw_text = "Copper: 1200kg"
        extraction = extractor.extract_materials(raw_text)
        assert len(extraction["extracted_materials"]) == 1
        item = extraction["extracted_materials"][0]
        assert item["quantity_base"] == 1200.0
        assert item["unit_base"] == "kg"

        candidates = matcher.find_matches(
            material_name=item["material_name"],
            category=item["material_category"],
            intended_context=item["intended_context"],
            module=item["module"]
        )
        assert len(candidates) > 0

        top_match, status, message = matcher.evaluate_top_match(candidates)
        assert top_match is not None
        assert status == "valid_match"
        assert "scrap" not in top_match["ecoinvent_name"].lower()
        assert "cake" not in top_match["ecoinvent_name"].lower()
        assert "ash" not in top_match["ecoinvent_name"].lower()
        assert top_match["process_type"] in [PROCESS_MATERIAL_PROD, PROCESS_MARKET]
        assert "copper" in top_match["ecoinvent_name"].lower()

    def test_3_aluminum_raw_material(self, extractor, matcher):
        """
        TEST 3:
        Input: Aluminum: 300kg
        Expected: Aluminum material production/market dataset (e.g. aluminium production, primary, ingot)
        Must NOT: welding, arc, aluminium
        """
        raw_text = "Aluminum: 300kg"
        extraction = extractor.extract_materials(raw_text)
        assert len(extraction["extracted_materials"]) == 1
        item = extraction["extracted_materials"][0]
        assert item["quantity_base"] == 300.0
        assert item["unit_base"] == "kg"

        candidates = matcher.find_matches(
            material_name=item["material_name"],
            category=item["material_category"],
            intended_context=item["intended_context"],
            module=item["module"]
        )
        assert len(candidates) > 0

        top_match, status, message = matcher.evaluate_top_match(candidates)
        assert top_match is not None
        assert status == "valid_match"
        assert "welding" not in top_match["ecoinvent_name"].lower()
        assert top_match["process_type"] in [PROCESS_MATERIAL_PROD, PROCESS_MARKET]
        assert "aluminium" in top_match["ecoinvent_name"].lower()

    def test_4_electronics_component(self, extractor, matcher):
        """
        TEST 4:
        Input: Electronics: 50kg
        Expected: Electronic component/material production dataset (e.g. electronics production, for control units)
        Must NOT: market for electronics scrap
        """
        raw_text = "Electronics: 50kg"
        extraction = extractor.extract_materials(raw_text)
        assert len(extraction["extracted_materials"]) == 1
        item = extraction["extracted_materials"][0]
        assert item["quantity_base"] == 50.0
        assert item["unit_base"] == "kg"

        candidates = matcher.find_matches(
            material_name=item["material_name"],
            category=item["material_category"],
            intended_context=item["intended_context"],
            module=item["module"]
        )
        assert len(candidates) > 0

        top_match, status, message = matcher.evaluate_top_match(candidates)
        assert top_match is not None
        assert status == "valid_match"
        assert "scrap" not in top_match["ecoinvent_name"].lower()
        assert top_match["process_type"] in [PROCESS_COMPONENT_PROD, PROCESS_MARKET]
        assert "electronic" in top_match["ecoinvent_name"].lower()

    def test_5_refrigerant_r1233zd_missing_handling(self, extractor, matcher):
        """
        TEST 5:
        Input: Refrigerant: R-1233zd(E), 500kg
        Expected: R-1233zd(E) dataset if available, otherwise 'not_found' / manual mapping required.
        Must NOT: map to used refrigerant R12!
        """
        raw_text = "Refrigerant: R-1233zd(E), 500kg"
        extraction = extractor.extract_materials(raw_text)
        assert len(extraction["extracted_materials"]) == 1
        item = extraction["extracted_materials"][0]
        assert item["quantity_base"] == 500.0
        assert item["unit_base"] == "kg"
        assert item["material_category"] == "refrigerant"

        candidates = matcher.find_matches(
            material_name=item["material_name"],
            category=item["material_category"],
            intended_context=item["intended_context"],
            module=item["module"]
        )

        top_match, status, message = matcher.evaluate_top_match(candidates)
        # Because R-1233zd(E) is not directly present in ecoinvent 3.12 cutoff, it must NOT fabricate or match used R12
        if top_match is not None:
            assert "r12" not in top_match["ecoinvent_name"].lower()
            assert "used" not in top_match["ecoinvent_name"].lower()
        else:
            assert status == "not_found"
            assert "manual mapping required" in message.lower()

    def test_6_explicit_process_welding(self, extractor, matcher):
        """
        TEST 6:
        Input: aluminum welding process: 10kg
        Expected: A welding/manufacturing process IS selected because input explicitly specified welding.
        """
        raw_text = "aluminum welding process: 10kg"
        extraction = extractor.extract_materials(raw_text)
        assert len(extraction["extracted_materials"]) == 1
        item = extraction["extracted_materials"][0]
        assert item["intended_context"] == "manufacturing_process"

        candidates = matcher.find_matches(
            material_name=item["material_name"],
            category=item["material_category"],
            intended_context=item["intended_context"],
            module=item["module"]
        )
        assert len(candidates) > 0

        top_match, status, message = matcher.evaluate_top_match(candidates)
        assert top_match is not None
        assert "welding" in top_match["ecoinvent_name"].lower()
        assert top_match["process_type"] == PROCESS_MANUFACTURING
