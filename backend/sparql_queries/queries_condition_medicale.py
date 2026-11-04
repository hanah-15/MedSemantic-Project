"""Query for medical conditions, including instances typed as subclasses."""

from ._common import PREFIXES, safe_individual_id, literal


def select_conditions(condition_id: str | None = None, *, q: str = '', category: str | None = None,
                      condition_type: str | None = None, severity: str | None = None) -> str:
    values = (
        f"VALUES ?entity {{ med:{safe_individual_id(condition_id)} }}"
        if condition_id is not None else ""
    )
    filters = []
    if category:
        if category not in ('EtatPhysiologique', 'EtatPathologique'):
            raise ValueError('Invalid condition category')
        filters.append(f'?type rdfs:subClassOf* med:{category} .')
    if condition_type:
        filters.append(f'?type rdfs:subClassOf* med:{safe_individual_id(condition_type)} .')
    if severity:
        filters.append(f'FILTER EXISTS {{ ?entity med:severite ?severity . FILTER(LCASE(STR(?severity)) = {literal(severity.lower())}) }}')
    if q.strip():
        term = literal(q.strip().lower())
        filters.append(f'''FILTER(CONTAINS(LCASE(REPLACE(REPLACE(STR(?entity), "_", " "), "([a-z])([A-Z])", "$1 $2")), {term}) ||
          CONTAINS(LCASE(STR(?type)), {term}) || EXISTS {{ ?entity med:severite ?searchValue .
          FILTER(CONTAINS(LCASE(STR(?searchValue)), {term})) }})''')
    return f"""{PREFIXES}
SELECT DISTINCT ?entity ?type ?group ?predicate ?value ?source ?incomingPredicate ?sourceDomain WHERE {{
  {values}
  ?entity rdf:type ?type .
  ?type rdfs:subClassOf* med:ConditionMedicale .
  {' '.join(filters)}
  OPTIONAL {{
    ?type rdfs:subClassOf* ?group .
    FILTER(?group IN (med:EtatPhysiologique, med:EtatPathologique))
  }}
  OPTIONAL {{
    ?entity ?predicate ?value .
    FILTER(?predicate IN (med:severite))
  }}
  OPTIONAL {{
    {{
      ?source med:aPourCondition ?entity ; rdf:type/rdfs:subClassOf* med:Patient .
      BIND(med:aPourCondition AS ?incomingPredicate)
      BIND("patients" AS ?sourceDomain)
    }} UNION {{
      ?source med:concerneCondition ?entity ; rdf:type/rdfs:subClassOf* med:ContreIndication .
      BIND(med:concerneCondition AS ?incomingPredicate)
      BIND("contraindications" AS ?sourceDomain)
    }}
  }}
}}
ORDER BY ?entity ?predicate ?value
"""
