"""Local French NLP translates safety questions to executable SPARQL."""
from app.services.clinical_nlp import normalize, match_entities
from app.services.nlp_service import nlp
from app.services.fuseki import query_select
from sparql_queries._common import PREFIXES, safe_individual_id
from fastapi import HTTPException
from app.services.fuseki import FusekiUnavailable


def select(query):
    try:
        return query_select(query)
    except FusekiUnavailable as error:
        raise HTTPException(status_code=503, detail='Records are temporarily unavailable.') from error


def answer_safety_question(text):
    normalized = normalize(text)
    words = {normalize(token.lemma_ or token.text) for token in nlp(text)}
    contraindications = 'contre-indication' in normalized or 'contre indication' in normalized or 'contreindication' in normalized
    effects = 'effet' in words and ('secondaire' in words or 'indesirable' in words)
    if not contraindications and not effects:
        return None
    result = {'query':text,'medicament':None,'records':[],
        'tools':['spaCy','fr_core_news_sm','PhraseMatcher','SPARQL templates']}
    if words & {'sans','aucun','pas'} or any(token.dep_ == 'neg' for token in nlp(text)):
        return {**result,'intention':'clarification','sparql':None,
            'reponse':"Je peux rechercher les effets et contre-indications enregistrés. Leur absence ne permet pas de conclure à la sécurité d'un médicament."}
    medications = select(PREFIXES+'SELECT DISTINCT ?med WHERE { ?med rdf:type/rdfs:subClassOf* med:Medicament }')
    ids = [row['med']['value'].split('#')[-1] for row in medications]
    matched = match_entities(text, ids)
    if len(matched)>1 or not matched and words & {'du','pour'}:
        return {**result,'intention':'clarification','sparql':None,'reponse':'Précisez un seul médicament de la collection.'}
    root = 'ContreIndication' if contraindications else 'EffetSecondaire'
    predicate = 'aPourContreIndication' if contraindications else 'provoque'
    inverse = 'estContreIndicationDe' if contraindications else 'estProvoquePar'
    domain = 'contraindications' if contraindications else 'side-effects'
    selected = f'VALUES ?medication {{ med:{safe_individual_id(matched[0])} }}' if matched else ''
    linkage = f'{{ ?medication med:{predicate} ?entity }} UNION {{ ?entity med:{inverse} ?medication }}'
    query = PREFIXES+f'''
    SELECT DISTINCT ?entity ?type ?predicate ?value ?medication WHERE {{
        ?entity a ?type . ?type rdfs:subClassOf* med:{root} .
        {selected}
        {('{ '+linkage+' }') if matched else ('OPTIONAL { '+linkage+' }')}
        OPTIONAL {{ ?entity ?predicate ?value . FILTER(?predicate != rdf:type) }}
    }} ORDER BY ?entity
    '''
    records = {}
    for row in select(query):
        local = lambda key: row.get(key,{}).get('value','').split('#')[-1]
        identifier = local('entity')
        item = records.setdefault(identifier,{'id':identifier,'name':identifier.replace('_',' '),'domain':domain,
            'type':local('type'),'description':'Recorded ontology result','properties':{},'relations':[]})
        if 'predicate' in row and 'value' in row:
            if row['value']['type']=='uri':
                relation={'predicate':local('predicate'),'target':local('value')}
                if relation not in item['relations']: item['relations'].append(relation)
            else:
                item['properties'][local('predicate')]=row['value']['value']
    message = f"{len(records)} résultat(s) enregistré(s) dans l'ontologie."
    if contraindications:
        message += " L'absence de contre-indication enregistrée ne prouve pas la sécurité d'un médicament."
    return {**result,'intention':'contraindications_filter' if contraindications else 'side_effects_filter',
        'medicament':matched[0] if matched else None,'sparql':query,'records':list(records.values()),'reponse':message}
