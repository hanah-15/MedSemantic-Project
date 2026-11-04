"""Queries for Patient and its direct medical links.

Explicit RDF triples are used. Age-based labels are calculated in the API,
not presented as OWL reasoner inferences.
"""

from ._common import PREFIXES, safe_individual_id, literal

PATIENT_PROPERTIES = (
    "med:age, med:sexe, med:aPourMaladie, med:aPourCondition, "
    "med:ressentSymptome, med:prend"
)


def select_patients(patient_id: str | None = None, *, q: str = '', min_age: int | None = None,
                    max_age: int | None = None, age_category: str | None = None,
                    sexe: str | None = None, condition_id: str | None = None,
                    condition_type: str | None = None) -> str:
    values = (
        f"VALUES ?entity {{ med:{safe_individual_id(patient_id)} }}"
        if patient_id is not None else ""
    )
    filters = []
    if min_age is not None:
        filters.append(f'FILTER EXISTS {{ ?entity med:age ?ageMin . FILTER(?ageMin >= {int(min_age)}) }}')
    if max_age is not None:
        filters.append(f'FILTER EXISTS {{ ?entity med:age ?ageMax . FILTER(?ageMax <= {int(max_age)}) }}')
    bands = {'Enfant': '?ageBand < 18', 'Adulte': '?ageBand >= 18 && ?ageBand < 65', 'PersonneAgee': '?ageBand >= 65'}
    if age_category:
        if age_category not in bands:
            raise ValueError('Invalid age category')
        filters.append(f'FILTER EXISTS {{ ?entity med:age ?ageBand . FILTER({bands[age_category]}) }}')
    if sexe:
        filters.append(f'FILTER EXISTS {{ ?entity med:sexe ?sex . FILTER(LCASE(STR(?sex)) = {literal(sexe.lower())}) }}')
    if condition_id:
        filters.append(f'?entity med:aPourCondition med:{safe_individual_id(condition_id)} .')
    if condition_type:
        filters.append(f'?entity med:aPourCondition ?condition . ?condition rdf:type/rdfs:subClassOf* med:{safe_individual_id(condition_type)} .')
    if q.strip():
        term = literal(q.strip().lower())
        filters.append(f'''FILTER(CONTAINS(LCASE(REPLACE(REPLACE(STR(?entity), "_", " "), "([a-z])([A-Z])", "$1 $2")), {term}) ||
          CONTAINS(LCASE(STR(?type)), {term}) || EXISTS {{ ?entity ?searchProperty ?searchValue .
          FILTER(?searchProperty IN (med:age, med:sexe)) FILTER(CONTAINS(LCASE(STR(?searchValue)), {term})) }})''')
    return f"""{PREFIXES}
SELECT DISTINCT ?entity ?type ?predicate ?value WHERE {{
  {values}
  ?entity rdf:type ?type .
  ?type rdfs:subClassOf* med:Patient .
  {' '.join(filters)}
  OPTIONAL {{
    ?entity ?predicate ?value .
    FILTER(?predicate IN ({PATIENT_PROPERTIES}))
  }}
}}
ORDER BY ?entity ?predicate ?value
"""
