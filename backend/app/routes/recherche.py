import re
from fastapi import APIRouter, Query
from app.services.clinical_nlp import answer_clinical_question
from app.services.safety_nlp import answer_safety_question
from app.services.nlp_service import analyser_requete_nlp
from app.services.sparql_service import execute_sparql_query, PREFIXES as SPARQL_PREFIXES

router = APIRouter(prefix="/api/recherche", tags=["Recherche NLP"])

def echapper_sparql(valeur: str) -> str:
    """Échappe les caractères réservés pour éviter toute erreur de syntaxe SPARQL."""
    return re.sub(r'([\\"\'])', r'\\\1', valeur)

@router.get("/")
def recherche_intelligente(q: str = Query(min_length=1, max_length=500)):
    """Point d'entrée pour les questions en langage naturel traitées par NLP et résolues via Fuseki."""
    safety = answer_safety_question(q)
    if safety is not None:
        return safety
    clinical = answer_clinical_question(q)
    if clinical is not None:
        return clinical
    query = None
    analyse = analyser_requete_nlp(q)
    intention = analyse["intention"]
    medicament = analyse["medicament"]

    if not medicament:
        return {
            "query": q,
            "sparql": SPARQL_PREFIXES + query if query else None,
            "tools": ["spaCy", "fr_core_news_sm", "PhraseMatcher", "SPARQL templates"],
            "intention": intention,
            "medicament": None,
            "reponse": "Je n'ai pas pu identifier de médicament dans votre question. Essayez par exemple : 'Quel est le dosage du Doliprane ?' ou 'Composition de l'Advil'."
        }

    med_clean = echapper_sparql(medicament)

    # 1. INTENTION : COMPOSITION CHIMIQUE (Principes actifs & Excipients)
    if intention == "composition":
        query = f"""
        SELECT ?nomCommercial ?moleculeUri ?typeMolecule ?formule
        WHERE {{
          ?medicament rdf:type/rdfs:subClassOf* ms:Medicament .
          ?medicament ms:nomCommercial ?nomCommercial .
          FILTER(CONTAINS(LCASE(STR(?nomCommercial)), LCASE("{med_clean}")))

          {{
            ?medicament ms:contientPrincipeActif ?moleculeUri .
            BIND("Principe actif" AS ?typeMolecule)
          }} UNION {{
            ?medicament ms:contientExcipient ?moleculeUri .
            BIND("Excipient" AS ?typeMolecule)
          }}
          OPTIONAL {{ ?moleculeUri ms:formuleChimique ?formule . }}
        }}
        """
        resultats = execute_sparql_query(query)
        if not resultats:
            return {
                "query": q,
            "sparql": SPARQL_PREFIXES + query if query else None,
            "tools": ["spaCy", "fr_core_news_sm", "PhraseMatcher", "SPARQL templates"],
                "intention": intention,
                "medicament": medicament,
                "reponse": f"Aucune composition chimique enregistrée dans l'ontologie pour '{medicament}'."
            }

        molecules = [
            {
                "nom": row["moleculeUri"]["value"].split("#")[-1],
                "type": row["typeMolecule"]["value"],
                "formule": row.get("formule", {}).get("value")
            }
            for row in resultats
        ]
        noms_actifs = [m["nom"] for m in molecules if "actif" in m["type"].lower()]
        noms_excipients = [m["nom"] for m in molecules if "excipient" in m["type"].lower()]

        detail_txt = []
        if noms_actifs:
            detail_txt.append(f"Principe(s) actif(s) : {', '.join(noms_actifs)}")
        if noms_excipients:
            detail_txt.append(f"Excipient(s) : {', '.join(noms_excipients)}")

        reponse_str = f"Le médicament {medicament} contient : {' | '.join(detail_txt) if detail_txt else ', '.join(m['nom'] for m in molecules)}."
        return {
            "query": q,
            "sparql": SPARQL_PREFIXES + query if query else None,
            "tools": ["spaCy", "fr_core_news_sm", "PhraseMatcher", "SPARQL templates"],
            "intention": intention,
            "medicament": medicament,
            "reponse": reponse_str,
            "data": molecules
        }

    # 2. INTENTION : DOSAGE
    elif intention == "dosage":
        query = f"""
        SELECT ?nomCommercial ?dosage WHERE {{
          ?medicament rdf:type/rdfs:subClassOf* ms:Medicament .
          ?medicament ms:nomCommercial ?nomCommercial .
          ?medicament ms:dosage ?dosage .
          FILTER(CONTAINS(LCASE(STR(?nomCommercial)), LCASE("{med_clean}")))
        }} LIMIT 1
        """
        res = execute_sparql_query(query)
        if res:
            nom_exact = res[0]["nomCommercial"]["value"]
            dosage = res[0]["dosage"]["value"]
            return {
                "query": q,
            "sparql": SPARQL_PREFIXES + query if query else None,
            "tools": ["spaCy", "fr_core_news_sm", "PhraseMatcher", "SPARQL templates"],
                "intention": intention,
                "medicament": nom_exact,
                "reponse": f"Le dosage de {nom_exact} est de {dosage}."
            }
        return {
            "query": q,
            "sparql": SPARQL_PREFIXES + query if query else None,
            "tools": ["spaCy", "fr_core_news_sm", "PhraseMatcher", "SPARQL templates"],
            "intention": intention,
            "medicament": medicament,
            "reponse": f"Le dosage pour '{medicament}' n'est pas précisé dans la base de connaissances."
        }

    # 3. INTENTION : FORME GALÉNIQUE
    elif intention == "forme_galenique":
        query = f"""
        SELECT ?nomCommercial ?forme WHERE {{
          ?medicament rdf:type/rdfs:subClassOf* ms:Medicament .
          ?medicament ms:nomCommercial ?nomCommercial .
          ?medicament ms:formeGalenique ?forme .
          FILTER(CONTAINS(LCASE(STR(?nomCommercial)), LCASE("{med_clean}")))
        }} LIMIT 1
        """
        res = execute_sparql_query(query)
        if res:
            nom_exact = res[0]["nomCommercial"]["value"]
            forme = res[0]["forme"]["value"]
            return {
                "query": q,
            "sparql": SPARQL_PREFIXES + query if query else None,
            "tools": ["spaCy", "fr_core_news_sm", "PhraseMatcher", "SPARQL templates"],
                "intention": intention,
                "medicament": nom_exact,
                "reponse": f"La forme galénique de {nom_exact} est : {forme}."
            }
        return {
            "query": q,
            "sparql": SPARQL_PREFIXES + query if query else None,
            "tools": ["spaCy", "fr_core_news_sm", "PhraseMatcher", "SPARQL templates"],
            "intention": intention,
            "medicament": medicament,
            "reponse": f"La forme galénique pour '{medicament}' n'est pas renseignée dans la base."
        }

    # 4. INTENTION NON RECONNUE MAIS MÉDICAMENT TROUVÉ
    return {
        "query": q,
            "sparql": SPARQL_PREFIXES + query if query else None,
            "tools": ["spaCy", "fr_core_news_sm", "PhraseMatcher", "SPARQL templates"],
        "intention": intention,
        "medicament": medicament,
        "reponse": f"Médicament détecté ({medicament}), mais l'intention est incertaine. Vous pouvez demander par exemple : 'Quel est le dosage de {medicament} ?' ou 'Quelle est la composition de {medicament} ?'"
    }
