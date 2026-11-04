"""Sofiene: read-only ConditionMedicale endpoints."""

from fastapi import APIRouter, HTTPException, Path

from app.services import fuseki
from app.services.medical_records import build_records
from sparql_queries.queries_condition_medicale import select_conditions

router = APIRouter(prefix='/api/conditions', tags=['Medical conditions'])


@router.get('')
def list_conditions():
    """Include instances of subclasses like Grossesse and InsuffisanceRenale."""
    try:
        return build_records(fuseki.query_select(select_conditions()), 'conditions')
    except fuseki.FusekiUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get('/{condition_id}')
def get_condition(condition_id: str = Path(pattern=r'^[A-Za-z][A-Za-z0-9_]*$')):
    try:
        records = build_records(fuseki.query_select(select_conditions(condition_id)), 'conditions')
    except fuseki.FusekiUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not records:
        raise HTTPException(status_code=404, detail='Medical condition not found')
    return records[0]
