"""Sofiene: read-only Patient endpoints."""

from fastapi import APIRouter, HTTPException, Path

from app.services import fuseki
from app.services.medical_records import build_records
from sparql_queries.queries_patient import select_patients

router = APIRouter(prefix='/api/patients', tags=['Patients'])


@router.get('')
def list_patients():
    """Return patients with age, sex and explicit medical relationships."""
    try:
        return build_records(fuseki.query_select(select_patients()), 'patients')
    except fuseki.FusekiUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get('/{patient_id}')
def get_patient(patient_id: str = Path(pattern=r'^[A-Za-z][A-Za-z0-9_]*$')):
    """Return one patient by OWL identifier (e.g. Patient_Karim)."""
    try:
        records = build_records(fuseki.query_select(select_patients(patient_id)), 'patients')
    except fuseki.FusekiUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not records:
        raise HTTPException(status_code=404, detail='Patient not found')
    return records[0]


@router.get('/{patient_id}/conditions')
def get_patient_conditions(patient_id: str = Path(pattern=r'^[A-Za-z][A-Za-z0-9_]*$')):
    """Return explicit aPourCondition target identifiers (possibly empty)."""
    patient = get_patient(patient_id)
    return [link['target'] for link in patient['relations'] if link['predicate'] == 'aPourCondition']
