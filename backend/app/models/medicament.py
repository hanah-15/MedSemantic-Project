from pydantic import BaseModel
from typing import List, Optional

class Molecule(BaseModel):
    nom: str
    type_molecule: str  # "Principe actif" ou "Excipient"
    formule_chimique: Optional[str] = None

class Medicament(BaseModel):
    uri: str
    nom_commercial: str
    dosage: str
    forme_galenique: str
    molecules: Optional[List[Molecule]] = []