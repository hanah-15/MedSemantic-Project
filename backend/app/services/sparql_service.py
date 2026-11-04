import requests
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv(Path(__file__).resolve().parents[2] / '.env')


def fuseki_endpoint(operation: str) -> str:
    base = os.getenv('FUSEKI_URL', 'http://localhost:3030/medsemantic').rstrip('/')
    for suffix in ('/query', '/sparql', '/update'):
        if base.endswith(suffix):
            base = base[:-len(suffix)]
            break
    return os.getenv(f'FUSEKI_{operation.upper()}_URL') or f'{base}/{operation}'

# Préfixes réutilisables dans toutes les requêtes SPARQL
PREFIXES = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX ms: <http://www.semanticweb.org/medsemantic#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""

def execute_sparql_query(query: str):
    """Exécute une requête SPARQL (SELECT/ASK) sur Fuseki et retourne les résultats en JSON."""
    try:
        response = requests.post(
            fuseki_endpoint('query'), data={'query': PREFIXES + query},
            headers={'Accept': 'application/sparql-results+json'}, timeout=12,
        )
        response.raise_for_status()
        bindings = response.json()['results']['bindings']
        if not isinstance(bindings, list):
            raise ValueError('Invalid query result')
        return bindings
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=503, detail='Records are temporarily unavailable.') from exc

def execute_sparql_update(update_query: str) -> bool:
    """Exécute une requête SPARQL Update (INSERT/DELETE) sur Fuseki."""
    full_query = PREFIXES + update_query
    try:
        response = requests.post(
            fuseki_endpoint('update'),
            data={"update": full_query},
            headers={"Accept": "application/json"},
            timeout=12,
        )
        if response.status_code in [200, 204]:
            return True
        else:
            print(f"Erreur HTTP Fuseki ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"Erreur SPARQL Update: {e}")
        return False
