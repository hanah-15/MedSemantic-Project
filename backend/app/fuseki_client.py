"""
Client partagé pour Apache Jena Fuseki.
Toutes les requêtes SPARQL de l'API passent par ce module.
"""

import os
import requests
from typing import Dict, Any, List
from fastapi import HTTPException

# Préfixe commun à toute l'ontologie MedSemantic
PREFIXES = """
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
PREFIX :     <http://www.semanticweb.org/medsemantic#>
"""

# Timeout par défaut (secondes) pour chaque appel HTTP vers Fuseki
FUSEKI_TIMEOUT = 10


def get_fuseki_url() -> str:
    """Retourne l'URL du dataset Fuseki depuis la variable d'environnement FUSEKI_URL."""
    url = os.getenv("FUSEKI_URL", "http://localhost:3030/medsemantic")
    return url.rstrip("/")


def execute_sparql(query: str) -> List[Dict[str, Any]]:
    """
    Exécute une requête SPARQL SELECT sur le endpoint Fuseki configuré.

    :param query: Chaîne SPARQL complète (préfixes inclus).
    :returns: Liste de dictionnaires {variable: {"type": ..., "value": ...}}.
    :raises HTTPException 502: Si Fuseki est injoignable ou retourne une erreur HTTP.
    """
    endpoint = f"{get_fuseki_url()}/sparql"
    headers = {"Accept": "application/sparql-results+json"}
    try:
        response = requests.get(
            endpoint,
            params={"query": query},
            headers=headers,
            timeout=FUSEKI_TIMEOUT,
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=502,
            detail="Impossible de joindre le serveur Fuseki. Vérifiez que le serveur est démarré.",
        )
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=503,
            detail="Le serveur Fuseki n'a pas répondu dans le délai imparti.",
        )
    except requests.exceptions.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Erreur HTTP depuis Fuseki : {exc.response.status_code}",
        )

    data = response.json()
    return data.get("results", {}).get("bindings", [])


def extract_local_name(iri: str) -> str:
    """
    Extrait l'identifiant court depuis une IRI complète.
    Ex: 'http://www.semanticweb.org/medsemantic#Essai_Metformine_2024'
        → 'Essai_Metformine_2024'
    """
    if "#" in iri:
        return iri.split("#")[-1]
    return iri.split("/")[-1]


def val(binding: Dict[str, Any], key: str) -> str:
    """Retourne la valeur d'une variable SPARQL ou une chaîne vide si absente."""
    return binding.get(key, {}).get("value", "")
