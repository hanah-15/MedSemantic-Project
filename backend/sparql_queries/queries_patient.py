"""Queries for Patient and its direct medical links.

Explicit RDF triples are used. Age-based labels are calculated in the API,
not presented as OWL reasoner inferences.
"""

from ._common import PREFIXES, safe_individual_id

PATIENT_PROPERTIES = (
    "med:age, med:sexe, med:aPourMaladie, med:aPourCondition, "
    "med:ressentSymptome, med:prend"
)


def select_patients(patient_id: str | None = None) -> str:
    values = (
        f"VALUES ?entity {{ med:{safe_individual_id(patient_id)} }}"
        if patient_id is not None else ""
    )
    return f"""{PREFIXES}
SELECT DISTINCT ?entity ?type ?predicate ?value WHERE {{
  {values}
  ?entity rdf:type ?type .
  ?type rdfs:subClassOf* med:Patient .
  OPTIONAL {{
    ?entity ?predicate ?value .
    FILTER(?predicate IN ({PATIENT_PROPERTIES}))
  }}
}}
ORDER BY ?entity ?predicate ?value
"""
