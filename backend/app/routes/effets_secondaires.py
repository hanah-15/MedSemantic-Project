"""
Routes FastAPI pour la classe EffetSecondaire et ses sous-classes
(EffetDigestif, EffetNeurologique, EffetCardiovasculaire, EffetAllergique).
Module développé par Oussema.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Path, Query

from app.fuseki_client import execute_sparql, extract_local_name, val
from app.models.effet_secondaire import (
    EffetSecondaireResume,
    EffetSecondaireDetail,
    EffetSecondaireStats,
)
from sparql_queries.queries_effet_secondaire import (
    requete_lister_effets_secondaires,
    requete_detail_effet_secondaire,
    requete_effets_par_type,
    requete_effets_par_gravite,
    requete_effets_par_frequence,
    requete_effets_par_medicament,
    requete_effets_par_symptome,
    requete_stats_effets_secondaires,
)

router = APIRouter(prefix="/effets-secondaires", tags=["Effets Secondaires"])


def _agreger_effets(bindings: list) -> List[EffetSecondaireResume]:
    """Agrège les lignes SPARQL par identifiant d'effet secondaire."""
    effets_map = {}
    for b in bindings:
        uri = val(b, "effet")
        if not uri:
            continue
        eid = extract_local_name(uri)
        if eid not in effets_map:
            effets_map[eid] = {
                "iri": uri,
                "id": eid,
                "type_effet": val(b, "typeEffet") or None,
                "label": val(b, "label") or None,
                "frequence": val(b, "frequence") or None,
                "gravite": val(b, "gravite") or None,
                "symptome_id": val(b, "symptomeNom") or (extract_local_name(val(b, "symptome")) if val(b, "symptome") else None),
                "symptome_iri": val(b, "symptome") or None,
                "medicaments_lies": set(),
            }
        med = val(b, "medicamentNom") or (extract_local_name(val(b, "medicament")) if val(b, "medicament") else None)
        if med:
            effets_map[eid]["medicaments_lies"].add(med)

    return [
        EffetSecondaireResume(
            iri=data["iri"],
            id=data["id"],
            type_effet=data["type_effet"],
            label=data["label"],
            frequence=data["frequence"],
            gravite=data["gravite"],
            symptome_id=data["symptome_id"],
            symptome_iri=data["symptome_iri"],
            medicaments_lies=sorted(list(data["medicaments_lies"])),
        )
        for data in effets_map.values()
    ]


@router.get("", response_model=List[EffetSecondaireResume])
@router.get("/", response_model=List[EffetSecondaireResume])
def lister_effets_secondaires(
    type_effet: Optional[str] = Query(None, description="Filtrer par type (ex: EffetDigestif, cardiovasculaire)"),
    gravite: Optional[str] = Query(None, description="Filtrer par gravité (légère, modérée, sévère)"),
    frequence: Optional[str] = Query(None, description="Filtrer par fréquence (fréquent, rare)"),
):
    """
    Retourne la liste des effets secondaires avec filtres optionnels.
    """
    if type_effet:
        bindings = execute_sparql(requete_effets_par_type(type_effet))
    elif gravite:
        bindings = execute_sparql(requete_effets_par_gravite(gravite))
    elif frequence:
        bindings = execute_sparql(requete_effets_par_frequence(frequence))
    else:
        bindings = execute_sparql(requete_lister_effets_secondaires())
    return _agreger_effets(bindings)


@router.get("/stats", response_model=List[EffetSecondaireStats])
def get_stats_effets():
    """
    Retourne les statistiques de distribution des effets secondaires par sous-classe.
    """
    bindings = execute_sparql(requete_stats_effets_secondaires())
    return [
        EffetSecondaireStats(
            type_effet=val(b, "typeEffet"),
            total=int(val(b, "total")) if val(b, "total") else 0,
        )
        for b in bindings
    ]


@router.get("/medicament/{medicament_id}", response_model=List[EffetSecondaireResume])
def get_effets_par_medicament(
    medicament_id: str = Path(..., description="Identifiant du médicament (ex: Glucophage, Amlor)"),
):
    """
    Retourne les effets secondaires provoqués par un médicament spécifique.
    """
    bindings = execute_sparql(requete_effets_par_medicament(medicament_id))
    return _agreger_effets(bindings)


@router.get("/symptome/{symptome_id}", response_model=List[EffetSecondaireResume])
def get_effets_par_symptome(
    symptome_id: str = Path(..., description="Identifiant du symptôme (ex: Nausee)"),
):
    """
    Retourne les effets secondaires manifestant un symptôme donné.
    """
    bindings = execute_sparql(requete_effets_par_symptome(symptome_id))
    return _agreger_effets(bindings)


@router.get("/type/{type_effet}", response_model=List[EffetSecondaireResume])
def get_effets_par_type(
    type_effet: str = Path(..., description="Sous-classe (ex: EffetDigestif, allergique)"),
):
    """
    Retourne les effets secondaires d'un type précis.
    """
    bindings = execute_sparql(requete_effets_par_type(type_effet))
    return _agreger_effets(bindings)


@router.get("/gravite/{gravite}", response_model=List[EffetSecondaireResume])
def get_effets_par_gravite(
    gravite: str = Path(..., description="Gravité recherchée (ex: légère, modérée, sévère)"),
):
    """
    Retourne les effets secondaires filtrés par gravité.
    """
    bindings = execute_sparql(requete_effets_par_gravite(gravite))
    return _agreger_effets(bindings)


@router.get("/frequence/{frequence}", response_model=List[EffetSecondaireResume])
def get_effets_par_frequence(
    frequence: str = Path(..., description="Fréquence recherchée (ex: fréquent, rare)"),
):
    """
    Retourne les effets secondaires filtrés par niveau de fréquence.
    """
    bindings = execute_sparql(requete_effets_par_frequence(frequence))
    return _agreger_effets(bindings)


@router.get("/{effet_id}", response_model=EffetSecondaireDetail)
def get_detail_effet_secondaire(
    effet_id: str = Path(..., description="Identifiant court de l'effet (ex: TroublesGastriques)"),
):
    """
    Retourne le détail complet d'un effet secondaire (type, fréquence, gravité, symptômes, médicaments).
    """
    bindings = execute_sparql(requete_detail_effet_secondaire(effet_id))
    if not bindings:
        raise HTTPException(
            status_code=404,
            detail=f"Effet secondaire '{effet_id}' introuvable dans l'ontologie.",
        )

    first = bindings[0]
    uri = val(first, "effet")
    type_effet = val(first, "typeEffet") or None
    label = val(first, "label") or None
    frequence = val(first, "frequence") or None
    gravite = val(first, "gravite") or None

    symptomes = {}
    medicaments = {}

    for b in bindings:
        sym_uri = val(b, "symptome")
        if sym_uri:
            sym_id = val(b, "symptomeNom") or extract_local_name(sym_uri)
            symptomes[sym_id] = {"id": sym_id, "iri": sym_uri}
        med_uri = val(b, "medicament")
        if med_uri:
            med_id = val(b, "medicamentNom") or extract_local_name(med_uri)
            medicaments[med_id] = {"id": med_id, "iri": med_uri}

    return EffetSecondaireDetail(
        iri=uri,
        id=effet_id,
        type_effet=type_effet,
        label=label,
        frequence=frequence,
        gravite=gravite,
        symptomes=list(symptomes.values()),
        medicaments=list(medicaments.values()),
    )
