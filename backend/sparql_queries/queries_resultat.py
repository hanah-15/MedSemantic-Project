"""
Requêtes SPARQL pour la classe ResultatClinique et ses sous-classes
(Efficacite, Securite, Tolerance).

Toutes les fonctions retournent une chaîne SPARQL prête à l'emploi.
"""

import re
from typing import Optional
from fastapi import HTTPException
from app.fuseki_client import PREFIXES

# ─────────────────────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────────────────────

_ID_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


def _valider_id(valeur: str, nom: str = "id") -> str:
    """Valide un identifiant. Lève HTTP 422 si invalide."""
    if not _ID_PATTERN.match(valeur):
        raise HTTPException(
            status_code=422,
            detail=(
                f"Paramètre '{nom}' invalide : '{valeur}'. "
                "Seuls A-Z, a-z, 0-9, _ sont autorisés."
            ),
        )
    return valeur


# Mapping des alias de types vers les IRI locales (insensible à la casse côté route)
_ALIAS_TYPE = {
    "efficacite":  "Efficacite",
    "securite":    "Securite",
    "tolerance":   "Tolerance",
}


# ─────────────────────────────────────────────────────────────────────────────
# 1. Lister tous les résultats (avec type précis via rdfs:subClassOf*)
# ─────────────────────────────────────────────────────────────────────────────

def requete_lister_resultats() -> str:
    """
    Retourne tous les résultats cliniques avec leur type précis.
    Tolerance est une sous-classe de Securite : rdfs:subClassOf* permet
    d'inclure toutes les sous-classes sans raisonneur.
    """
    return PREFIXES + """
SELECT DISTINCT
    ?resultat ?typeResultat ?valeur ?unite
    ?etude ?etudeNom ?medicament ?medicamentNom
WHERE {
    ?sousClasse rdfs:subClassOf* :ResultatClinique .
    ?resultat a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeResultat)

    OPTIONAL { ?resultat :valeurMesuree ?valeur . }
    OPTIONAL { ?resultat :uniteMesure ?unite . }
    OPTIONAL {
        ?etude :aPourResultat ?resultat .
        BIND(REPLACE(STR(?etude), ".*#", "") AS ?etudeNom)
        OPTIONAL {
            ?etude :testeMedicament ?medicament .
            BIND(REPLACE(STR(?medicament), ".*#", "") AS ?medicamentNom)
        }
    }
}
ORDER BY ?typeResultat ?resultat
"""


# ─────────────────────────────────────────────────────────────────────────────
# 2. Détail d'un résultat par identifiant
# ─────────────────────────────────────────────────────────────────────────────

def requete_detail_resultat(resultat_id: str) -> str:
    """
    Retourne le détail d'un résultat avec l'étude et le médicament associés.

    :param resultat_id: Identifiant court validé (ex: 'Res_Efficacite_Glucophage').
    """
    _valider_id(resultat_id, "resultat_id")
    return PREFIXES + f"""
SELECT DISTINCT
    ?resultat ?typeResultat ?valeur ?unite
    ?etude ?etudeNom ?typeEtude
    ?medicament ?medicamentNom
WHERE {{
    BIND(:{resultat_id} AS ?resultat)
    ?sousClasse rdfs:subClassOf* :ResultatClinique .
    ?resultat a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeResultat)

    OPTIONAL {{ ?resultat :valeurMesuree ?valeur . }}
    OPTIONAL {{ ?resultat :uniteMesure ?unite . }}
    OPTIONAL {{
        ?etude :aPourResultat ?resultat .
        BIND(REPLACE(STR(?etude), ".*#", "") AS ?etudeNom)
        OPTIONAL {{
            ?sousClasseEtude rdfs:subClassOf* :EtudeClinique .
            ?etude a ?sousClasseEtude .
            BIND(REPLACE(STR(?sousClasseEtude), ".*#", "") AS ?typeEtude)
        }}
        OPTIONAL {{
            ?etude :testeMedicament ?medicament .
            BIND(REPLACE(STR(?medicament), ".*#", "") AS ?medicamentNom)
        }}
    }}
}}
"""


# ─────────────────────────────────────────────────────────────────────────────
# 3. Résultats par type (efficacite / securite / tolerance)
# ─────────────────────────────────────────────────────────────────────────────

def requete_resultats_par_type(type_alias: str) -> str:
    """
    Retourne les résultats d'un type donné.
    - 'securite' inclut aussi les Tolerance via rdfs:subClassOf*
    - 'tolerance' retourne uniquement les Tolerance

    :param type_alias: 'efficacite', 'securite' ou 'tolerance' (insensible à la casse).
    """
    alias = type_alias.lower()
    if alias not in _ALIAS_TYPE:
        raise HTTPException(
            status_code=422,
            detail=f"Type de résultat invalide : '{type_alias}'. "
                   f"Valeurs acceptées : {sorted(_ALIAS_TYPE.keys())}.",
        )
    classe_iri = _ALIAS_TYPE[alias]
    return PREFIXES + f"""
SELECT DISTINCT
    ?resultat ?typeResultat ?valeur ?unite
    ?etude ?etudeNom ?medicament ?medicamentNom
WHERE {{
    # rdfs:subClassOf* permet d'inclure les sous-classes (ex: Tolerance ⊆ Securite)
    ?sousClasse rdfs:subClassOf* :{classe_iri} .
    ?resultat a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeResultat)

    OPTIONAL {{ ?resultat :valeurMesuree ?valeur . }}
    OPTIONAL {{ ?resultat :uniteMesure ?unite . }}
    OPTIONAL {{
        ?etude :aPourResultat ?resultat .
        BIND(REPLACE(STR(?etude), ".*#", "") AS ?etudeNom)
        OPTIONAL {{
            ?etude :testeMedicament ?medicament .
            BIND(REPLACE(STR(?medicament), ".*#", "") AS ?medicamentNom)
        }}
    }}
}}
ORDER BY ?typeResultat ?resultat
"""


# ─────────────────────────────────────────────────────────────────────────────
# 4. Résultats par médicament (via l'étude intermédiaire)
# ─────────────────────────────────────────────────────────────────────────────

def requete_resultats_par_medicament(medicament_id: str) -> str:
    """
    Retourne les résultats cliniques liés à un médicament,
    en passant par la chaîne : Medicament ← testeMedicament ← EtudeClinique → aPourResultat → ResultatClinique.

    :param medicament_id: Identifiant court du médicament (ex: 'Glucophage').
    """
    _valider_id(medicament_id, "medicament_id")
    return PREFIXES + f"""
SELECT DISTINCT
    ?resultat ?typeResultat ?valeur ?unite
    ?etude ?etudeNom ?medicament ?medicamentNom
WHERE {{
    BIND(:{medicament_id} AS ?medicament)
    BIND("{medicament_id}" AS ?medicamentNom)
    ?etude :testeMedicament ?medicament .
    ?etude :aPourResultat ?resultat .

    ?sousClasse rdfs:subClassOf* :ResultatClinique .
    ?resultat a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeResultat)
    BIND(REPLACE(STR(?etude), ".*#", "") AS ?etudeNom)

    OPTIONAL {{ ?resultat :valeurMesuree ?valeur . }}
    OPTIONAL {{ ?resultat :uniteMesure ?unite . }}
}}
ORDER BY ?typeResultat ?resultat
"""


# ─────────────────────────────────────────────────────────────────────────────
# 5. Statistiques des résultats
# ─────────────────────────────────────────────────────────────────────────────

def requete_stats_resultats() -> str:
    """
    Calcule le nombre de résultats par type (Efficacite, Securite, Tolerance).
    Retourne le type précis (pas le type parent).
    """
    return PREFIXES + """
SELECT ?typeResultat (COUNT(DISTINCT ?resultat) AS ?nombreResultats)
WHERE {
    ?sousClasse rdfs:subClassOf* :ResultatClinique .
    ?resultat a ?sousClasse .
    BIND(REPLACE(STR(?sousClasse), ".*#", "") AS ?typeResultat)
}
GROUP BY ?typeResultat
ORDER BY ?typeResultat
"""
