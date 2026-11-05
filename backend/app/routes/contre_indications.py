"""
Routes FastAPI pour la classe ContreIndication et ses sous-classes
(ContreIndicationAbsolue, ContreIndicationRelative).
Module développé par Oussema.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Path, Query

from app.fuseki_client import execute_sparql, extract_local_name, val
from app.models.contre_indication import (
    ContreIndicationResume,
    ContreIndicationDetail,
    ContreIndicationStats,
    AlerteContreIndication,
)
from sparql_queries.queries_contre_indication import (
    requete_lister_contre_indications,
    requete_detail_contre_indication,
    requete_contre_indications_par_type,
    requete_contre_indications_par_medicament,
    requete_contre_indications_par_condition,
    requete_verifier_contre_indication,
    requete_stats_contre_indications,
)

router = APIRouter(prefix="/contre-indications", tags=["Contre-indications"])


def _agreger_contre_indications(bindings: list) -> List[ContreIndicationResume]:
    """Agrège les lignes SPARQL par identifiant de contre-indication."""
    ci_map = {}
    for b in bindings:
        uri = val(b, "ci")
        if not uri:
            continue
        ci_id = extract_local_name(uri)
        if ci_id not in ci_map:
            ci_map[ci_id] = {
                "iri": uri,
                "id": ci_id,
                "type_ci": val(b, "typeCI") or None,
                "label": val(b, "label") or None,
                "description": val(b, "description") or None,
                "condition_id": val(b, "conditionNom") or (extract_local_name(val(b, "condition")) if val(b, "condition") else None),
                "condition_iri": val(b, "condition") or None,
                "medicaments_lies": set(),
            }
        med = val(b, "medicamentNom") or (extract_local_name(val(b, "medicament")) if val(b, "medicament") else None)
        if med:
            ci_map[ci_id]["medicaments_lies"].add(med)

    return [
        ContreIndicationResume(
            iri=data["iri"],
            id=data["id"],
            type_ci=data["type_ci"],
            label=data["label"],
            description=data["description"],
            condition_id=data["condition_id"],
            condition_iri=data["condition_iri"],
            medicaments_lies=sorted(list(data["medicaments_lies"])),
        )
        for data in ci_map.values()
    ]


@router.get("", response_model=List[ContreIndicationResume])
@router.get("/", response_model=List[ContreIndicationResume])
def lister_contre_indications(
    type_ci: Optional[str] = Query(None, description="Filtrer par type (ex: absolue, relative)"),
):
    """
    Retourne la liste de toutes les contre-indications (avec filtre optionnel par type).
    """
    if type_ci:
        bindings = execute_sparql(requete_contre_indications_par_type(type_ci))
    else:
        bindings = execute_sparql(requete_lister_contre_indications())
    return _agreger_contre_indications(bindings)


@router.get("/stats", response_model=List[ContreIndicationStats])
def get_stats_contre_indications():
    """
    Retourne la répartition des contre-indications par type (absolue vs relative).
    """
    bindings = execute_sparql(requete_stats_contre_indications())
    return [
        ContreIndicationStats(
            type_ci=val(b, "typeCI"),
            total=int(val(b, "total")) if val(b, "total") else 0,
        )
        for b in bindings
    ]


@router.get("/verifier/{patient_id}/{medicament_id}", response_model=AlerteContreIndication)
def verifier_securite_patient_medicament(
    patient_id: str = Path(..., description="Identifiant du patient (ex: Patient_Sarah)"),
    medicament_id: str = Path(..., description="Identifiant du médicament (ex: Advil)"),
):
    """
    Vérifie si un médicament présente des contre-indications pour un patient donné,
    en croisant les pathologies ou conditions actives du patient avec l'ontologie.
    """
    bindings = execute_sparql(requete_verifier_contre_indication(patient_id, medicament_id))

    alertes = []
    for b in bindings:
        alertes.append({
            "contre_indication_id": extract_local_name(val(b, "ci")),
            "type_ci": val(b, "typeCI"),
            "description": val(b, "description"),
            "condition_concernee": val(b, "conditionNom"),
            "motif": val(b, "raison"),
        })

    return AlerteContreIndication(
        est_contre_indique=len(alertes) > 0,
        patient_id=patient_id,
        medicament_id=medicament_id,
        alertes=alertes,
    )


@router.get("/medicament/{medicament_id}", response_model=List[ContreIndicationResume])
def get_contre_indications_par_medicament(
    medicament_id: str = Path(..., description="Identifiant du médicament (ex: Advil, Glucophage, Doliprane)"),
):
    """
    Retourne les contre-indications spécifiquement associées à un médicament.
    """
    bindings = execute_sparql(requete_contre_indications_par_medicament(medicament_id))
    return _agreger_contre_indications(bindings)


@router.get("/condition/{condition_id}", response_model=List[ContreIndicationResume])
def get_contre_indications_par_condition(
    condition_id: str = Path(..., description="Identifiant de la condition ou maladie (ex: Grossesse_T3, InsufRenaleSevere)"),
):
    """
    Retourne les contre-indications liées à une condition médicale ou maladie donnée.
    """
    bindings = execute_sparql(requete_contre_indications_par_condition(condition_id))
    return _agreger_contre_indications(bindings)


@router.get("/type/{type_ci}", response_model=List[ContreIndicationResume])
def get_contre_indications_par_type(
    type_ci: str = Path(..., description="Type (absolue ou relative)"),
):
    """
    Retourne les contre-indications filtrées par type (ContreIndicationAbsolue ou ContreIndicationRelative).
    """
    bindings = execute_sparql(requete_contre_indications_par_type(type_ci))
    return _agreger_contre_indications(bindings)


@router.get("/{ci_id}", response_model=ContreIndicationDetail)
def get_detail_contre_indication(
    ci_id: str = Path(..., description="Identifiant court de la contre-indication (ex: CI_Ibuprofene_Grossesse)"),
):
    """
    Retourne le détail complet d'une contre-indication (type, description, conditions et médicaments liés).
    """
    bindings = execute_sparql(requete_detail_contre_indication(ci_id))
    if not bindings:
        raise HTTPException(
            status_code=404,
            detail=f"Contre-indication '{ci_id}' introuvable dans l'ontologie.",
        )

    first = bindings[0]
    uri = val(first, "ci")
    type_ci = val(first, "typeCI") or None
    label = val(first, "label") or None
    description = val(first, "description") or None

    conditions = {}
    medicaments = {}

    for b in bindings:
        cond_uri = val(b, "condition")
        if cond_uri:
            cond_id = val(b, "conditionNom") or extract_local_name(cond_uri)
            conditions[cond_id] = {"id": cond_id, "iri": cond_uri}
        med_uri = val(b, "medicament")
        if med_uri:
            med_id = val(b, "medicamentNom") or extract_local_name(med_uri)
            medicaments[med_id] = {"id": med_id, "iri": med_uri}

    return ContreIndicationDetail(
        iri=uri,
        id=ci_id,
        type_ci=type_ci,
        label=label,
        description=description,
        conditions_concernees=list(conditions.values()),
        medicaments_concernes=list(medicaments.values()),
    )
