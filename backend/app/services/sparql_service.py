from SPARQLWrapper import SPARQLWrapper, JSON
import os

# L'URL de notre serveur Fuseki local
FUSEKI_URL = os.getenv("FUSEKI_URL", "http://localhost:3030/medsemantic/query")

def execute_sparql_query(query: str):
    """Exécute une requête SPARQL sur Fuseki et retourne les résultats en JSON."""
    sparql = SPARQLWrapper(FUSEKI_URL)
    
    # Ajout automatique des préfixes pour éviter de les répéter dans chaque requête
    prefixes = """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX ms: <http://www.semanticweb.org/medsemantic#>
    """
    
    sparql.setQuery(prefixes + query)
    sparql.setReturnFormat(JSON)
    
    try:
        results = sparql.query().convert()
        return results["results"]["bindings"]
    except Exception as e:
        print(f"Erreur SPARQL: {e}")
        return []
