from typing import List, Optional
from pydantic import BaseModel


class EffetSecondaireResume(BaseModel):
    """Représentation synthétique d'un effet secondaire."""
    iri: str
    id: str
    type_effet: Optional[str] = None
    label: Optional[str] = None
    frequence: Optional[str] = None
    gravite: Optional[str] = None
    symptome_id: Optional[str] = None
    symptome_iri: Optional[str] = None
    medicaments_lies: List[str] = []


class EffetSecondaireDetail(BaseModel):
    """Détail complet d'un effet secondaire."""
    iri: str
    id: str
    type_effet: Optional[str] = None
    label: Optional[str] = None
    frequence: Optional[str] = None
    gravite: Optional[str] = None
    symptomes: List[dict] = []
    medicaments: List[dict] = []


class EffetSecondaireStats(BaseModel):
    """Statistiques par type d'effet secondaire."""
    type_effet: str
    total: int
