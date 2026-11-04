"""Map SPARQL binding rows to stable, UI-friendly API records."""

from collections import defaultdict
from typing import Any
from urllib.parse import unquote

from sparql_queries._common import NAMESPACE

# Only the predicates owned by Sofiene's two classes are represented here.
PATIENT_PREDICATES = {'aPourMaladie', 'aPourCondition', 'ressentSymptome', 'prend'}


def local_name(uri: str) -> str:
    return unquote(uri.rsplit('#', 1)[-1].rsplit('/', 1)[-1])


def binding_value(row: dict[str, Any], key: str) -> str | None:
    binding = row.get(key)
    return str(binding['value']) if binding is not None else None


def age_class(age: int | None) -> str | None:
    """Age label computed from the specification, NOT an OWL inference."""
    if age is None or age < 0:
        return None
    if age < 18:
        return 'Enfant'
    if age < 65:
        return 'Adulte'
    return 'PersonneAgee'


def build_records(rows: list[dict[str, Any]], domain: str) -> list[dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    seen_links: dict[str, set[tuple[str, str]]] = defaultdict(set)

    for row in rows:
        entity_uri = binding_value(row, 'entity')
        if not entity_uri or not entity_uri.startswith(NAMESPACE):
            continue
        identifier = local_name(entity_uri)
        if identifier not in records:
            records[identifier] = {
                'id': identifier,
                'name': identifier.replace('_', ' '),
                'domain': domain,
                'type': 'Patient' if domain == 'patients' else 'ConditionMedicale',
                'description': ('Patient record from the medical ontology' if domain == 'patients'
                                else 'Medical condition from the ontology'),
                'properties': {},
                'relations': [],
            }
        entity = records[identifier]
        rdf_type = binding_value(row, 'type')
        if rdf_type and rdf_type.startswith(NAMESPACE):
            name = local_name(rdf_type)
            root_name = 'Patient' if domain == 'patients' else 'ConditionMedicale'
            if entity['type'] == root_name or name != root_name:
                entity['type'] = name

        group = binding_value(row, 'group')
        if group and group.startswith(NAMESPACE):
            entity['properties']['category'] = local_name(group)

        predicate_uri = binding_value(row, 'predicate')
        value = binding_value(row, 'value')
        if not predicate_uri or value is None or not predicate_uri.startswith(NAMESPACE):
            continue
        predicate = local_name(predicate_uri)
        if domain == 'patients':
            if predicate in ('age', 'sexe'):
                entity['properties'][predicate] = value
            elif predicate in PATIENT_PREDICATES and value.startswith(NAMESPACE):
                pair = (predicate, local_name(value))
                if pair not in seen_links[identifier]:
                    entity['relations'].append({'predicate': pair[0], 'target': pair[1]})
                    seen_links[identifier].add(pair)
        elif domain == 'conditions' and predicate == 'severite':
            entity['properties'][predicate] = value

    if domain == 'patients':
        for item in records.values():
            raw_age = item['properties'].get('age')
            try:
                age = int(raw_age) if raw_age is not None else None
            except (TypeError, ValueError):
                age = None
            category = age_class(age)
            if category is not None:
                item['properties']['ageCategory'] = category
            item['description'] = (
                f"Patient · {age} years old" if age is not None else 'Patient record from the ontology'
            )
    else:
        for item in records.values():
            category = item['properties'].get('category', 'ConditionMedicale')
            item['description'] = category.replace('Etat', 'État ') + ' · ' + item['type']

    return sorted(records.values(), key=lambda record: record['id'])
