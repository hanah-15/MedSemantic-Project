from typing import List, Optional
from pydantic import BaseModel


class ContreIndicationResume(BaseModel):
    """Représentation synthétique d'une contre-indication."""
    iri: str
    id: str
    type_ci: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    condition_id: Optional[str] = None
    condition_iri: Optional[str] = None
    medicaments_lies: List[str] = []


class ContreIndicationDetail(BaseModel):
    """Détail complet d'une contre-indication."""
    iri: str
    id: str
    type_ci: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    conditions_concernees: List[dict] = []
    medicaments_concernes: List[dict] = []


class AlerteContreIndication(BaseModel):
    """Alerte de sécurité patient-médicament."""
    est_contre_indique: bool
    patient_id: str
    medicament_id: str
    alertes: List[dict] = []


class ContreIndicationStats(BaseModel):
    """Statistiques par type de contre-indication."""
    type_ci: str
    total: int
