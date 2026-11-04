"""
Routes FastAPI pour les ResultatClinique (Efficacite, Securite, Tolerance).
Préfixe : /resultats
"""

from typing import Optional, List

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel

from app.fuseki_client import execute_sparql, extract_local_name, val
from sparql_queries.queries_resultat import (
    requete_lister_resultats,
    requete_detail_resultat,
    requete_resultats_par_type,
    requete_resultats_par_medicament,
    requete_stats_resultats,
)

router = APIRouter(prefix="/resultats", tags=["Résultats Cliniques"])

# ─────────────────────────────────────────────────────────────────────────────
# Modèles Pydantic
# ─────────────────────────────────────────────────────────────────────────────

class ResultatResume(BaseModel):
    """Résumé d'un résultat clinique."""
    iri: str
    id: str
    type_resultat: Optional[str] = None
    valeur: Optional[float] = None
    unite: Optional[str] = None
    etude_id: Optional[str] = None
    etude_iri: Optional[str] = None
    medicament_id: Optional[str] = None
    medicament_iri: Optional[str] = None


class ResultatDetail(ResultatResume):
    """Détail d'un résultat avec informations de l'étude associée."""
    type_etude: Optional[str] = None


class StatResultat(BaseModel):
    """Statistique par type de résultat."""
    type_resultat: str
    nombre_resultats: int


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _to_float(s: Optional[str]) -> Optional[float]:
    """Convertit une chaîne RDF en float."""
    if not s:
        return None
    try:
        from decimal import Decimal
        return float(Decimal(s))
    except (ValueError, TypeError):
        return None


def _binding_vers_resultat_resume(b: dict) -> ResultatResume:
    """Convertit un binding SPARQL en ResultatResume."""
    iri = val(b, "resultat")
    return ResultatResume(
        iri=iri,
        id=extract_local_name(iri),
        type_resultat=val(b, "typeResultat") or None,
        valeur=_to_float(val(b, "valeur")),
        unite=val(b, "unite") or None,
        etude_id=val(b, "etudeNom") or None,
        etude_iri=val(b, "etude") or None,
        medicament_id=val(b, "medicamentNom") or None,
        medicament_iri=val(b, "medicament") or None,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=List[ResultatResume],
    summary="Lister tous les résultats cliniques",
    description=(
        "Retourne tous les résultats cliniques (Efficacite, Securite, Tolerance) "
        "avec leur type précis, leur valeur et l'étude associée."
    ),
)
def lister_resultats():
    """Liste tous les résultats cliniques de l'ontologie."""
    bindings = execute_sparql(requete_lister_resultats())
    vus = {}
    for b in bindings:
        iri = val(b, "resultat")
        if iri and iri not in vus:
            vus[iri] = _binding_vers_resultat_resume(b)
    return list(vus.values())


@router.get(
    "/stats",
    response_model=List[StatResultat],
    summary="Statistiques des résultats cliniques",
    description="Retourne le nombre de résultats par type (Efficacite, Securite, Tolerance).",
)
def stats_resultats():
    """Statistiques agrégées par type de résultat."""
    bindings = execute_sparql(requete_stats_resultats())
    return [
        StatResultat(
            type_resultat=val(b, "typeResultat"),
            nombre_resultats=int(val(b, "nombreResultats") or 0),
        )
        for b in bindings
        if val(b, "typeResultat")
    ]


@router.get(
    "/type/{type_resultat}",
    response_model=List[ResultatResume],
    summary="Résultats par type",
    description=(
        "Retourne les résultats d'un type donné : 'efficacite', 'securite' ou 'tolerance'. "
        "Insensible à la casse. 'securite' inclut aussi les Tolerance (sous-classe)."
    ),
)
def resultats_par_type(
    type_resultat: str = Path(
        ...,
        description="Type de résultat : 'efficacite', 'securite' ou 'tolerance'",
        examples=["efficacite"],
    )
):
    """Filtre les résultats par type."""
    bindings = execute_sparql(requete_resultats_par_type(type_resultat))
    return [_binding_vers_resultat_resume(b) for b in bindings if val(b, "resultat")]


@router.get(
    "/medicament/{medicament_id}",
    response_model=List[ResultatResume],
    summary="Résultats par médicament",
    description=(
        "Retourne les résultats cliniques liés à un médicament, "
        "via la chaîne Medicament → EtudeClinique → ResultatClinique."
    ),
)
def resultats_par_medicament(
    medicament_id: str = Path(
        ...,
        description="Identifiant court du médicament (ex: 'Glucophage')",
        examples=["Glucophage"],
    )
):
    """Résultats liés à un médicament (via l'étude intermédiaire)."""
    bindings = execute_sparql(requete_resultats_par_medicament(medicament_id))
    if not bindings:
        raise HTTPException(
            status_code=404,
            detail=f"Aucun résultat trouvé pour le médicament '{medicament_id}'.",
        )
    return [_binding_vers_resultat_resume(b) for b in bindings if val(b, "resultat")]


@router.get(
    "/{resultat_id}",
    response_model=ResultatDetail,
    summary="Détail d'un résultat clinique",
    description="Retourne le détail complet d'un résultat avec l'étude et le médicament associés.",
)
def detail_resultat(
    resultat_id: str = Path(
        ...,
        description="Identifiant court du résultat (ex: 'Res_Efficacite_Glucophage')",
        examples=["Res_Efficacite_Glucophage"],
    )
):
    """Détail d'un résultat clinique par identifiant."""
    bindings = execute_sparql(requete_detail_resultat(resultat_id))
    if not bindings:
        raise HTTPException(
            status_code=404,
            detail=f"Résultat '{resultat_id}' introuvable.",
        )

    premier = bindings[0]
    iri = val(premier, "resultat")
    if not iri:
        raise HTTPException(
            status_code=404,
            detail=f"Résultat '{resultat_id}' introuvable.",
        )

    return ResultatDetail(
        iri=iri,
        id=extract_local_name(iri),
        type_resultat=val(premier, "typeResultat") or None,
        valeur=_to_float(val(premier, "valeur")),
        unite=val(premier, "unite") or None,
        etude_id=val(premier, "etudeNom") or None,
        etude_iri=val(premier, "etude") or None,
        type_etude=val(premier, "typeEtude") or None,
        medicament_id=val(premier, "medicamentNom") or None,
        medicament_iri=val(premier, "medicament") or None,
    )
