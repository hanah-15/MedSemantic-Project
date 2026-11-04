import re
from rdflib import Literal
from fastapi import APIRouter, HTTPException, status
from app.services.sparql_service import execute_sparql_query, execute_sparql_update
from app.models.medicament import (
    Medicament,
    Molecule,
    MedicamentCreate,
    MedicamentUpdate
)

router = APIRouter(prefix="/api/medicaments", tags=["Médicaments & Molécules"])

def sparql_literal(value: str) -> str:
    return Literal(value).n3()


def sanitize_uri(text: str) -> str:
    """Nettoie une chaîne pour en faire un identifiant URI SPARQL valide."""
    clean = re.sub(r"[^\w\-]", "_", text.strip())
    return clean

def medicament_exists(uri: str) -> bool:
    """Vérifie si un médicament existe dans l'ontologie."""
    clean_uri = sanitize_uri(uri.replace("ms:", ""))
    query = f"""
    SELECT ?medicament WHERE {{
        BIND(ms:{clean_uri} AS ?medicament)
        ?medicament rdf:type ?type .
    }} LIMIT 1
    """
    rows = execute_sparql_query(query)
    return len(rows) > 0


# ==========================================
# 1. READ (Lectures)
# ==========================================

@router.get("/", response_model=list[Medicament])
def get_tous_les_medicaments():
    """Récupère la liste de tous les médicaments avec leurs informations de base."""
    query = """
    SELECT DISTINCT ?medicament ?nom ?dosage ?forme
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


@router.get("/details/{uri}", response_model=Medicament)
def get_medicament_par_uri(uri: str):
    """Récupère les détails complets d'un médicament (y compris ses molécules) par son URI."""
    clean_uri = sanitize_uri(uri.replace("ms:", ""))
    query_info = f"""
    SELECT ?nom ?dosage ?forme WHERE {{
      ms:{clean_uri} ms:nomCommercial ?nom .
      OPTIONAL {{ ms:{clean_uri} ms:dosage ?dosage . }}
      OPTIONAL {{ ms:{clean_uri} ms:formeGalenique ?forme . }}
    }} LIMIT 1
    """
    info_res = execute_sparql_query(query_info)
    if not info_res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Médicament avec l'URI '{uri}' introuvable."
        )

    row = info_res[0]
    nom = row["nom"]["value"]
    dosage = row.get("dosage", {}).get("value", "")
    forme = row.get("forme", {}).get("value", "")

    # Récupération des molécules associées
    query_molecules = f"""
    SELECT DISTINCT ?moleculeUri ?formule ?typeMolecule WHERE {{
      {{
        ms:{clean_uri} ms:contientPrincipeActif ?moleculeUri .
        BIND("Principe actif" AS ?typeMolecule)
      }} UNION {{
        ms:{clean_uri} ms:contientExcipient ?moleculeUri .
        BIND("Excipient" AS ?typeMolecule)
      }}
      OPTIONAL {{ ?moleculeUri ms:formuleChimique ?formule . }}
    }}
    """
    mol_res = execute_sparql_query(query_molecules)
    molecules = []
    for m in mol_res:
        molecules.append(Molecule(
            nom=m["moleculeUri"]["value"].split("#")[-1],
            type_molecule=m["typeMolecule"]["value"],
            formule_chimique=m.get("formule", {}).get("value")
        ))

    return Medicament(
        uri=clean_uri,
        nom_commercial=nom,
        dosage=dosage,
        forme_galenique=forme,
        molecules=molecules
    )


@router.get("/{nom_medicament}", response_model=list[Molecule])
def get_molecules_medicament(nom_medicament: str):
    """Récupère la composition chimique (Principes actifs et Excipients) d'un médicament précis par son nom."""
    query = f"""
    SELECT DISTINCT ?moleculeUri ?formule ?typeMolecule
    WHERE {{
      ?medicament ms:nomCommercial ?nom .
      FILTER(STR(?nom) = {sparql_literal(nom_medicament)})

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


# ==========================================
# 2. CREATE (Ajout)
# ==========================================

@router.post("/", response_model=Medicament, status_code=status.HTTP_201_CREATED)
def creer_medicament(payload: MedicamentCreate):
    """Crée et ajoute un nouveau médicament ainsi que ses molécules associées dans l'ontologie."""
    uri_id = payload.uri if payload.uri else sanitize_uri(payload.nom_commercial)
    uri_id = sanitize_uri(uri_id.replace("ms:", ""))

    # Vérifier si l'URI existe déjà
    if medicament_exists(uri_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Un médicament avec l'URI '{uri_id}' existe déjà."
        )

    # Triples de base pour le médicament
    triples = [
        f'ms:{uri_id} rdf:type ms:Medicament .',
        f'ms:{uri_id} ms:nomCommercial {sparql_literal(payload.nom_commercial)} .',
        f'ms:{uri_id} ms:dosage {sparql_literal(payload.dosage)} .',
        f'ms:{uri_id} ms:formeGalenique {sparql_literal(payload.forme_galenique)} .'
    ]

    # Ajout des molécules si spécifiées
    if payload.molecules:
        for mol in payload.molecules:
            mol_uri = sanitize_uri(mol.nom)
            if "actif" in mol.type_molecule.lower():
                triples.append(f"ms:{uri_id} ms:contientPrincipeActif ms:{mol_uri} .")
                triples.append(f"ms:{mol_uri} rdf:type ms:PrincipeActif .")
            else:
                triples.append(f"ms:{uri_id} ms:contientExcipient ms:{mol_uri} .")
                triples.append(f"ms:{mol_uri} rdf:type ms:Excipient .")

            if mol.formule_chimique:
                triples.append(f'ms:{mol_uri} ms:formuleChimique {sparql_literal(mol.formule_chimique)} .')

    sparql_update = f"""
    INSERT DATA {{
      {' '.join(triples)}
    }}
    """
    success = execute_sparql_update(sparql_update)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'insertion dans Fuseki."
        )

    return Medicament(
        uri=uri_id,
        nom_commercial=payload.nom_commercial,
        dosage=payload.dosage,
        forme_galenique=payload.forme_galenique,
        molecules=payload.molecules or []
    )


# ==========================================
# 3. UPDATE (Modification)
# ==========================================

@router.put("/{uri}", response_model=dict)
def modifier_medicament(uri: str, payload: MedicamentUpdate):
    """Modifie les informations (nom commercial, dosage, forme galénique) d'un médicament existant."""
    clean_uri = sanitize_uri(uri.replace("ms:", ""))
    if not medicament_exists(clean_uri):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Médicament avec l'URI '{uri}' introuvable."
        )

    delete_triples = []
    insert_triples = []
    where_triples = []

    if payload.nom_commercial is not None:
        delete_triples.append(f"ms:{clean_uri} ms:nomCommercial ?oldNom .")
        insert_triples.append(f'ms:{clean_uri} ms:nomCommercial {sparql_literal(payload.nom_commercial)} .')
        where_triples.append(f"OPTIONAL {{ ms:{clean_uri} ms:nomCommercial ?oldNom . }}")

    if payload.dosage is not None:
        delete_triples.append(f"ms:{clean_uri} ms:dosage ?oldDosage .")
        insert_triples.append(f'ms:{clean_uri} ms:dosage {sparql_literal(payload.dosage)} .')
        where_triples.append(f"OPTIONAL {{ ms:{clean_uri} ms:dosage ?oldDosage . }}")

    if payload.forme_galenique is not None:
        delete_triples.append(f"ms:{clean_uri} ms:formeGalenique ?oldForme .")
        insert_triples.append(f'ms:{clean_uri} ms:formeGalenique {sparql_literal(payload.forme_galenique)} .')
        where_triples.append(f"OPTIONAL {{ ms:{clean_uri} ms:formeGalenique ?oldForme . }}")

    if not delete_triples:
        return {"status": "success", "message": "Aucun champ à modifier."}

    sparql_update = f"""
    DELETE {{
      {' '.join(delete_triples)}
    }}
    INSERT {{
      {' '.join(insert_triples)}
    }}
    WHERE {{
      {' '.join(where_triples)}
    }}
    """
    success = execute_sparql_update(sparql_update)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour dans Fuseki."
        )

    return {
        "status": "success",
        "message": f"Médicament '{clean_uri}' mis à jour avec succès.",
        "uri": clean_uri
    }


# ==========================================
# 4. DELETE (Suppression)
# ==========================================

@router.delete("/{uri}", response_model=dict)
def supprimer_medicament(uri: str):
    """Supprime un médicament et l'ensemble de ses liens dans l'ontologie."""
    clean_uri = sanitize_uri(uri.replace("ms:", ""))
    if not medicament_exists(clean_uri):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Médicament avec l'URI '{uri}' introuvable."
        )

    # Suppression de tous les triplets où le médicament est sujet ou objet
    sparql_update = f"""
    DELETE {{
      ms:{clean_uri} ?p ?o .
      ?s ?incoming ms:{clean_uri} .
    }}
    WHERE {{
      {{ ms:{clean_uri} ?p ?o . }} UNION {{ ?s ?incoming ms:{clean_uri} . }}
    }}
    """
    success = execute_sparql_update(sparql_update)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression dans Fuseki."
        )

    return {
        "status": "success",
        "message": f"Médicament '{clean_uri}' supprimé avec succès."
    }
