import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class RobustBOMExtractorWithFallback:
    """
    Multi-stage extraction with graceful degradation.
    If NER fails, fall back to regex. If regex fails, return what we have + manual override UX.
    """

    def __init__(self):
        # Sample dictionary of common equipment components and standard material mapping categories
        self.domain_keywords = {
            "steel": "metals",
            "copper": "metals",
            "aluminum": "metals",
            "aluminium": "metals",
            "brass": "metals",
            "iron": "metals",
            "polyethylene": "plastics",
            "polypropylene": "plastics",
            "pvc": "plastics",
            "plastic": "plastics",
            "rubber": "elastomers",
            "refrigerant": "chemicals",
            "r-410a": "refrigerant",
            "r-134a": "refrigerant",
            "r-32": "refrigerant",
            "r-1234yf": "refrigerant",
            "concrete": "mineral",
            "cement": "mineral",
            "glass": "glass",
            "insulation": "mineral fibers",
            "wood": "wood",
            "cardboard": "paper",
        }

    def extract_materials(self, text: str) -> Dict[str, Any]:
        """
        Returns structured extraction payload:
        {
            'extraction_status': 'success' | 'partial' | 'manual_required',
            'extracted_materials': [...],
            'extraction_quality_score': 0-100,
            'warnings': [],
            'requires_manual_review': bool,
            'debug_info': {...}
        }
        """
        results = {
            'extraction_status': 'success',
            'extracted_materials': [],
            'warnings': [],
            'requires_manual_review': False,
            'debug_info': {},
        }

        # Stage 1: Try domain NER (dictionary keyword + context parser)
        try:
            materials_ner = self._extract_via_domain_ner(text)
            results['extracted_materials'].extend(materials_ner)
            results['debug_info']['stage_1_ner_success'] = True
            results['debug_info']['stage_1_ner_count'] = len(materials_ner)
        except Exception as e:
            logger.warning(f"Domain NER failed: {e}")
            results['debug_info']['stage_1_ner_error'] = str(e)
            results['warnings'].append("NER extraction encountered an error; falling back to regex.")

        # Stage 2: Regex fallback
        try:
            materials_regex = self._extract_via_regex(text)
            existing_keys = {m['material_name'].lower() for m in results['extracted_materials']}
            new_materials = [m for m in materials_regex if m['material_name'].lower() not in existing_keys]
            results['extracted_materials'].extend(new_materials)
            results['debug_info']['stage_2_regex_success'] = True
            results['debug_info']['stage_2_regex_count'] = len(new_materials)
        except Exception as e:
            logger.error(f"Regex extraction failed: {e}")
            results['debug_info']['stage_2_regex_error'] = str(e)

        # Stage 3: Quality assessment
        if not results['extracted_materials']:
            results['extraction_status'] = 'manual_required'
            results['requires_manual_review'] = True
            results['warnings'].append(
                "No materials automatically extracted. Please paste raw text or enter manually."
            )
        elif len(results['extracted_materials']) < 3:
            results['extraction_status'] = 'partial'
            results['requires_manual_review'] = True
            results['warnings'].append(
                f"Only {len(results['extracted_materials'])} material(s) extracted. "
                "Please verify completeness and add any missing materials manually."
            )

        # Compute quality score
        quality_components = {
            'material_count': min(len(results['extracted_materials']) / 5, 1.0),  # 5+ materials = 100%
            'extraction_success_rate': 0.85 if not results['warnings'] else 0.5,
        }
        results['extraction_quality_score'] = int(
            (quality_components['material_count'] * 0.6 + quality_components['extraction_success_rate'] * 0.4) * 100
        )

        return results

    def _extract_via_domain_ner(self, text: str) -> List[Dict[str, Any]]:
        """Stage 1: Rule-based domain NER simulator matching standard formats."""
        extracted = []
        lines = text.split("\n")
        
        # Match pattern: [material name/description] ... [qty] [unit]
        # e.g., "Steel Frame: 450.5 kg" or "Copper tube (A1) - 12 kg"
        pattern = re.compile(
            r"([a-zA-Z\s\-\(\)\/\d]+?)\s*[:\-–—]\s*(\d+(?:\.\d+)?)\s*(kg|g|t|lbs|tons|m3|l|liters|pcs|pieces)",
            re.IGNORECASE
        )
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            match = pattern.search(line)
            if match:
                name = match.group(1).strip()
                qty = float(match.group(2))
                unit = match.group(3).lower()

                # Clean up unit to standard 'kg' or similar
                if unit in ['lbs', 'pounds']:
                    qty = qty * 0.45359237
                    unit = 'kg'
                elif unit in ['g', 'grams']:
                    qty = qty / 1000.0
                    unit = 'kg'
                elif unit in ['t', 'tons', 'tonnes']:
                    qty = qty * 1000.0
                    unit = 'kg'

                category = "other"
                for kw, cat in self.domain_keywords.items():
                    if kw in name.lower():
                        category = cat
                        break

                extracted.append({
                    "material_name": name,
                    "quantity_base": qty,
                    "unit_base": "kg", # Standardize to kg
                    "material_category": category,
                    "confidence_ner": 0.90
                })
        return extracted

    def _extract_via_regex(self, text: str) -> List[Dict[str, Any]]:
        """Stage 2: Regex fallback to grab quantities and material words anywhere in sentences."""
        extracted = []
        # Find any number followed by unit and a word
        # e.g. "120 kg steel", "5 kg of plastic"
        pattern = re.compile(
            r"(\d+(?:\.\d+)?)\s*(kg|g|t|lbs|pcs)\s*(?:of)?\s*([a-zA-Z]{3,20}(?:\s+[a-zA-Z]{3,20})?)",
            re.IGNORECASE
        )
        matches = pattern.findall(text)
        for qty_str, unit_str, mat_name in matches:
            qty = float(qty_str)
            unit = unit_str.lower()
            name = mat_name.strip()

            if name.lower() in ["the", "and", "for", "with"]:
                continue

            if unit in ['lbs']:
                qty = qty * 0.45359237
                unit = 'kg'
            elif unit in ['g']:
                qty = qty / 1000.0
                unit = 'kg'
            elif unit in ['t']:
                qty = qty * 1000.0
                unit = 'kg'

            category = "other"
            for kw, cat in self.domain_keywords.items():
                if kw in name.lower():
                    category = cat
                    break

            extracted.append({
                "material_name": name,
                "quantity_base": qty,
                "unit_base": "kg",
                "material_category": category,
                "confidence_ner": 0.65
            })
        return extracted
