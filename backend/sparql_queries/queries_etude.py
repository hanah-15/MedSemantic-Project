"""
Requêtes SPARQL pour la classe EtudeClinique et ses sous-classes
(EssaiClinique, EtudeObservationnelle).

Toutes les fonctions retournent une chaîne SPARQL prête à l'emploi.
Les paramètres sont sécurisés (jamais de concaténation directe d'entrée brute).
"""

import re
from typing import Optional
from fastapi import HTTPException
from app.fuseki_client import PREFIXES

# ─────────────────────────────────────────────────────────────────────────────
# Validation des paramètres
# ─────────────────────────────────────────────────────────────────────────────

_ID_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


def _valider_id(valeur: str, nom: str = "id") -> str:
    """
    Valide qu'un identifiant ne contient que des caractères alphanumériques ou '_'.
    Lève HTTP 422 si invalide.
    """
    if not _ID_PATTERN.match(valeur):
        raise HTTPException(
            status_code=422,
            detail=(
                f"Paramètre '{nom}' invalide : '{valeur}'. "
                "Seuls les caractères A-Z, a-z, 0-9 et _ sont autorisés."
            ),
        )
    return valeur


# ─────────────────────────────────────────────────────────────────────────────
# 1. Lister toutes les études
# ─────────────────────────────────────────────────────────────────────────────

def requete_lister_etudes() -> str:
    """
    Retourne toutes les études cliniques (EssaiClinique et EtudeObservationnelle)
    avec leurs attributs optionnels (phase, maladie, résultats).

    Utilise OPTIONAL pour ne perdre aucune étude même si certaines données manquent
    (ex: Etude_Paracetamol_Obs n'a ni phase ni maladie ni résultat).
    """
    return PREFIXES + """
SELECT DISTINCT
    ?etude ?typeEtude
    ?medicament ?medicamentNom
    ?maladie ?maladieNom
    ?phase ?annee ?participants ?comparative
WHERE {
    # Inclut EssaiClinique et EtudeObservationnelle via rdfs:subClassOf*
    ?sousClasse rdfs:subClassOf* :EtudeClinique .
    ?etude a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeEtude)

    OPTIONAL {
        ?etude :testeMedicament ?medicament .
        BIND(REPLACE(STR(?medicament), ".*#", "") AS ?medicamentNom)
    }
    OPTIONAL {
        ?etude :porteSurMaladie ?maladie .
        BIND(REPLACE(STR(?maladie), ".*#", "") AS ?maladieNom)
    }
    OPTIONAL { ?etude :phaseEssai ?phase . }
    OPTIONAL { ?etude :anneePublication ?annee . }
    OPTIONAL { ?etude :nombreParticipants ?participants . }
    OPTIONAL { ?etude :estComparative ?comparative . }
}
ORDER BY ?typeEtude ?etude
"""


# ─────────────────────────────────────────────────────────────────────────────
# 2. Détail d'une étude par identifiant (avec ses résultats)
# ─────────────────────────────────────────────────────────────────────────────

def requete_detail_etude(etude_id: str) -> str:
    """
    Retourne le détail complet d'une étude par son identifiant court,
    incluant les résultats (valeur, unité, type précis).

    :param etude_id: Identifiant court validé (ex: 'Essai_Metformine_2024').
    """
    _valider_id(etude_id, "etude_id")
    return PREFIXES + f"""
SELECT DISTINCT
    ?etude ?typeEtude
    ?medicament ?medicamentNom
    ?maladie ?maladieNom
    ?phase ?annee ?participants ?comparative
    ?resultat ?typeResultat ?valeur ?unite
WHERE {{
    BIND(:{etude_id} AS ?etude)
    ?sousClasse rdfs:subClassOf* :EtudeClinique .
    ?etude a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeEtude)

    OPTIONAL {{
        ?etude :testeMedicament ?medicament .
        BIND(REPLACE(STR(?medicament), ".*#", "") AS ?medicamentNom)
    }}
    OPTIONAL {{
        ?etude :porteSurMaladie ?maladie .
        BIND(REPLACE(STR(?maladie), ".*#", "") AS ?maladieNom)
    }}
    OPTIONAL {{ ?etude :phaseEssai ?phase . }}
    OPTIONAL {{ ?etude :anneePublication ?annee . }}
    OPTIONAL {{ ?etude :nombreParticipants ?participants . }}
    OPTIONAL {{ ?etude :estComparative ?comparative . }}
    OPTIONAL {{
        ?etude :aPourResultat ?resultat .
        OPTIONAL {{
            ?sousTypeRes rdfs:subClassOf* :ResultatClinique .
            ?resultat a ?sousTypeRes .
            BIND(REPLACE(STR(?sousTypeRes), ".*#", "") AS ?typeResultat)
        }}
        OPTIONAL {{ ?resultat :valeurMesuree ?valeur . }}
        OPTIONAL {{ ?resultat :uniteMesure ?unite . }}
    }}
}}
"""


# ─────────────────────────────────────────────────────────────────────────────
# 3. Filtrer par type : EssaiClinique / EtudeObservationnelle
# ─────────────────────────────────────────────────────────────────────────────

_TYPES_ETUDE_VALIDES = {"EssaiClinique", "EtudeObservationnelle"}


def requete_etudes_par_type(type_etude: str) -> str:
    """
    Filtre les études par sous-classe exacte.

    :param type_etude: 'EssaiClinique' ou 'EtudeObservationnelle'.
    :raises HTTPException 422: Si le type est inconnu.
    """
    _valider_id(type_etude, "type_etude")
    if type_etude not in _TYPES_ETUDE_VALIDES:
        raise HTTPException(
            status_code=422,
            detail=f"Type d'étude invalide : '{type_etude}'. "
                   f"Valeurs acceptées : {sorted(_TYPES_ETUDE_VALIDES)}.",
        )
    return PREFIXES + f"""
SELECT DISTINCT
    ?etude ?typeEtude ?medicament ?medicamentNom ?maladie ?maladieNom
    ?phase ?annee ?participants ?comparative
WHERE {{
    ?etude a :{type_etude} .
    BIND("{type_etude}" AS ?typeEtude)

    OPTIONAL {{
        ?etude :testeMedicament ?medicament .
        BIND(REPLACE(STR(?medicament), ".*#", "") AS ?medicamentNom)
    }}
    OPTIONAL {{
        ?etude :porteSurMaladie ?maladie .
        BIND(REPLACE(STR(?maladie), ".*#", "") AS ?maladieNom)
    }}
    OPTIONAL {{ ?etude :phaseEssai ?phase . }}
    OPTIONAL {{ ?etude :anneePublication ?annee . }}
    OPTIONAL {{ ?etude :nombreParticipants ?participants . }}
    OPTIONAL {{ ?etude :estComparative ?comparative . }}
}}
ORDER BY ?etude
"""


# ─────────────────────────────────────────────────────────────────────────────
# 4. Études par médicament
# ─────────────────────────────────────────────────────────────────────────────

def requete_etudes_par_medicament(medicament_id: str) -> str:
    """
    Retourne les études qui testent un médicament donné (via :testeMedicament).

    :param medicament_id: Identifiant court du médicament (ex: 'Glucophage').
    """
    _valider_id(medicament_id, "medicament_id")
    return PREFIXES + f"""
SELECT DISTINCT
    ?etude ?typeEtude
    ?medicament ?medicamentNom
    ?maladie ?maladieNom
    ?phase ?annee ?participants ?comparative
WHERE {{
    ?sousClasse rdfs:subClassOf* :EtudeClinique .
    ?etude a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeEtude)
    BIND(:{medicament_id} AS ?medicament)
    BIND("{medicament_id}" AS ?medicamentNom)
    ?etude :testeMedicament ?medicament .

    OPTIONAL {{
        ?etude :porteSurMaladie ?maladie .
        BIND(REPLACE(STR(?maladie), ".*#", "") AS ?maladieNom)
    }}
    OPTIONAL {{ ?etude :phaseEssai ?phase . }}
    OPTIONAL {{ ?etude :anneePublication ?annee . }}
    OPTIONAL {{ ?etude :nombreParticipants ?participants . }}
    OPTIONAL {{ ?etude :estComparative ?comparative . }}
}}
ORDER BY ?etude
"""


# ─────────────────────────────────────────────────────────────────────────────
# 5. Études par maladie
# ─────────────────────────────────────────────────────────────────────────────

def requete_etudes_par_maladie(maladie_id: str) -> str:
    """
    Retourne les études qui portent sur une maladie donnée (via :porteSurMaladie).

    :param maladie_id: Identifiant court de la maladie (ex: 'DiabeteType2').
    """
    _valider_id(maladie_id, "maladie_id")
    return PREFIXES + f"""
SELECT DISTINCT
    ?etude ?typeEtude
    ?medicament ?medicamentNom
    ?maladie ?maladieNom
    ?phase ?annee ?participants ?comparative
WHERE {{
    ?sousClasse rdfs:subClassOf* :EtudeClinique .
    ?etude a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeEtude)
    BIND(:{maladie_id} AS ?maladie)
    BIND("{maladie_id}" AS ?maladieNom)
    ?etude :porteSurMaladie ?maladie .

    OPTIONAL {{
        ?etude :testeMedicament ?medicament .
        BIND(REPLACE(STR(?medicament), ".*#", "") AS ?medicamentNom)
    }}
    OPTIONAL {{ ?etude :phaseEssai ?phase . }}
    OPTIONAL {{ ?etude :anneePublication ?annee . }}
    OPTIONAL {{ ?etude :nombreParticipants ?participants . }}
    OPTIONAL {{ ?etude :estComparative ?comparative . }}
}}
ORDER BY ?etude
"""


# ─────────────────────────────────────────────────────────────────────────────
# 6. Filtres avancés : phase, année, participants, comparative
# ─────────────────────────────────────────────────────────────────────────────

def requete_etudes_par_phase(phase: int) -> str:
    """
    Retourne les essais cliniques d'une phase donnée.
    Seuls les EssaiClinique ont une phaseEssai.

    :param phase: Numéro de phase (ex: 3).
    """
    return PREFIXES + f"""
SELECT DISTINCT
    ?etude ?typeEtude ?medicament ?medicamentNom ?maladie ?maladieNom
    ?phase ?annee ?participants ?comparative
WHERE {{
    ?etude a :EssaiClinique .
    BIND("EssaiClinique" AS ?typeEtude)
    ?etude :phaseEssai ?phase .
    FILTER(?phase = {int(phase)})

    OPTIONAL {{
        ?etude :testeMedicament ?medicament .
        BIND(REPLACE(STR(?medicament), ".*#", "") AS ?medicamentNom)
    }}
    OPTIONAL {{
        ?etude :porteSurMaladie ?maladie .
        BIND(REPLACE(STR(?maladie), ".*#", "") AS ?maladieNom)
    }}
    OPTIONAL {{ ?etude :anneePublication ?annee . }}
    OPTIONAL {{ ?etude :nombreParticipants ?participants . }}
    OPTIONAL {{ ?etude :estComparative ?comparative . }}
}}
ORDER BY ?etude
"""


def requete_etudes_par_annee(annee_min: Optional[int], annee_max: Optional[int]) -> str:
    """
    Filtre les études par plage d'années de publication.

    :param annee_min: Année minimale (incluse), ou None.
    :param annee_max: Année maximale (incluse), ou None.
    """
    filtres = []
    if annee_min is not None:
        filtres.append(f"    FILTER(?annee >= {int(annee_min)})")
    if annee_max is not None:
        filtres.append(f"    FILTER(?annee <= {int(annee_max)})")
    bloc_filtres = "\n".join(filtres)

    return PREFIXES + f"""
SELECT DISTINCT
    ?etude ?typeEtude ?medicament ?medicamentNom ?maladie ?maladieNom
    ?phase ?annee ?participants ?comparative
WHERE {{
    ?sousClasse rdfs:subClassOf* :EtudeClinique .
    ?etude a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeEtude)
    ?etude :anneePublication ?annee .
{bloc_filtres}
    OPTIONAL {{
        ?etude :testeMedicament ?medicament .
        BIND(REPLACE(STR(?medicament), ".*#", "") AS ?medicamentNom)
    }}
    OPTIONAL {{
        ?etude :porteSurMaladie ?maladie .
        BIND(REPLACE(STR(?maladie), ".*#", "") AS ?maladieNom)
    }}
    OPTIONAL {{ ?etude :phaseEssai ?phase . }}
    OPTIONAL {{ ?etude :nombreParticipants ?participants . }}
    OPTIONAL {{ ?etude :estComparative ?comparative . }}
}}
ORDER BY ?annee ?etude
"""


def requete_etudes_min_participants(minimum: int) -> str:
    """
    Retourne les études avec au moins `minimum` participants.

    :param minimum: Nombre minimal de participants.
    """
    return PREFIXES + f"""
SELECT DISTINCT
    ?etude ?typeEtude ?medicament ?medicamentNom ?maladie ?maladieNom
    ?phase ?annee ?participants ?comparative
WHERE {{
    ?sousClasse rdfs:subClassOf* :EtudeClinique .
    ?etude a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeEtude)
    ?etude :nombreParticipants ?participants .
    FILTER(?participants >= {int(minimum)})

    OPTIONAL {{
        ?etude :testeMedicament ?medicament .
        BIND(REPLACE(STR(?medicament), ".*#", "") AS ?medicamentNom)
    }}
    OPTIONAL {{
        ?etude :porteSurMaladie ?maladie .
        BIND(REPLACE(STR(?maladie), ".*#", "") AS ?maladieNom)
    }}
    OPTIONAL {{ ?etude :phaseEssai ?phase . }}
    OPTIONAL {{ ?etude :anneePublication ?annee . }}
    OPTIONAL {{ ?etude :estComparative ?comparative . }}
}}
ORDER BY DESC(?participants)
"""


def requete_etudes_comparatives() -> str:
    """Retourne uniquement les études dont estComparative = true."""
    return PREFIXES + """
SELECT DISTINCT
    ?etude ?typeEtude ?medicament ?medicamentNom ?maladie ?maladieNom
    ?phase ?annee ?participants ?comparative
WHERE {
    ?sousClasse rdfs:subClassOf* :EtudeClinique .
    ?etude a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeEtude)
    ?etude :estComparative ?comparative .
    FILTER(?comparative = true)

    OPTIONAL {
        ?etude :testeMedicament ?medicament .
        BIND(REPLACE(STR(?medicament), ".*#", "") AS ?medicamentNom)
    }
    OPTIONAL {
        ?etude :porteSurMaladie ?maladie .
        BIND(REPLACE(STR(?maladie), ".*#", "") AS ?maladieNom)
    }
    OPTIONAL { ?etude :phaseEssai ?phase . }
    OPTIONAL { ?etude :anneePublication ?annee . }
    OPTIONAL { ?etude :nombreParticipants ?participants . }
}
ORDER BY ?etude
"""


# ─────────────────────────────────────────────────────────────────────────────
# 7. Études SANS résultat
# ─────────────────────────────────────────────────────────────────────────────

def requete_etudes_sans_resultat() -> str:
    """
    Retourne les études qui n'ont aucun résultat clinique associé.
    Utilise FILTER NOT EXISTS (monde ouvert : absence ≠ faux, mais c'est ce qu'on cherche).
    """
    return PREFIXES + """
SELECT DISTINCT
    ?etude ?typeEtude ?medicament ?medicamentNom ?maladie ?maladieNom
    ?phase ?annee ?participants ?comparative
WHERE {
    ?sousClasse rdfs:subClassOf* :EtudeClinique .
    ?etude a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeEtude)
    FILTER NOT EXISTS { ?etude :aPourResultat ?r . }

    OPTIONAL {
        ?etude :testeMedicament ?medicament .
        BIND(REPLACE(STR(?medicament), ".*#", "") AS ?medicamentNom)
    }
    OPTIONAL {
        ?etude :porteSurMaladie ?maladie .
        BIND(REPLACE(STR(?maladie), ".*#", "") AS ?maladieNom)
    }
    OPTIONAL { ?etude :phaseEssai ?phase . }
    OPTIONAL { ?etude :anneePublication ?annee . }
    OPTIONAL { ?etude :nombreParticipants ?participants . }
    OPTIONAL { ?etude :estComparative ?comparative . }
}
ORDER BY ?etude
"""


# ─────────────────────────────────────────────────────────────────────────────
# 8. Statistiques
# ─────────────────────────────────────────────────────────────────────────────

def requete_stats_etudes() -> str:
    """
    Calcule :
    - Le nombre d'études par type (EssaiClinique / EtudeObservationnelle)
    - La moyenne du nombre de participants par type
    """
    return PREFIXES + """
SELECT ?typeEtude (COUNT(DISTINCT ?etude) AS ?nombreEtudes) (AVG(?participants) AS ?moyenneParticipants)
WHERE {
    ?sousClasse rdfs:subClassOf* :EtudeClinique .
    ?etude a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeEtude)
    OPTIONAL { ?etude :nombreParticipants ?participants . }
}
GROUP BY ?typeEtude
ORDER BY ?typeEtude
"""
