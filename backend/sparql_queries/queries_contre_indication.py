"""
Requêtes SPARQL pour la classe ContreIndication et ses sous-classes
(ContreIndicationAbsolue, ContreIndicationRelative).
Module développé par Oussema.
"""

import re
from typing import Optional
from fastapi import HTTPException
from app.fuseki_client import PREFIXES

_ID_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


def _valider_id(valeur: str, nom: str = "id") -> str:
    """Valide qu'un identifiant ne contient que des caractères alphanumériques ou '_'."""
    if not _ID_PATTERN.fullmatch(valeur):
        raise HTTPException(
            status_code=422,
            detail=(
                f"Paramètre '{nom}' invalide : '{valeur}'. "
                "Seuls les caractères A-Z, a-z, 0-9 et _ sont autorisés."
            ),
        )
    return valeur


_ALIAS_TYPE = {
    "absolue": "ContreIndicationAbsolue",
    "contreindicationabsolue": "ContreIndicationAbsolue",
    "relative": "ContreIndicationRelative",
    "contreindicationrelative": "ContreIndicationRelative",
}


def requete_lister_contre_indications() -> str:
    """
    Retourne toutes les contre-indications (absolues et relatives) via rdfs:subClassOf*.
    Inclut la description, la condition/maladie concernée et les médicaments associés.
    """
    return PREFIXES + """
SELECT DISTINCT
    ?ci ?typeCI
    ?description
    ?condition ?conditionNom
    ?medicament ?medicamentNom
    ?label
WHERE {
    ?sousClasse rdfs:subClassOf* :ContreIndication .
    ?ci a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeCI)

    OPTIONAL { ?ci :description ?description . }
    OPTIONAL {
        ?ci :concerneCondition ?condition .
        BIND(REPLACE(STR(?condition), ".*#", "") AS ?conditionNom)
    }
    OPTIONAL {
        { ?medicament :aPourContreIndication ?ci . }
        UNION
        { ?ci :estContreIndicationDe ?medicament . }
        BIND(REPLACE(STR(?medicament), ".*#", "") AS ?medicamentNom)
    }
    OPTIONAL { ?ci rdfs:label ?label . }
}
ORDER BY ?typeCI ?ci
"""


def requete_detail_contre_indication(ci_id: str) -> str:
    """
    Retourne le détail complet d'une contre-indication par son identifiant court.
    """
    _valider_id(ci_id, "ci_id")
    return PREFIXES + f"""
SELECT DISTINCT
    ?ci ?typeCI
    ?description
    ?condition ?conditionNom
    ?medicament ?medicamentNom
    ?label
WHERE {{
    BIND(:{ci_id} AS ?ci)
    ?sousClasse rdfs:subClassOf* :ContreIndication .
    ?ci a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeCI)

    OPTIONAL {{ ?ci :description ?description . }}
    OPTIONAL {{
        ?ci :concerneCondition ?condition .
        BIND(REPLACE(STR(?condition), ".*#", "") AS ?conditionNom)
    }}
    OPTIONAL {{
        {{ ?medicament :aPourContreIndication ?ci . }}
        UNION
        {{ ?ci :estContreIndicationDe ?medicament . }}
        BIND(REPLACE(STR(?medicament), ".*#", "") AS ?medicamentNom)
    }}
    OPTIONAL {{ ?ci rdfs:label ?label . }}
}}
"""


def requete_contre_indications_par_type(type_ci: str) -> str:
    """
    Filtre les contre-indications par type ('absolue' ou 'relative').
    """
    cle = type_ci.lower().replace("-", "").replace("_", "")
    type_normalise = _ALIAS_TYPE.get(cle, type_ci)
    _valider_id(type_normalise, "type_ci")
    if type_normalise not in set(_ALIAS_TYPE.values()):
        raise HTTPException(status_code=422, detail="Type de contre-indication inconnu")

    return PREFIXES + f"""
SELECT DISTINCT
    ?ci ?typeCI
    ?description
    ?condition ?conditionNom
    ?medicament ?medicamentNom
    ?label
WHERE {{
    ?sousClasse rdfs:subClassOf* :{type_normalise} .
    ?ci a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeCI)

    OPTIONAL {{ ?ci :description ?description . }}
    OPTIONAL {{
        ?ci :concerneCondition ?condition .
        BIND(REPLACE(STR(?condition), ".*#", "") AS ?conditionNom)
    }}
    OPTIONAL {{
        {{ ?medicament :aPourContreIndication ?ci . }}
        UNION
        {{ ?ci :estContreIndicationDe ?medicament . }}
        BIND(REPLACE(STR(?medicament), ".*#", "") AS ?medicamentNom)
    }}
    OPTIONAL {{ ?ci rdfs:label ?label . }}
}}
ORDER BY ?ci
"""


def requete_contre_indications_par_medicament(medicament_id: str) -> str:
    """
    Retourne les contre-indications associées à un médicament donné (:aPourContreIndication).
    """
    _valider_id(medicament_id, "medicament_id")
    return PREFIXES + f"""
SELECT DISTINCT
    ?ci ?typeCI
    ?description
    ?condition ?conditionNom
    ?label ?medicament ?medicamentNom
WHERE {{
    BIND(:{medicament_id} AS ?medicament)
    BIND("{medicament_id}" AS ?medicamentNom)
    {{ ?medicament :aPourContreIndication ?ci . }}
    UNION
    {{ ?ci :estContreIndicationDe ?medicament . }}

    ?sousClasse rdfs:subClassOf* :ContreIndication .
    ?ci a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeCI)

    OPTIONAL {{ ?ci :description ?description . }}
    OPTIONAL {{
        ?ci :concerneCondition ?condition .
        BIND(REPLACE(STR(?condition), ".*#", "") AS ?conditionNom)
    }}
    OPTIONAL {{ ?ci rdfs:label ?label . }}
}}
ORDER BY ?typeCI ?ci
"""


def requete_contre_indications_par_condition(condition_id: str) -> str:
    """
    Retourne les contre-indications concernant une condition médicale ou une maladie (:concerneCondition).
    """
    _valider_id(condition_id, "condition_id")
    return PREFIXES + f"""
SELECT DISTINCT
    ?ci ?typeCI
    ?description
    ?medicament ?medicamentNom
    ?label
WHERE {{
    BIND(:{condition_id} AS ?condition)
    ?ci :concerneCondition ?condition .

    ?sousClasse rdfs:subClassOf* :ContreIndication .
    ?ci a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeCI)

    OPTIONAL {{ ?ci :description ?description . }}
    OPTIONAL {{
        {{ ?medicament :aPourContreIndication ?ci . }}
        UNION
        {{ ?ci :estContreIndicationDe ?medicament . }}
        BIND(REPLACE(STR(?medicament), ".*#", "") AS ?medicamentNom)
    }}
    OPTIONAL {{ ?ci rdfs:label ?label . }}
}}
ORDER BY ?typeCI ?ci
"""


def requete_verifier_contre_indication(patient_id: str, medicament_id: str) -> str:
    """
    Vérifie si un médicament est contre-indiqué pour un patient donné,
    en croisant les conditions / maladies du patient avec les contre-indications du médicament.
    """
    _valider_id(patient_id, "patient_id")
    _valider_id(medicament_id, "medicament_id")
    return PREFIXES + f"""
SELECT DISTINCT
    ?ci ?typeCI
    ?description
    ?condition ?conditionNom
    ?raison
WHERE {{
    BIND(:{patient_id} AS ?patient)
    BIND(:{medicament_id} AS ?medicament)

    # Récupérer les contre-indications du médicament
    {{ ?medicament :aPourContreIndication ?ci . }}
    UNION
    {{ ?ci :estContreIndicationDe ?medicament . }}

    ?sousClasse rdfs:subClassOf* :ContreIndication .
    ?ci a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeCI)

    # Croiser avec la condition ou la maladie du patient
    ?ci :concerneCondition ?condition .
    BIND(REPLACE(STR(?condition), ".*#", "") AS ?conditionNom)

    {{
        ?patient :aPourCondition ?condition .
        BIND("Condition médicale active du patient" AS ?raison)
    }} UNION {{
        ?patient :aPourMaladie ?condition .
        BIND("Pathologie active du patient" AS ?raison)
    }}

    OPTIONAL {{ ?ci :description ?description . }}
}}
"""


def requete_stats_contre_indications() -> str:
    """
    Statistiques globales sur les contre-indications (nombre par type : Absolue / Relative).
    """
    return PREFIXES + """
SELECT ?typeCI (COUNT(DISTINCT ?ci) AS ?total)
WHERE {
    ?sousClasse rdfs:subClassOf* :ContreIndication .
    ?ci a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeCI)
}
GROUP BY ?typeCI
ORDER BY DESC(?total) ?typeCI
"""
