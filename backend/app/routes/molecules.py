"""Read molecular composition and metabolism directly from the ontology."""
from fastapi import APIRouter, HTTPException
from app.services.fuseki import query_select, FusekiUnavailable
from sparql_queries._common import PREFIXES, safe_individual_id

router = APIRouter(prefix='/api/molecules', tags=['Molécules'])
NS = 'http://www.semanticweb.org/medsemantic#'


def records(identifier=None):
    try:
        selected = f'VALUES ?entity {{ :{safe_individual_id(identifier)} }}' if identifier else ''
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    query = PREFIXES + f'PREFIX : <{NS}>\n' + f'''
    SELECT DISTINCT ?entity ?type ?predicate ?value ?source ?incomingPredicate ?sourceDomain
    WHERE {{
        {selected}
        ?entity a ?type . ?type rdfs:subClassOf* :Molecule .
        OPTIONAL {{ ?entity ?predicate ?value . FILTER(?predicate != rdf:type) }}
        OPTIONAL {{
            ?source ?incomingPredicate ?entity .
            VALUES (?root ?sourceDomain) {{ (:Medicament "medications") (:Molecule "molecules") }}
            ?source rdf:type/rdfs:subClassOf* ?root .
        }}
    }} ORDER BY ?entity ?type
    '''
    try:
        rows = query_select(query)
    except FusekiUnavailable as error:
        raise HTTPException(status_code=503, detail='Molecules are temporarily unavailable') from error
    items = {}
    for row in rows:
        value = lambda key: row.get(key, {}).get('value', '')
        local = lambda iri: iri.rsplit('#', 1)[-1].rsplit('/', 1)[-1]
        identifier = local(value('entity'))
        item = items.setdefault(identifier, dict(id=identifier, name=identifier, domain='molecules',
            type=local(value('type')), description='Molecular composition and metabolism',
            properties={}, relations=[], incomingRelations=[]))
        if value('predicate'):
            predicate = local(value('predicate'))
            if row.get('value', {}).get('type') == 'uri':
                relation = dict(predicate=predicate, target=local(value('value')))
                if relation not in item['relations']:
                    item['relations'].append(relation)
            else:
                item['properties'][predicate] = value('value')
        if value('source'):
            relation = dict(predicate=local(value('incomingPredicate')), source=local(value('source')), sourceDomain=value('sourceDomain'))
            if relation not in item['incomingRelations']:
                item['incomingRelations'].append(relation)
    return list(items.values())


@router.get('')
@router.get('/')
def list_molecules():
    return records()


@router.get('/{identifier}')
def get_molecule(identifier: str):
    items = records(identifier)
    if not items:
        raise HTTPException(status_code=404, detail='Molecule not found')
    return items[0]
