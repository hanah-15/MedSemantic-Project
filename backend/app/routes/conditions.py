"""Sofiene: ConditionMedicale queries and ontology-backed editing."""

from fastapi import APIRouter, HTTPException, Path, Query, Response
from typing import Literal
from app.models.clinical import ConditionCreate, ConditionWrite
from app.services import clinical_editor

from app.services import fuseki
from app.services.medical_records import build_records
from sparql_queries.queries_condition_medicale import select_conditions

router = APIRouter(prefix='/api/conditions', tags=['Medical conditions'])


@router.get('')
def list_conditions(q: str = Query('', max_length=200),
                    category: Literal['EtatPhysiologique','EtatPathologique'] | None = None,
                    condition_type: str | None = Query(None, pattern=r'^[A-Za-z][A-Za-z0-9_]*$'),
                    severity: str | None = Query(None, max_length=200)):
    """Include instances of subclasses like Grossesse and InsuffisanceRenale."""
    try:
        return build_records(fuseki.query_select(select_conditions(q=q, category=category,
                            condition_type=condition_type, severity=severity)), 'conditions')
    except fuseki.FusekiUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get('/types')
def get_condition_types():
    return clinical_editor.condition_types()


@router.post('', status_code=201)
def create_condition(payload: ConditionCreate):
    clinical_editor.write_record(payload.id, payload, 'conditions', create=True)
    return get_condition(payload.id)


@router.get('/{condition_id}')
def get_condition(condition_id: str = Path(pattern=r'^[A-Za-z][A-Za-z0-9_]*$')):
    try:
        records = build_records(fuseki.query_select(select_conditions(condition_id)), 'conditions')
    except fuseki.FusekiUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not records:
        raise HTTPException(status_code=404, detail='Medical condition not found')
    return records[0]


@router.put('/{condition_id}')
def update_condition(payload: ConditionWrite, condition_id: str = Path(pattern=r'^[A-Za-z][A-Za-z0-9_]*$')):
    get_condition(condition_id)
    clinical_editor.write_record(condition_id, payload, 'conditions', create=False)
    return get_condition(condition_id)


@router.delete('/{condition_id}', status_code=204)
def delete_condition(condition_id: str = Path(pattern=r'^[A-Za-z][A-Za-z0-9_]*$')):
    get_condition(condition_id)
    clinical_editor.delete_record(condition_id)
    return Response(status_code=204)
