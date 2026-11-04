"""Editable attributes and explicit links owned by the clinical module."""

from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field

Identifier = Annotated[str, Field(pattern=r'^[A-Za-z][A-Za-z0-9_]*$', max_length=120)]


class ClinicalModel(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class PatientWrite(ClinicalModel):
    age: int = Field(ge=0, strict=True)
    sexe: str = Field(min_length=1, max_length=40)
    aPourMaladie: list[Identifier] = Field(default_factory=list)
    aPourCondition: list[Identifier] = Field(default_factory=list)
    ressentSymptome: list[Identifier] = Field(default_factory=list)
    prend: list[Identifier] = Field(default_factory=list)


class PatientCreate(PatientWrite):
    id: Identifier


class ConditionWrite(ClinicalModel):
    type: Identifier
    severite: str | None = Field(default=None, max_length=500)


class ConditionCreate(ConditionWrite):
    id: Identifier
