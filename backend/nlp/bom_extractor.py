"""
backend/nlp/bom_extractor.py

BOM Information Extraction Engine.
Extracts material items, physical quantities (strictly in kg), units, categories,
intended process contexts (A1 raw materials vs A3 manufacturing processes vs C3/C4 EOL),
and data provenance.
"""

from __future__ import annotations
import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Category mapping lookup
DOMAIN_KEYWORDS: Dict[str, Dict[str, str]] = {
    "steel": {"category": "metals", "component": "structural"},
    "stainless steel": {"category": "metals", "component": "structural"},
    "copper": {"category": "metals", "component": "piping / electrical"},
    "aluminum": {"category": "metals", "component": "structural / heat exchange"},
    "aluminium": {"category": "metals", "component": "structural / heat exchange"},
    "brass": {"category": "metals", "component": "fittings"},
    "iron": {"category": "metals", "component": "structural / casting"},
    "cast iron": {"category": "metals", "component": "structural / casting"},
    "polyethylene": {"category": "plastics", "component": "insulation / casing"},
    "polypropylene": {"category": "plastics", "component": "insulation / casing"},
    "pvc": {"category": "plastics", "component": "piping / insulation"},
    "plastic": {"category": "plastics", "component": "casing"},
    "rubber": {"category": "elastomers", "component": "gaskets / seals"},
    "elastomer": {"category": "elastomers", "component": "gaskets / seals"},
    "electronics": {"category": "electronics", "component": "control / electrical"},
    "electronic": {"category": "electronics", "component": "control / electrical"},
    "circuit board": {"category": "electronics", "component": "control / electrical"},
    "pcb": {"category": "electronics", "component": "control / electrical"},
    "control board": {"category": "electronics", "component": "control / electrical"},
    "refrigerant": {"category": "refrigerant", "component": "working fluid"},
    "r-1233zd(e)": {"category": "refrigerant", "component": "working fluid"},
    "r-1233zd": {"category": "refrigerant", "component": "working fluid"},
    "r-134a": {"category": "refrigerant", "component": "working fluid"},
    "r134a": {"category": "refrigerant", "component": "working fluid"},
    "r-32": {"category": "refrigerant", "component": "working fluid"},
    "r-410a": {"category": "refrigerant", "component": "working fluid"},
    "r-22": {"category": "refrigerant", "component": "working fluid"},
    "concrete": {"category": "mineral", "component": "foundation"},
    "cement": {"category": "mineral", "component": "foundation"},
    "glass wool": {"category": "mineral fibers", "component": "thermal insulation"},
    "mineral wool": {"category": "mineral fibers", "component": "thermal insulation"},
    "insulation": {"category": "mineral fibers", "component": "thermal insulation"},
    "glass": {"category": "glass", "component": "panels"},
    "wood": {"category": "wood", "component": "packaging"},
    "cardboard": {"category": "paper", "component": "packaging"},
}

class RobustBOMExtractorWithFallback:
    """
    Multi-stage BOM extraction engine with semantic classification and context awareness.
    """

    def __init__(self):
        self.domain_keywords = DOMAIN_KEYWORDS

    def extract_materials(self, text: str, provenance: str = "extracted") -> Dict[str, Any]:
        """
        Extract materials and quantities from raw text.
        
        Returns structured payload:
        {
            'extraction_status': 'success' | 'partial' | 'manual_required',
            'extracted_materials': [...],
            'extraction_quality_score': 0-100,
            'warnings': [],
            'requires_manual_review': bool,
            'debug_info': {...}
        }
        """
        results: Dict[str, Any] = {
            'extraction_status': 'success',
            'extracted_materials': [],
            'warnings': [],
            'requires_manual_review': False,
            'debug_info': {},
        }

        if not text or not text.strip():
            results['extraction_status'] = 'manual_required'
            results['requires_manual_review'] = True
            results['warnings'].append("Input text is empty. Please enter or paste BOM data.")
            results['extraction_quality_score'] = 0
            return results

        # Stage 1: Domain NER parser
        try:
            materials_ner = self._extract_via_domain_ner(text, provenance)
            results['extracted_materials'].extend(materials_ner)
            results['debug_info']['stage_1_ner_success'] = True
            results['debug_info']['stage_1_ner_count'] = len(materials_ner)
        except Exception as e:
            logger.warning(f"Domain NER failed: {e}")
            results['debug_info']['stage_1_ner_error'] = str(e)
            results['warnings'].append("NER parser encountered an issue; attempting fallback regex parser.")

        # Stage 2: Fallback regex parser for any non-delimited sentences
        try:
            materials_regex = self._extract_via_regex(text, provenance)
            existing_names = {m['material_name'].lower().strip() for m in results['extracted_materials']}
            for m in materials_regex:
                if m['material_name'].lower().strip() not in existing_names:
                    results['extracted_materials'].append(m)
            results['debug_info']['stage_2_regex_success'] = True
        except Exception as e:
            logger.error(f"Regex extraction failed: {e}")
            results['debug_info']['stage_2_regex_error'] = str(e)

        # Stage 3: Quality Assessment
        count = len(results['extracted_materials'])
        if count == 0:
            results['extraction_status'] = 'manual_required'
            results['requires_manual_review'] = True
            results['warnings'].append(
                "No materials could be automatically extracted. Please enter items manually."
            )
            results['extraction_quality_score'] = 0
        elif count < 3:
            results['extraction_status'] = 'partial'
            results['requires_manual_review'] = True
            results['warnings'].append(
                f"Extracted {count} material(s). Please review and add any missing materials manually."
            )
            results['extraction_quality_score'] = min(count * 30, 80)
        else:
            results['extraction_status'] = 'success'
            results['extraction_quality_score'] = 95

        return results

    def _determine_context(self, name: str) -> Tuple[str, str]:
        """
        Determine the intended process context and lifecycle module.
        Returns: (intended_context, module)
        """
        name_low = name.lower()
        if any(w in name_low for w in ["welding", "machining", "turning", "milling", "cutting", "drilling", "stamping", "extrusion", "surface treatment"]):
            return "manufacturing_process", "A3"
        elif any(w in name_low for w in ["scrap", "waste", "disposal", "recycling", "dismantling", "treatment of"]):
            return "end_of_life", "C3"
        elif any(w in name_low for w in ["transport", "freight", "lorry", "truck"]):
            return "transport", "A4"
        return "material_procurement", "A1"

    def _extract_via_domain_ner(self, text: str, provenance: str = "extracted") -> List[Dict[str, Any]]:
        """
        Stage 1: Line-by-line structured extraction matching standard industrial BOM formats.
        Examples:
          - Steel: 5000kg
          - Copper: 1200 kg
          - Aluminum: 300kg
          - Electronics: 50 kg
          - Refrigerant: R-1233zd(E), 500kg
          - Refrigerant R-134a - 45 kg
          - aluminum welding process: 10kg
        """
        extracted: List[Dict[str, Any]] = []
        lines = text.split("\n")

        # Regex matching item name/spec, delimiter, quantity, and unit
        pattern = re.compile(
            r"^\s*([a-zA-Z0-9\s\-\(\)\/\,\.\+]+?)\s*[:\-–—=]\s*([a-zA-Z0-9\s\-\(\)\/\,\.\+]*?)(\d+(?:[\.,]\d+)?)\s*(kg|g|t|lbs|tons|tonnes|m3|l|liters|pcs|pieces)?\s*$",
            re.IGNORECASE
        )

        for line in lines:
            line_str = line.strip()
            if not line_str or line_str.startswith("#"):
                continue

            match = pattern.search(line_str)
            if match:
                prefix = match.group(1).strip()
                middle = match.group(2).strip()
                qty_raw = match.group(3).replace(",", ".").strip()
                unit_raw = (match.group(4) or "kg").lower().strip()

                try:
                    qty = float(qty_raw)
                except ValueError:
                    continue

                # Combine prefix and middle into full item name (e.g. "Refrigerant" + "R-1233zd(E)" -> "Refrigerant R-1233zd(E)")
                if middle and not middle.isdigit():
                    full_name = f"{prefix} {middle}".strip().rstrip(",")
                else:
                    full_name = prefix.rstrip(",")

                # Standardize units strictly to physical mass in kg
                unit = "kg"
                if unit_raw in ['lbs', 'pounds']:
                    qty = round(qty * 0.45359237, 3)
                elif unit_raw in ['g', 'grams']:
                    qty = round(qty / 1000.0, 4)
                elif unit_raw in ['t', 'tons', 'tonnes']:
                    qty = round(qty * 1000.0, 2)

                # Determine category and component role
                category = "other"
                component_cat = "general"
                full_name_low = full_name.lower()

                for kw, info in self.domain_keywords.items():
                    if kw in full_name_low:
                        category = info["category"]
                        component_cat = info["component"]
                        break

                intended_context, module = self._determine_context(full_name)

                extracted.append({
                    "material_name": full_name,
                    "quantity_base": qty,
                    "unit_base": "kg",
                    "material_category": category,
                    "component_category": component_cat,
                    "intended_context": intended_context,
                    "module": module,
                    "data_provenance": provenance,
                    "confidence_ner": 0.95
                })

        return extracted

    def _extract_via_regex(self, text: str, provenance: str = "extracted") -> List[Dict[str, Any]]:
        """
        Stage 2: Free-text fallback for inline quantities (e.g. "5000 kg steel", "300 kg of aluminum").
        """
        extracted: List[Dict[str, Any]] = []
        pattern = re.compile(
            r"(\d+(?:[\.,]\d+)?)\s*(kg|g|t|lbs|tons)\s*(?:of\s+)?([a-zA-Z0-9\s\-\(\)\/\+]{3,35})",
            re.IGNORECASE
        )

        matches = pattern.findall(text)
        for qty_str, unit_raw, mat_name in matches:
            name = mat_name.strip().rstrip(".,;:")
            name_low = name.lower()

            if name_low in ["the", "and", "for", "with", "from", "each", "total"]:
                continue

            try:
                qty = float(qty_str.replace(",", "."))
            except ValueError:
                continue

            if unit_raw.lower() in ['lbs']:
                qty = round(qty * 0.45359237, 3)
            elif unit_raw.lower() in ['g']:
                qty = round(qty / 1000.0, 4)
            elif unit_raw.lower() in ['t', 'tons']:
                qty = round(qty * 1000.0, 2)

            category = "other"
            component_cat = "general"
            for kw, info in self.domain_keywords.items():
                if kw in name_low:
                    category = info["category"]
                    component_cat = info["component"]
                    break

            intended_context, module = self._determine_context(name)

            extracted.append({
                "material_name": name,
                "quantity_base": qty,
                "unit_base": "kg",
                "material_category": category,
                "component_category": component_cat,
                "intended_context": intended_context,
                "module": module,
                "data_provenance": provenance,
                "confidence_ner": 0.70
            })

        return extracted
