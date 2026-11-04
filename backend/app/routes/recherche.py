from fastapi import APIRouter
from app.services.nlp_service import analyser_requete_nlp
from app.services.sparql_service import execute_sparql_query

router = APIRouter(prefix="/api/recherche", tags=["Recherche NLP"])

@router.get("/")
def recherche_intelligente(q: str):
    """Point d'entrée pour les questions en langage naturel."""
    # 1. Le NLP analyse la question
    analyse = analyser_requete_nlp(q)
    intention = analyse["intention"]
    medicament = analyse["medicament"]
    
    if not medicament:
        return {"reponse": "Je n'ai pas compris de quel médicament vous parlez."}
        
    # 2. Construction dynamique de la requête SPARQL selon l'intention
    if intention == "composition":
        query = f"""
        SELECT ?moleculeUri ?typeMolecule
        WHERE {{
          ?medicament ms:nomCommercial "{medicament}" .
          {{
            ?medicament ms:contientPrincipeActif ?moleculeUri .
            BIND("Principe actif" AS ?typeMolecule)
          }} UNION {{
            ?medicament ms:contientExcipient ?moleculeUri .
            BIND("Excipient" AS ?typeMolecule)
          }}
        }}
        """
        resultats = execute_sparql_query(query)
        molecules = [row["moleculeUri"]["value"].split("#")[-1] for row in resultats]
        return {"reponse": f"Le {medicament} est composé de : {', '.join(molecules)}."}
        
    elif intention == "dosage":
        query = f"""
        SELECT ?dosage WHERE {{
          ?medicament ms:nomCommercial "{medicament}" .
          ?medicament ms:dosage ?dosage .
        }}
        """
        resultats = execute_sparql_query(query)
        if resultats:
            dosage = resultats[0]["dosage"]["value"]
            return {"reponse": f"Le dosage du {medicament} est de {dosage}."}
            
    elif intention == "forme_galenique":
        query = f"""
        SELECT ?forme WHERE {{
          ?medicament ms:nomCommercial "{medicament}" .
          ?medicament ms:formeGalenique ?forme .
        }}
        """
        resultats = execute_sparql_query(query)
        if resultats:
            forme = resultats[0]["forme"]["value"]
            return {"reponse": f"La forme galénique du {medicament} est : {forme}."}
            
    return {"reponse": f"Je vois que vous parlez du {medicament}, mais je n'ai pas compris votre question exacte (essayez avec 'dosage', 'molécules' ou 'forme')."}