"""
Routes FastAPI pour les EtudeClinique (EssaiClinique, EtudeObservationnelle).
Préfixe : /etudes
"""

from typing import Optional, List
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel

from app.fuseki_client import execute_sparql, extract_local_name, val
from sparql_queries.queries_etude import (
    requete_lister_etudes,
    requete_detail_etude,
    requete_etudes_par_type,
    requete_etudes_par_medicament,
    requete_etudes_par_maladie,
    requete_etudes_par_phase,
    requete_etudes_par_annee,
    requete_etudes_min_participants,
    requete_etudes_comparatives,
    requete_etudes_sans_resultat,
    requete_stats_etudes,
)

router = APIRouter(prefix="/etudes", tags=["Études Cliniques"])

# ─────────────────────────────────────────────────────────────────────────────
# Modèles Pydantic
# ─────────────────────────────────────────────────────────────────────────────

class ResultatResume(BaseModel):
    """Résumé d'un résultat clinique lié à une étude."""
    iri: str
    id: str
    type_resultat: Optional[str] = None
    valeur: Optional[float] = None
    unite: Optional[str] = None


class EtudeResume(BaseModel):
    """Résumé d'une étude clinique (liste)."""
    iri: str
    id: str
    type_etude: Optional[str] = None
    medicament_id: Optional[str] = None
    medicament_iri: Optional[str] = None
    maladie_id: Optional[str] = None
    maladie_iri: Optional[str] = None
    phase: Optional[int] = None
    annee: Optional[int] = None
    participants: Optional[int] = None
    comparative: Optional[bool] = None


class EtudeDetail(EtudeResume):
    """Détail complet d'une étude avec ses résultats."""
    resultats: List[ResultatResume] = []


class StatEtude(BaseModel):
    """Statistiques par type d'étude."""
    type_etude: str
    nombre_etudes: int
    moyenne_participants: Optional[float] = None


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de conversion
# ─────────────────────────────────────────────────────────────────────────────

def _to_int(s: Optional[str]) -> Optional[int]:
    """Convertit une chaîne RDF en int, ou None si absent."""
    if not s:
        return None
    try:
        return int(s)
    except (ValueError, TypeError):
        return None


def _to_float(s: Optional[str]) -> Optional[float]:
    """Convertit une chaîne RDF en float, ou None si absent."""
    if not s:
        return None
    try:
        return float(Decimal(s))
    except (ValueError, TypeError):
        return None


def _to_bool(s: Optional[str]) -> Optional[bool]:
    """Convertit une chaîne RDF ('true'/'false') en bool, ou None si absente."""
    if not s:
        return None
    low = s.strip().lower()
    if low in ("true", "1"):
        return True
    if low in ("false", "0"):
        return False
    return None


def _binding_vers_etude_resume(b: dict) -> EtudeResume:
    """Convertit un binding SPARQL en EtudeResume."""
    iri = val(b, "etude")
    return EtudeResume(
        iri=iri,
        id=extract_local_name(iri),
        type_etude=val(b, "typeEtude") or None,
        medicament_id=val(b, "medicamentNom") or None,
        medicament_iri=val(b, "medicament") or None,
        maladie_id=val(b, "maladieNom") or None,
        maladie_iri=val(b, "maladie") or None,
        phase=_to_int(val(b, "phase")),
        annee=_to_int(val(b, "annee")),
        participants=_to_int(val(b, "participants")),
        comparative=_to_bool(val(b, "comparative")),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=List[EtudeResume],
    summary="Lister toutes les études cliniques",
    description=(
        "Retourne l'ensemble des études cliniques (EssaiClinique et EtudeObservationnelle) "
        "avec leurs attributs. Les champs optionnels (phase, maladie, résultats) peuvent être "
        "absents (monde ouvert)."
    ),
)
def lister_etudes():
    """Liste toutes les études cliniques de l'ontologie."""
    bindings = execute_sparql(requete_lister_etudes())
    # Dédupliquer par IRI (un binding par combinaison)
    vus = {}
    for b in bindings:
        iri = val(b, "etude")
        if iri and iri not in vus:
            vus[iri] = _binding_vers_etude_resume(b)
    return list(vus.values())


@router.get(
    "/stats",
    response_model=List[StatEtude],
    summary="Statistiques des études cliniques",
    description="Retourne le nombre d'études et la moyenne des participants par type d'étude.",
)
def stats_etudes():
    """Statistiques agrégées par type d'étude (COUNT, AVG)."""
    bindings = execute_sparql(requete_stats_etudes())
    resultats = []
    for b in bindings:
        type_etude = val(b, "typeEtude")
        if not type_etude:
            continue
        resultats.append(StatEtude(
            type_etude=type_etude,
            nombre_etudes=_to_int(val(b, "nombreEtudes")) or 0,
            moyenne_participants=_to_float(val(b, "moyenneParticipants")),
        ))
    return resultats


@router.get(
    "/sans-resultat",
    response_model=List[EtudeResume],
    summary="Études sans résultat clinique",
    description=(
        "Retourne les études qui n'ont aucun résultat clinique associé "
        "(ex : Etude_Paracetamol_Obs)."
    ),
)
def etudes_sans_resultat():
    """Études n'ayant aucun :aPourResultat."""
    bindings = execute_sparql(requete_etudes_sans_resultat())
    return [_binding_vers_etude_resume(b) for b in bindings if val(b, "etude")]


@router.get(
    "/annee/recherche",
    response_model=List[EtudeResume],
    summary="Études par plage d'années",
    description="Filtre les études par année de publication (borne min et/ou max).",
    include_in_schema=True,
)
def etudes_par_annee(
    annee_min: Optional[int] = Query(None, description="Année minimale (incluse)", examples=[2020]),
    annee_max: Optional[int] = Query(None, description="Année maximale (incluse)", examples=[2024]),
):
    """Filtre les études par plage d'années de publication."""
    if annee_min is None and annee_max is None:
        raise HTTPException(status_code=422, detail="Fournissez au moins annee_min ou annee_max.")
    bindings = execute_sparql(requete_etudes_par_annee(annee_min, annee_max))
    return [_binding_vers_etude_resume(b) for b in bindings if val(b, "etude")]


@router.get(
    "/participants/minimum",
    response_model=List[EtudeResume],
    summary="Études avec un minimum de participants",
    description="Retourne les études avec au moins N participants.",
)
def etudes_min_participants(
    n: int = Query(..., description="Nombre minimal de participants", ge=1, examples=[500]),
):
    """Filtre par nombre minimal de participants."""
    bindings = execute_sparql(requete_etudes_min_participants(n))
    return [_binding_vers_etude_resume(b) for b in bindings if val(b, "etude")]


@router.get(
    "/comparatives/liste",
    response_model=List[EtudeResume],
    summary="Études comparatives uniquement",
    description="Retourne les études dont estComparative = true.",
)
def etudes_comparatives():
    """Filtre les études comparatives."""
    bindings = execute_sparql(requete_etudes_comparatives())
    return [_binding_vers_etude_resume(b) for b in bindings if val(b, "etude")]


@router.get(
    "/type/{type_etude}",
    response_model=List[EtudeResume],
    summary="Filtrer les études par type",
    description="Retourne les études d'un type précis : 'EssaiClinique' ou 'EtudeObservationnelle'.",
)
def etudes_par_type(
    type_etude: str = Path(
        ...,
        description="Type d'étude : 'EssaiClinique' ou 'EtudeObservationnelle'",
        examples=["EssaiClinique"],
    )
):
    """Filtre les études par sous-classe."""
    bindings = execute_sparql(requete_etudes_par_type(type_etude))
    return [_binding_vers_etude_resume(b) for b in bindings if val(b, "etude")]


@router.get(
    "/medicament/{medicament_id}",
    response_model=List[EtudeResume],
    summary="Études par médicament",
    description="Retourne les études qui testent le médicament identifié (via :testeMedicament).",
)
def etudes_par_medicament(
    medicament_id: str = Path(
        ...,
        description="Identifiant court du médicament (ex: 'Glucophage')",
        examples=["Glucophage"],
    )
):
    """Études liées à un médicament donné."""
    bindings = execute_sparql(requete_etudes_par_medicament(medicament_id))
    if not bindings:
        raise HTTPException(status_code=404, detail=f"Aucune étude trouvée pour le médicament '{medicament_id}'.")
    return [_binding_vers_etude_resume(b) for b in bindings if val(b, "etude")]


@router.get(
    "/maladie/{maladie_id}",
    response_model=List[EtudeResume],
    summary="Études par maladie",
    description="Retourne les études portant sur la maladie identifiée (via :porteSurMaladie).",
)
def etudes_par_maladie(
    maladie_id: str = Path(
        ...,
        description="Identifiant court de la maladie (ex: 'DiabeteType2')",
        examples=["DiabeteType2"],
    )
):
    """Études liées à une maladie donnée."""
    bindings = execute_sparql(requete_etudes_par_maladie(maladie_id))
    if not bindings:
        raise HTTPException(status_code=404, detail=f"Aucune étude trouvée pour la maladie '{maladie_id}'.")
    return [_binding_vers_etude_resume(b) for b in bindings if val(b, "etude")]


@router.get(
    "/phase/{phase}",
    response_model=List[EtudeResume],
    summary="Essais cliniques par phase",
    description="Retourne les essais cliniques d'une phase donnée (ex: phase 3).",
)
def etudes_par_phase(
    phase: int = Path(
        ...,
        description="Numéro de phase (1, 2, 3 ou 4)",
        ge=1,
        le=4,
        examples=[3],
    )
):
    """Filtre les EssaiClinique par phaseEssai."""
    bindings = execute_sparql(requete_etudes_par_phase(phase))
    if not bindings:
        raise HTTPException(status_code=404, detail=f"Aucun essai clinique de phase {phase} trouvé.")
    return [_binding_vers_etude_resume(b) for b in bindings if val(b, "etude")]


@router.get(
    "/{etude_id}",
    response_model=EtudeDetail,
    summary="Détail d'une étude clinique",
    description=(
        "Retourne le détail complet d'une étude par son identifiant court, "
        "incluant tous ses résultats cliniques."
    ),
)
def detail_etude(
    etude_id: str = Path(
        ...,
        description="Identifiant court de l'étude (ex: 'Essai_Metformine_2024')",
        examples=["Essai_Metformine_2024"],
    )
):
    """Détail d'une étude avec ses résultats."""
    bindings = execute_sparql(requete_detail_etude(etude_id))
    if not bindings:
        raise HTTPException(status_code=404, detail=f"Étude '{etude_id}' introuvable.")

    # Construire le détail à partir du premier binding
    premier = bindings[0]
    iri = val(premier, "etude")
    if not iri:
        raise HTTPException(status_code=404, detail=f"Étude '{etude_id}' introuvable.")

    detail = EtudeDetail(
        iri=iri,
        id=extract_local_name(iri),
        type_etude=val(premier, "typeEtude") or None,
        medicament_id=val(premier, "medicamentNom") or None,
        medicament_iri=val(premier, "medicament") or None,
        maladie_id=val(premier, "maladieNom") or None,
        maladie_iri=val(premier, "maladie") or None,
        phase=_to_int(val(premier, "phase")),
        annee=_to_int(val(premier, "annee")),
        participants=_to_int(val(premier, "participants")),
        comparative=_to_bool(val(premier, "comparative")),
    )

    # Collecter les résultats (un binding par résultat)
    resultats_vus = {}
    for b in bindings:
        res_iri = val(b, "resultat")
        if res_iri and res_iri not in resultats_vus:
            resultats_vus[res_iri] = ResultatResume(
                iri=res_iri,
                id=extract_local_name(res_iri),
                type_resultat=val(b, "typeResultat") or None,
                valeur=_to_float(val(b, "valeur")),
                unite=val(b, "unite") or None,
            )
    detail.resultats = list(resultats_vus.values())
    return detail
