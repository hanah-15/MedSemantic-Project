from SPARQLWrapper import SPARQLWrapper, JSON
import requests
import os

# URLs de notre serveur Fuseki local
FUSEKI_QUERY_URL = os.getenv("FUSEKI_QUERY_URL", os.getenv("FUSEKI_URL", "http://localhost:3030/medsemantic/query"))
FUSEKI_UPDATE_URL = os.getenv("FUSEKI_UPDATE_URL", "http://localhost:3030/medsemantic/update")

# Préfixes réutilisables dans toutes les requêtes SPARQL
PREFIXES = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX ms: <http://www.semanticweb.org/medsemantic#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""

def execute_sparql_query(query: str):
    """Exécute une requête SPARQL (SELECT/ASK) sur Fuseki et retourne les résultats en JSON."""
    sparql = SPARQLWrapper(FUSEKI_QUERY_URL)
    sparql.setQuery(PREFIXES + query)
    sparql.setReturnFormat(JSON)
    
    try:
        results = sparql.query().convert()
        return results.get("results", {}).get("bindings", [])
    except Exception as e:
        print(f"Erreur SPARQL Query: {e}")
        return []

def execute_sparql_update(update_query: str) -> bool:
    """Exécute une requête SPARQL Update (INSERT/DELETE) sur Fuseki."""
    full_query = PREFIXES + update_query
    try:
        response = requests.post(
            FUSEKI_UPDATE_URL,
            data={"update": full_query},
            headers={"Accept": "application/json"}
        )
        if response.status_code in [200, 204]:
            return True
        else:
            print(f"Erreur HTTP Fuseki ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"Erreur SPARQL Update: {e}")
        return False
