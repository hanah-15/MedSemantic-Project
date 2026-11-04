"""Query for medical conditions, including instances typed as subclasses."""

from ._common import PREFIXES, safe_individual_id


def select_conditions(condition_id: str | None = None) -> str:
    values = (
        f"VALUES ?entity {{ med:{safe_individual_id(condition_id)} }}"
        if condition_id is not None else ""
    )
    return f"""{PREFIXES}
SELECT DISTINCT ?entity ?type ?group ?predicate ?value WHERE {{
  {values}
  ?entity rdf:type ?type .
  ?type rdfs:subClassOf* med:ConditionMedicale .
  OPTIONAL {{
    ?type rdfs:subClassOf* ?group .
    FILTER(?group IN (med:EtatPhysiologique, med:EtatPathologique))
  }}
  OPTIONAL {{
    ?entity ?predicate ?value .
    FILTER(?predicate IN (med:severite))
  }}
}}
ORDER BY ?entity ?predicate ?value
"""
