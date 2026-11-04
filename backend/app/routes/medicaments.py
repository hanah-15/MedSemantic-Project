from fastapi import APIRouter
from app.services.sparql_service import execute_sparql_query
from app.models.medicament import Medicament, Molecule

router = APIRouter(prefix="/api/medicaments", tags=["Médicaments & Molécules"])

@router.get("/", response_model=list[Medicament])
def get_tous_les_medicaments():
    """Récupère la liste de tous les médicaments avec leurs informations de base."""
    query = """
    SELECT ?medicament ?nom ?dosage ?forme
    WHERE {
      ?medicament rdf:type/rdfs:subClassOf* ms:Medicament .
      ?medicament ms:nomCommercial ?nom .
      ?medicament ms:dosage ?dosage .
      ?medicament ms:formeGalenique ?forme .
    }
    """
    resultats = execute_sparql_query(query)
    
    liste_medicaments = []
    for row in resultats:
        liste_medicaments.append(Medicament(
            uri=row["medicament"]["value"].split("#")[-1],
            nom_commercial=row["nom"]["value"],
            dosage=row["dosage"]["value"],
            forme_galenique=row["forme"]["value"]
        ))
        
    return liste_medicaments

@router.get("/{nom_medicament}", response_model=list[Molecule])
def get_molecules_medicament(nom_medicament: str):
    """Récupère la composition chimique (Principes actifs et Excipients) d'un médicament précis."""
    query = f"""
    SELECT ?moleculeUri ?formule ?typeMolecule
    WHERE {{
      ?medicament ms:nomCommercial "{nom_medicament}" .
      
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
    
    liste_molecules = []
    for row in resultats:
        liste_molecules.append(Molecule(
            nom=row["moleculeUri"]["value"].split("#")[-1],
            type_molecule=row["typeMolecule"]["value"],
            formule_chimique=row.get("formule", {}).get("value")
        ))
        
    return liste_molecules