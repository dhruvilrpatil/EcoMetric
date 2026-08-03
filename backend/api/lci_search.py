"""
backend/api/lci_search.py

LCI dataset search endpoint — backed by AWS RDS PostgreSQL (ecoinvent 3.12 cutoff).
Uses pg_trgm trigram index on activity_name for fast full-text search.
"""

from __future__ import annotations
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from core.db import get_db_cursor

router = APIRouter(prefix="/lci", tags=["LCI Data"])


@router.get("/search", response_model=List[dict])
async def search_lci(
    q: str = Query(..., min_length=2, description="Search query for material or process name"),
    category: Optional[str] = Query(None, description="Filter by ecoinvent category"),
    geography: Optional[str] = Query(None, description="Filter by geography code (e.g. 'GLO', 'RER', 'US')"),
    limit: int = Query(20, ge=1, le=100, description="Max results to return"),
    cursor=Depends(get_db_cursor),
):
    """
    Fast trigram-based search against the ecoinvent 3.12 LCI database in AWS RDS.
    Returns matching unit processes normalized for the frontend LCISearchResult type.
    """
    try:
        params: list = [f"%{q}%"]
        sql = """
            SELECT
                id,
                activity_name  AS name,
                activity_name  AS activity,
                geography,
                reference_year,
                data_quality_score,
                xml_file       AS source_file,
                elementary_exchanges,
                intermediate_exchanges
            FROM lci_database
            WHERE activity_name ILIKE %s
        """

        if geography:
            sql += " AND geography = %s"
            params.append(geography.upper())

        if category:
            # category not stored separately — filter by activity name pattern
            sql += " AND activity_name ILIKE %s"
            params.append(f"%{category}%")

        sql += f" ORDER BY activity_name LIMIT {int(limit)}"

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            d = dict(row)
            # Add a unit field — extract from elementary_exchanges if possible
            d["unit"] = "kg"
            d["gwp_factor"] = None
            # Derive GWP from elementary_exchanges if present
            try:
                import json
                exchanges = d.get("elementary_exchanges") or {}
                if isinstance(exchanges, str):
                    exchanges = json.loads(exchanges)
                gwp = 0.0
                for name_ex, ex_data in exchanges.items():
                    n = name_ex.lower()
                    amt = float(ex_data.get("amount", 0)) if isinstance(ex_data, dict) else float(ex_data)
                    if "carbon dioxide" in n or "co2" in n:
                        gwp += amt * 1.0
                    elif "methane" in n or "ch4" in n:
                        gwp += amt * 29.8
                    elif "dinitrogen monoxide" in n or "nitrous oxide" in n or "n2o" in n:
                        gwp += amt * 273.0
                if gwp > 0:
                    d["gwp_factor"] = round(gwp, 4)
            except Exception:
                pass
            results.append(d)

        return results

    except Exception as e:
        import structlog
        log = structlog.get_logger()
        log.error("LCI search failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/dataset/{dataset_id}", response_model=dict)
async def get_lci_dataset(
    dataset_id: str,
    cursor=Depends(get_db_cursor),
):
    """
    Retrieve full details (including elementary exchanges) for a specific LCI dataset by ID.
    """
    try:
        cursor.execute(
            """
            SELECT
                id,
                activity_name AS name,
                activity_name AS activity,
                geography,
                reference_year,
                data_quality_score,
                xml_file AS source_file,
                elementary_exchanges,
                intermediate_exchanges
            FROM lci_database
            WHERE id = %s
            """,
            (dataset_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")

        return dict(row)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lookup failed: {str(e)}")


@router.get("/stats", response_model=dict)
async def get_lci_stats(cursor=Depends(get_db_cursor)):
    """Return total dataset count and geography breakdown."""
    try:
        cursor.execute("SELECT COUNT(*) AS total FROM lci_database")
        total = dict(cursor.fetchone())["total"]

        cursor.execute(
            """
            SELECT geography, COUNT(*) AS count
            FROM lci_database
            GROUP BY geography
            ORDER BY count DESC
            LIMIT 15
            """
        )
        geo_breakdown = [dict(r) for r in cursor.fetchall()]

        return {"total_datasets": total, "geography_breakdown": geo_breakdown}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats failed: {str(e)}")
