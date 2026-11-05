"""
Requêtes SPARQL pour la classe EffetSecondaire et ses sous-classes
(EffetDigestif, EffetNeurologique, EffetCardiovasculaire, EffetAllergique).
Module développé par Oussema.
"""

import re
from typing import Optional
from fastapi import HTTPException
from app.fuseki_client import PREFIXES

_ID_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


def _valider_id(valeur: str, nom: str = "id") -> str:
    """Valide qu'un identifiant ne contient que des caractères alphanumériques ou '_'."""
    if not _ID_PATTERN.match(valeur):
        raise HTTPException(
            status_code=422,
            detail=(
                f"Paramètre '{nom}' invalide : '{valeur}'. "
                "Seuls les caractères A-Z, a-z, 0-9 et _ sont autorisés."
            ),
        )
    return valeur


# Alias normalisés vers les noms de classes exactes de l'ontologie
_ALIAS_TYPE = {
    "effetdigestif": "EffetDigestif",
    "digestif": "EffetDigestif",
    "effetneurologique": "EffetNeurologique",
    "neurologique": "EffetNeurologique",
    "effetcardiovasculaire": "EffetCardiovasculaire",
    "cardiovasculaire": "EffetCardiovasculaire",
    "effetallergique": "EffetAllergique",
    "allergique": "EffetAllergique",
}


def requete_lister_effets_secondaires() -> str:
    """
    Retourne tous les effets secondaires et leurs sous-classes via rdfs:subClassOf*.
    Inclut les informations de fréquence, gravité, symptômes manifestés et médicaments déclencheurs.
    """
    return PREFIXES + """
SELECT DISTINCT
    ?effet ?typeEffet
    ?frequence ?gravite
    ?symptome ?symptomeNom
    ?medicament ?medicamentNom
    ?label
WHERE {
    ?sousClasse rdfs:subClassOf* :EffetSecondaire .
    ?effet a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeEffet)

    OPTIONAL { ?effet :frequenceEffet ?frequence . }
    OPTIONAL { ?effet :gravite ?gravite . }
    OPTIONAL {
        ?effet :manifesteSymptome ?symptome .
        BIND(REPLACE(STR(?symptome), ".*#", "") AS ?symptomeNom)
    }
    OPTIONAL {
        { ?medicament :provoque ?effet . }
        UNION
        { ?effet :estProvoquePar ?medicament . }
        BIND(REPLACE(STR(?medicament), ".*#", "") AS ?medicamentNom)
    }
    OPTIONAL { ?effet rdfs:label ?label . }
}
ORDER BY ?typeEffet ?effet
"""


def requete_detail_effet_secondaire(effet_id: str) -> str:
    """
    Retourne le détail d'un effet secondaire par son identifiant.
    """
    _valider_id(effet_id, "effet_id")
    return PREFIXES + f"""
SELECT DISTINCT
    ?effet ?typeEffet
    ?frequence ?gravite
    ?symptome ?symptomeNom
    ?medicament ?medicamentNom
    ?label
WHERE {{
    BIND(:{effet_id} AS ?effet)
    ?sousClasse rdfs:subClassOf* :EffetSecondaire .
    ?effet a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeEffet)

    OPTIONAL {{ ?effet :frequenceEffet ?frequence . }}
    OPTIONAL {{ ?effet :gravite ?gravite . }}
    OPTIONAL {{
        ?effet :manifesteSymptome ?symptome .
        BIND(REPLACE(STR(?symptome), ".*#", "") AS ?symptomeNom)
    }}
    OPTIONAL {{
        {{ ?medicament :provoque ?effet . }}
        UNION
        {{ ?effet :estProvoquePar ?medicament . }}
        BIND(REPLACE(STR(?medicament), ".*#", "") AS ?medicamentNom)
    }}
    OPTIONAL {{ ?effet rdfs:label ?label . }}
}}
"""


def requete_effets_par_type(type_effet: str) -> str:
    """
    Retourne les effets secondaires d'un type précis (sous-classe).
    Supporte les alias (ex: 'digestif' -> 'EffetDigestif').
    """
    cle = type_effet.lower().replace("-", "").replace("_", "")
    type_normalise = _ALIAS_TYPE.get(cle, type_effet)
    _valider_id(type_normalise, "type_effet")

    return PREFIXES + f"""
SELECT DISTINCT
    ?effet ?typeEffet
    ?frequence ?gravite
    ?symptome ?symptomeNom
    ?medicament ?medicamentNom
    ?label
WHERE {{
    ?sousClasse rdfs:subClassOf* :{type_normalise} .
    ?effet a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeEffet)

    OPTIONAL {{ ?effet :frequenceEffet ?frequence . }}
    OPTIONAL {{ ?effet :gravite ?gravite . }}
    OPTIONAL {{
        ?effet :manifesteSymptome ?symptome .
        BIND(REPLACE(STR(?symptome), ".*#", "") AS ?symptomeNom)
    }}
    OPTIONAL {{
        {{ ?medicament :provoque ?effet . }}
        UNION
        {{ ?effet :estProvoquePar ?medicament . }}
        BIND(REPLACE(STR(?medicament), ".*#", "") AS ?medicamentNom)
    }}
    OPTIONAL {{ ?effet rdfs:label ?label . }}
}}
ORDER BY ?effet
"""


def requete_effets_par_gravite(gravite: str) -> str:
    """
    Filtre les effets secondaires par gravité (légère, modérée, sévère).
    """
    # Nettoyage et sécurisation de la chaîne
    gravite_clean = gravite.replace('"', '\\"').strip()
    return PREFIXES + f"""
SELECT DISTINCT
    ?effet ?typeEffet
    ?frequence ?gravite
    ?symptome ?symptomeNom
    ?medicament ?medicamentNom
    ?label
WHERE {{
    ?sousClasse rdfs:subClassOf* :EffetSecondaire .
    ?effet a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeEffet)
    ?effet :gravite ?gravite .
    FILTER(LCASE(STR(?gravite)) = LCASE("{gravite_clean}"))

    OPTIONAL {{ ?effet :frequenceEffet ?frequence . }}
    OPTIONAL {{
        ?effet :manifesteSymptome ?symptome .
        BIND(REPLACE(STR(?symptome), ".*#", "") AS ?symptomeNom)
    }}
    OPTIONAL {{
        {{ ?medicament :provoque ?effet . }}
        UNION
        {{ ?effet :estProvoquePar ?medicament . }}
        BIND(REPLACE(STR(?medicament), ".*#", "") AS ?medicamentNom)
    }}
    OPTIONAL {{ ?effet rdfs:label ?label . }}
}}
ORDER BY ?effet
"""


def requete_effets_par_frequence(frequence: str) -> str:
    """
    Filtre les effets secondaires par niveau de fréquence (ex: 'fréquent', 'rare').
    """
    frequence_clean = frequence.replace('"', '\\"').strip()
    return PREFIXES + f"""
SELECT DISTINCT
    ?effet ?typeEffet
    ?frequence ?gravite
    ?symptome ?symptomeNom
    ?medicament ?medicamentNom
    ?label
WHERE {{
    ?sousClasse rdfs:subClassOf* :EffetSecondaire .
    ?effet a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeEffet)
    ?effet :frequenceEffet ?frequence .
    FILTER(LCASE(STR(?frequence)) = LCASE("{frequence_clean}"))

    OPTIONAL {{ ?effet :gravite ?gravite . }}
    OPTIONAL {{
        ?effet :manifesteSymptome ?symptome .
        BIND(REPLACE(STR(?symptome), ".*#", "") AS ?symptomeNom)
    }}
    OPTIONAL {{
        {{ ?medicament :provoque ?effet . }}
        UNION
        {{ ?effet :estProvoquePar ?medicament . }}
        BIND(REPLACE(STR(?medicament), ".*#", "") AS ?medicamentNom)
    }}
    OPTIONAL {{ ?effet rdfs:label ?label . }}
}}
ORDER BY ?effet
"""


def requete_effets_par_medicament(medicament_id: str) -> str:
    """
    Retourne tous les effets secondaires provoqués par un médicament donné (:provoque).
    """
    _valider_id(medicament_id, "medicament_id")
    return PREFIXES + f"""
SELECT DISTINCT
    ?effet ?typeEffet
    ?frequence ?gravite
    ?symptome ?symptomeNom
    ?label
WHERE {{
    BIND(:{medicament_id} AS ?medicament)
    {{ ?medicament :provoque ?effet . }}
    UNION
    {{ ?effet :estProvoquePar ?medicament . }}

    ?sousClasse rdfs:subClassOf* :EffetSecondaire .
    ?effet a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeEffet)

    OPTIONAL {{ ?effet :frequenceEffet ?frequence . }}
    OPTIONAL {{ ?effet :gravite ?gravite . }}
    OPTIONAL {{
        ?effet :manifesteSymptome ?symptome .
        BIND(REPLACE(STR(?symptome), ".*#", "") AS ?symptomeNom)
    }}
    OPTIONAL {{ ?effet rdfs:label ?label . }}
}}
ORDER BY ?typeEffet ?effet
"""


def requete_effets_par_symptome(symptome_id: str) -> str:
    """
    Retourne les effets secondaires manifestant un symptôme donné (:manifesteSymptome).
    """
    _valider_id(symptome_id, "symptome_id")
    return PREFIXES + f"""
SELECT DISTINCT
    ?effet ?typeEffet
    ?frequence ?gravite
    ?medicament ?medicamentNom
    ?label
WHERE {{
    BIND(:{symptome_id} AS ?symptome)
    ?effet :manifesteSymptome ?symptome .

    ?sousClasse rdfs:subClassOf* :EffetSecondaire .
    ?effet a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeEffet)

    OPTIONAL {{ ?effet :frequenceEffet ?frequence . }}
    OPTIONAL {{ ?effet :gravite ?gravite . }}
    OPTIONAL {{
        {{ ?medicament :provoque ?effet . }}
        UNION
        {{ ?effet :estProvoquePar ?medicament . }}
        BIND(REPLACE(STR(?medicament), ".*#", "") AS ?medicamentNom)
    }}
    OPTIONAL {{ ?effet rdfs:label ?label . }}
}}
ORDER BY ?typeEffet ?effet
"""


def requete_stats_effets_secondaires() -> str:
    """
    Statistiques globales sur les effets secondaires groupés par type de sous-classe.
    """
    return PREFIXES + """
SELECT ?typeEffet (COUNT(DISTINCT ?effet) AS ?total)
WHERE {
    ?sousClasse rdfs:subClassOf* :EffetSecondaire .
    ?effet a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeEffet)
}
GROUP BY ?typeEffet
ORDER BY DESC(?total) ?typeEffet
"""
