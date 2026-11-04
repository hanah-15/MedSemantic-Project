"""Sofiene: Patient queries and ontology-backed editing."""

from fastapi import APIRouter, HTTPException, Path, Query, Response
from typing import Literal
from app.models.clinical import PatientCreate, PatientWrite
from app.services import clinical_editor

from app.services import fuseki
from app.services.medical_records import build_records
from sparql_queries.queries_patient import select_patients

router = APIRouter(prefix='/api/patients', tags=['Patients'])


@router.get('')
def list_patients(q: str = Query('', max_length=200), min_age: int | None = Query(None, ge=0),
                  max_age: int | None = Query(None, ge=0),
                  age_category: Literal['Enfant','Adulte','PersonneAgee'] | None = None,
                  sexe: str | None = Query(None, max_length=40),
                  condition_id: str | None = Query(None, pattern=r'^[A-Za-z][A-Za-z0-9_]*$')):
    """Return patients with age, sex and explicit medical relationships."""
    if min_age is not None and max_age is not None and min_age > max_age:
        raise HTTPException(422, 'Minimum age must not exceed maximum age.')
    try:
        return build_records(fuseki.query_select(select_patients(q=q, min_age=min_age, max_age=max_age,
                            age_category=age_category, sexe=sexe, condition_id=condition_id)), 'patients')
    except fuseki.FusekiUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get('/options')
def get_patient_options():
    return clinical_editor.patient_options()


@router.post('', status_code=201)
def create_patient(payload: PatientCreate):
    clinical_editor.write_record(payload.id, payload, 'patients', create=True)
    return get_patient(payload.id)


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


@router.put('/{patient_id}')
def update_patient(payload: PatientWrite, patient_id: str = Path(pattern=r'^[A-Za-z][A-Za-z0-9_]*$')):
    get_patient(patient_id)
    clinical_editor.write_record(patient_id, payload, 'patients', create=False)
    return get_patient(patient_id)


@router.delete('/{patient_id}', status_code=204)
def delete_patient(patient_id: str = Path(pattern=r'^[A-Za-z][A-Za-z0-9_]*$')):
    get_patient(patient_id)
    clinical_editor.delete_record(patient_id)
    return Response(status_code=204)
