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

class MedicamentCreate(BaseModel):
    uri: Optional[str] = None  # Optionnel: s'il n'est pas fourni, il est dérivé du nom_commercial
    nom_commercial: str
    dosage: str
    forme_galenique: str
    molecules: Optional[List[Molecule]] = []

class MedicamentUpdate(BaseModel):
    nom_commercial: Optional[str] = None
    dosage: Optional[str] = None
    forme_galenique: Optional[str] = None
