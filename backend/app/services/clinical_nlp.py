"""French clinical questions -> spaCy analysis -> bounded SPARQL templates.

Shares Hana's local French pipeline. Entity aliases come from the RDF dataset,
including individuals added through the clinical forms. No hosted LLM is used.
"""

import re
import unicodedata
from spacy.matcher import PhraseMatcher

from app.services.nlp_service import nlp
from app.services import clinical_editor
from app.services.medical_records import build_records
from sparql_queries._common import NAMESPACE, PREFIXES, safe_individual_id
from sparql_queries.queries_patient import select_patients
from sparql_queries.queries_condition_medicale import select_conditions


def normalize(text: str) -> str:
    text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text).replace('_', ' ')
    return ''.join(char for char in unicodedata.normalize('NFKD',text.lower()) if not unicodedata.combining(char))


def match_entities(text: str, identifiers: list[str], *, patients: bool = False) -> list[str]:
    matcher = PhraseMatcher(nlp.vocab, attr='LOWER')
    for identifier in identifiers:
        aliases = {normalize(identifier)}
        if patients:
            aliases.add(normalize(identifier.removeprefix('Patient_')))
        matcher.add(identifier, [nlp.make_doc(alias) for alias in aliases if alias])
    return sorted({nlp.vocab.strings[match_id] for match_id,_,_ in matcher(nlp.make_doc(normalize(text)))})


def execute(query: str):
    # clinical_editor.select supplies the same shared prefixes as the CRUD routes.
    return clinical_editor.select(query.removeprefix(PREFIXES))


def answer_clinical_question(text: str) -> dict | None:
    doc = nlp(text)
    words = {normalize(token.lemma_ or token.text) for token in doc}
    normalized = normalize(text)
    patient_question = bool(words & {'patient','enfant','adulte','age','agee','prendre','ressentir','symptome','maladie'})
    condition_question = bool(words & {'condition','physiologique','pathologique','grossesse','allaitement','allergie','insuffisance'})
    # A medication-only question remains owned by Hana's translator.
    if not patient_question and not condition_question:
        return None
    if words & {'dosage','dose','composition','galenique'} and not words & {'patient','prendre','ressentir'}:
        return None

    def response(intent: str, answer: str, query: str | None = None, records: list | None = None, **details):
        return {'query':text,'intention':intent,'medicament':None,'reponse':answer,
                'records':records or [],'sparql':query,'analysis':details,
                'tools':['spaCy','fr_core_news_sm','PhraseMatcher','SPARQL templates']}

    if words & {'sans','aucun'} or any(token.dep_ == 'neg' for token in doc) or re.search(r"\b(?:pas|jamais)\b", normalized):
        return response('clarification',"Les questions négatives ne sont pas prises en charge. Une relation absente ne prouve pas l'absence d'une maladie ou d'une condition.")

    patient_rows = execute(select_patients())
    patient_records = build_records(patient_rows,'patients')
    matches = match_entities(text,[record['id'] for record in patient_records],patients=True)
    relation = None
    if words & {'prendre','medicament','traitement'}:
        relation = ('prend','medications','Medicament','Médicaments')
    elif words & {'symptome','ressentir'}:
        relation = ('ressentSymptome','symptoms','Symptome','Symptômes')
    elif 'maladie' in words:
        relation = ('aPourMaladie','diseases','Maladie','Maladies')
    elif 'condition' in words:
        relation = ('aPourCondition','conditions','ConditionMedicale','Conditions')
    targeted = bool(re.search(r'(?:pour|chez|du patient|de patient)\s', normalized))
    if relation and (matches or targeted or words & {'prendre','ressentir','symptome','maladie'} or 'patient' in words and not re.search(r'quels? patients',normalized)):
        if len(matches) != 1:
            return response('clarification','Précisez un seul patient présent dans la collection.',candidates=matches)
        identifier = safe_individual_id(matches[0])
        predicate,domain,root,label = relation
        query = f'''{PREFIXES}SELECT DISTINCT ?target WHERE {{
          med:{identifier} rdf:type/rdfs:subClassOf* med:Patient ; med:{predicate} ?target .
          FILTER(STRSTARTS(STR(?target), "{NAMESPACE}"))
        }} ORDER BY ?target'''
        rows = execute(query)
        records = [{'id':row['target']['value'][len(NAMESPACE):],
                    'name':row['target']['value'][len(NAMESPACE):].replace('_',' '),
                    'domain':domain,'type':root,'description':f'{label} · {identifier.replace("_"," ")}',
                    'properties':{},'relations':[]} for row in rows]
        names = ', '.join(record['name'] for record in records)
        answer = f'{label} enregistrés pour {identifier.replace("_"," ")} : {names}.' if records else f'Aucune relation {predicate} enregistrée pour {identifier.replace("_"," ")}.'
        return response('patient_'+predicate,answer,query,records,patient=identifier,predicate=predicate)

    if patient_question:
        filters = {}
        age_patterns = [
            (r'entre\s+(\d+)\s+et\s+(\d+)', 'between'),
            (r'(?:au moins|a partir de)\s+(\d+)', 'min'),
            (r'plus de\s+(\d+)', 'over'),
            (r'(?:au plus|jusqu.a)\s+(\d+)', 'max'),
            (r'moins de\s+(\d+)', 'under'),
        ]
        for pattern,operator in age_patterns:
            match = re.search(pattern,normalized)
            if match:
                age = int(match[1])
                if operator == 'between': filters = {'min_age':age,'max_age':int(match[2])}
                elif operator in ('min','over'): filters['min_age'] = max(filters.get('min_age',0), age + (operator == 'over'))
                else: filters['max_age'] = min(filters.get('max_age',float('inf')),age - (operator == 'under'))
        if not filters:
            exact=re.search(r'(\d+)\s*ans?',normalized)
            if exact:
                filters={'min_age':int(exact[1]),'max_age':int(exact[1])}
        if 'enfant' in words: filters['age_category'] = 'Enfant'
        elif 'adulte' in words: filters['age_category'] = 'Adulte'
        elif 'agee' in words or 'personnes agees' in normalized: filters['age_category'] = 'PersonneAgee'
        if filters.get('max_age',0) < 0 or filters.get('min_age',0) > filters.get('max_age',float('inf')):
            return response('clarification',"Précisez un intervalle d'âge valide.")
        if 'condition' in words:
            if 'physiologique' in words: filters['condition_type'] = 'EtatPhysiologique'
            elif 'pathologique' in words: filters['condition_type'] = 'EtatPathologique'
            else: filters['condition_type'] = 'ConditionMedicale'
        if not filters and not matches:
            content={normalize(token.lemma_) for token in doc if token.is_alpha and not token.is_stop}
            allowed={'patient','liste','lister','afficher','enregistrer','trouver','base','ontologie','voir','donner','total','nombre','exister'}
            if content - allowed:
                return response('clarification',"Essayez une question sur l'âge des patients, leur catégorie ou leurs conditions enregistrées.")
        query = select_patients(matches[0] if len(matches) == 1 else None,**filters)
        records = build_records(execute(query),'patients')
        return response('patients_filter',f'{len(records)} patient(s) trouvé(s).',query,records,filters=filters)

    category = 'EtatPhysiologique' if 'physiologique' in words else 'EtatPathologique' if 'pathologique' in words else None
    types = clinical_editor.condition_types()
    type_matches = match_entities(text,[item['id'] for item in types])
    # Matching a subclass is sufficient; never invent an unrecorded condition.
    condition_type = type_matches[0] if len(type_matches) == 1 else None
    if not category and not condition_type:
        content={normalize(token.lemma_) for token in doc if token.is_alpha and not token.is_stop}
        allowed={'condition','medical','type','liste','lister','afficher','enregistrer','trouver','base','ontologie','voir','donner','total','nombre','exister'}
        if content - allowed:
            return response('clarification',"Précisez une catégorie physiologique ou pathologique, ou un type de condition présent dans l'ontologie.")
    query = select_conditions(category=category,condition_type=condition_type)
    records = build_records(execute(query),'conditions')
    return response('conditions_filter',f'{len(records)} condition(s) enregistrée(s) trouvée(s).',query,records,
                    category=category,condition_type=condition_type)
