"""Validate and write only clinical individuals, preserving unrelated triples."""

from fastapi import HTTPException
from app.services import fuseki
from sparql_queries._common import NAMESPACE, PREFIXES, safe_individual_id, literal

LINK_ROOTS = {'aPourMaladie':'Maladie', 'aPourCondition':'ConditionMedicale', 'ressentSymptome':'Symptome', 'prend':'Medicament'}


def select(query: str):
    try:
        return fuseki.query_select(PREFIXES + query)
    except fuseki.FusekiUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc


def update(query: str):
    try:
        fuseki.query_update(PREFIXES + query)
    except fuseki.FusekiUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc


def ensure_unused(identifier: str):
    identifier = safe_individual_id(identifier)
    if select(f'SELECT ?p WHERE {{ {{ med:{identifier} ?p ?o }} UNION {{ ?s ?p med:{identifier} }} }} LIMIT 1'):
        raise HTTPException(409, 'This identifier is already in use.')


def condition_types():
    rows = select('''SELECT DISTINCT ?entity ?parent WHERE {
      ?entity rdfs:subClassOf* med:ConditionMedicale .
      FILTER(isIRI(?entity))
      OPTIONAL { ?entity rdfs:subClassOf ?parent . FILTER(isIRI(?parent)) }
    } ORDER BY ?entity''')
    return [{'id':row['entity']['value'][len(NAMESPACE):], 'parent':row.get('parent',{}).get('value','').removeprefix(NAMESPACE)}
            for row in rows if row['entity']['value'].startswith(NAMESPACE)]


def patient_options():
    rows = select('''SELECT DISTINCT ?entity ?root WHERE {
      VALUES ?root { med:Maladie med:ConditionMedicale med:Symptome med:Medicament }
      ?entity rdf:type/rdfs:subClassOf* ?root .
      FILTER(STRSTARTS(STR(?entity), "''' + NAMESPACE + '''"))
    } ORDER BY ?entity''')
    result = {predicate:[] for predicate in LINK_ROOTS}
    for row in rows:
        identifier = row['entity']['value'][len(NAMESPACE):]
        for predicate,root in LINK_ROOTS.items():
            if row['root']['value'] == NAMESPACE + root:
                result[predicate].append({'id':identifier,'name':identifier.replace('_',' ')})
    return result


def filter_options(domain: str):
    root,predicate,key = ('Patient','sexe','sexes') if domain == 'patients' else ('ConditionMedicale','severite','severities')
    rows = select(f'''SELECT DISTINCT ?value WHERE {{
      ?entity rdf:type/rdfs:subClassOf* med:{root} ; med:{predicate} ?value .
      FILTER(isLiteral(?value))
    }}''')
    return {key:sorted({row['value']['value'] for row in rows},key=str.casefold)}


def write_record(identifier: str, payload, domain: str, *, create: bool):
    identifier = safe_individual_id(identifier)
    root = 'Patient' if domain == 'patients' else 'ConditionMedicale'
    if create:
        ensure_unused(identifier)
    values = payload.model_dump(exclude={'id'})
    if domain == 'patients':
        triples = [f'med:{identifier} rdf:type med:Patient, owl:NamedIndividual .',
                   f'med:{identifier} med:age {literal(values["age"])} ; med:sexe {literal(values["sexe"])} .']
        for predicate,target_root in LINK_ROOTS.items():
            for target in sorted(set(values[predicate])):
                if not select(f'SELECT ?type WHERE {{ med:{target} rdf:type ?type . ?type rdfs:subClassOf* med:{target_root} }} LIMIT 1'):
                    raise HTTPException(422, f'{target} is not a recorded {target_root}.')
                triples.append(f'med:{identifier} med:{predicate} med:{target} .')
        owned = ['age','sexe',*LINK_ROOTS]
    else:
        condition_type = values['type']
        if not select(f'SELECT ?type WHERE {{ BIND(med:{condition_type} AS ?type) ?type rdfs:subClassOf* med:ConditionMedicale }} LIMIT 1'):
            raise HTTPException(422, 'Choose a condition class defined in the ontology.')
        triples = [f'med:{identifier} rdf:type med:{condition_type}, owl:NamedIndividual .']
        if values['severite']:
            triples.append(f'med:{identifier} med:severite {literal(values["severite"])} .')
        owned = ['severite']
    if create:
        update('INSERT DATA { ' + ' '.join(triples) + ' }')
    else:
        predicates = ', '.join('med:'+name for name in owned)
        update(f'''DELETE {{ med:{identifier} ?p ?o }} INSERT {{ {' '.join(triples)} }}
          WHERE {{ OPTIONAL {{ med:{identifier} ?p ?o . FILTER(?p IN ({predicates}) ||
          (?p = rdf:type && EXISTS {{ ?o rdfs:subClassOf* med:{root} }})) }} }}''')


def delete_record(identifier: str):
    identifier = safe_individual_id(identifier)
    update(f'''DELETE {{ med:{identifier} ?p ?o . ?s ?incoming med:{identifier} }}
      WHERE {{ {{ med:{identifier} ?p ?o }} UNION {{ ?s ?incoming med:{identifier} }} }}''')
