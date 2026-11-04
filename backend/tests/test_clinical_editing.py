"""Clinical CRUD, SPARQL filters and local NLP on isolated ontology graphs."""

import pytest
from rdflib import Namespace, RDF, RDFS, Literal, OWL
from app.services import fuseki

med = Namespace('http://www.semanticweb.org/medsemantic#')


@pytest.fixture
def clinical_client(client,graph):
    for identifier,root in [('Doliprane','Medicament'),('Glucophage','Medicament'),('Amlor','Medicament'),
                            ('DiabeteType2','Maladie'),('Fievre','Symptome')]:
        graph.add((med[identifier],RDF.type,med[root]))
    graph.add((med.Allaitement,RDFS.subClassOf,med.EtatPhysiologique))
    return client


def test_patient_crud_preserves_unowned_attributes_and_updates_age_category(clinical_client,graph):
    before=set(graph)
    created=clinical_client.post('/api/patients',json={'id':'Patient_Test','age':17,'sexe':'F',
        'aPourMaladie':['DiabeteType2'],'prend':['Glucophage'],'ressentSymptome':['Fievre']})
    assert created.status_code == 201,created.text
    assert created.json()['properties']['ageCategory'] == 'Enfant'
    graph.add((med.Patient_Test,RDFS.label,Literal('Keep this label')))
    edited=clinical_client.put('/api/patients/Patient_Test',json={'age':65,'sexe':'M','prend':['Doliprane']})
    assert edited.status_code == 200,edited.text
    assert edited.json()['properties']['ageCategory'] == 'PersonneAgee'
    assert edited.json()['relations'] == [{'predicate':'prend','target':'Doliprane'}]
    assert (med.Patient_Test,RDFS.label,Literal('Keep this label')) in graph
    assert len(list(graph.objects(med.Patient_Test,med.age))) == 1
    assert clinical_client.delete('/api/patients/Patient_Test').status_code == 204
    assert clinical_client.get('/api/patients/Patient_Test').status_code == 404
    assert set(graph) == before


def test_conditions_crud_and_explicit_patient_links(clinical_client,graph):
    original=set(graph)
    severity='sévère "documentée"\nsans interprétation'
    response=clinical_client.post('/api/conditions',json={'id':'Condition_Test','type':'InsuffisanceRenale','severite':severity})
    assert response.status_code == 201,response.text
    assert response.json()['properties']['severite'] == severity
    assert response.json()['properties']['category'] == 'EtatPathologique'
    assert clinical_client.post('/api/patients',json={'id':'Patient_Test','age':30,'sexe':'F','aPourCondition':['Condition_Test']}).status_code == 201
    assert clinical_client.get('/api/patients/Patient_Test/conditions').json() == ['Condition_Test']
    updated=clinical_client.put('/api/conditions/Condition_Test',json={'type':'Allaitement','severite':None})
    assert updated.status_code == 200,updated.text
    assert updated.json()['type'] == 'Allaitement'
    assert updated.json()['properties']['category'] == 'EtatPhysiologique'
    assert 'severite' not in updated.json()['properties']
    assert len(updated.json()['incomingRelations']) == 1
    assert clinical_client.delete('/api/conditions/Condition_Test').status_code == 204
    assert clinical_client.get('/api/patients/Patient_Test/conditions').json() == []
    assert (med.Allaitement,RDFS.subClassOf,med.EtatPhysiologique) in graph
    assert clinical_client.delete('/api/patients/Patient_Test').status_code == 204
    assert set(graph) == original


@pytest.mark.parametrize('payload',[
    {'id':'Patient_Bad','age':-1,'sexe':'F'},
    {'id':'Patient_Bad','age':2.5,'sexe':'F'},
    {'id':'Patient_Bad','age':True,'sexe':'F'},
    {'id':'Patient_Bad','age':20,'sexe':'   '},
    {'id':'Bad) . ?s ?p ?o','age':20,'sexe':'M'},
    {'id':'Patient_Bad','age':20,'sexe':'F','prend':['Grossesse_T3']},
    {'id':'Patient_Bad','age':20,'sexe':'F','aPourCondition':['Missing']},
])
def test_invalid_patient_writes_do_not_change_the_graph(clinical_client,graph,payload):
    before=set(graph)
    assert clinical_client.post('/api/patients',json=payload).status_code == 422
    assert set(graph) == before


def test_collision_wrong_class_and_missing_records(clinical_client,graph):
    before=set(graph)
    assert clinical_client.post('/api/patients',json={'id':'Patient_Karim','age':20,'sexe':'M'}).status_code == 409
    assert clinical_client.post('/api/conditions',json={'id':'Patient','type':'Allergie'}).status_code == 409
    assert clinical_client.post('/api/conditions',json={'id':'Condition_Test','type':'InventedClass'}).status_code == 422
    assert clinical_client.delete('/api/patients/Patient').status_code == 404
    assert clinical_client.put('/api/conditions/Missing',json={'type':'Allergie'}).status_code == 404
    assert clinical_client.delete('/api/conditions/Missing').status_code == 404
    assert set(graph) == before


def test_actual_ontology_options(clinical_client):
    options=clinical_client.get('/api/patients/options')
    assert options.status_code == 200
    assert {'id':'Glucophage','name':'Glucophage'} in options.json()['prend']
    types=clinical_client.get('/api/conditions/types').json()
    assert {'id':'Allaitement','parent':'EtatPhysiologique'} in types


@pytest.mark.parametrize(('params','expected'),[
    ({'min_age':65},['Patient_Fatma']),
    ({'max_age':17},['Patient_Sarah']),
    ({'min_age':18,'max_age':64},['Patient_Karim']),
    ({'age_category':'Enfant'},['Patient_Sarah']),
    ({'sexe':'M','q':'karim'},['Patient_Karim']),
    ({'q':'" } UNION { ?s ?p ?o } #'},[]),
])
def test_patient_filtering_happens_in_sparql(clinical_client,params,expected):
    result=clinical_client.get('/api/patients',params=params)
    assert result.status_code == 200,result.text
    assert [item['id'] for item in result.json()] == expected


@pytest.mark.parametrize(('params','expected'),[
    ({'category':'EtatPhysiologique'},['Grossesse_T3']),
    ({'condition_type':'Allergie'},['AllergiePenicilline']),
    ({'severity':'sévère'},['InsufRenaleSevere']),
    ({'q':'Grossesse'},['Grossesse_T3']),
    ({'q':'Insuf Renale'},['InsufRenaleSevere']),
])
def test_condition_filtering_happens_in_sparql(clinical_client,params,expected):
    result=clinical_client.get('/api/conditions',params=params)
    assert result.status_code == 200,result.text
    assert [item['id'] for item in result.json()] == expected


def test_invalid_filter_values_are_rejected(clinical_client):
    for params in [{'min_age':-1},{'min_age':50,'max_age':20},{'age_category':'Unknown'}]:
        assert clinical_client.get('/api/patients',params=params).status_code == 422
    assert clinical_client.get('/api/conditions',params={'category':'Unknown'}).status_code == 422


@pytest.mark.parametrize(('question','expected'),[
    ('Quels médicaments prend Karim ?', ['Glucophage']),
    ('Quels symptômes ressent Sarah ?', ['Fievre']),
    ('Quelles maladies a Karim ?', ['DiabeteType2']),
    ('Quels patients ont plus de 65 ans ?', ['Patient_Fatma']),
    ('Quels patients ont entre 18 et 64 ans ?', ['Patient_Karim']),
    ('Quels patients sont âgés de 45 ans ?', ['Patient_Karim']),
    ('Quels patients ont plus de 40 ans et moins de 65 ans ?', ['Patient_Karim']),
    ('Quels patients sont des enfants ?', ['Patient_Sarah']),
    ('Quelles conditions sont physiologiques ?', ['Grossesse_T3']),
    ('Quelles conditions sont de type allergie ?', ['AllergiePenicilline']),
])
def test_clinical_questions_generate_executable_sparql(clinical_client,graph,question,expected):
    response=clinical_client.get('/api/recherche/',params={'q':question})
    assert response.status_code == 200,response.text
    body=response.json()
    assert [item['id'] for item in body['records']] == expected,body
    assert body['sparql'].startswith('PREFIX')
    assert list(graph.query(body['sparql']))
    assert 'spaCy' in body['tools']


def test_nlp_recognizes_new_individuals_and_empty_links(clinical_client):
    assert clinical_client.post('/api/patients',json={'id':'Patient_Nadia','age':65,'sexe':'F','prend':['Doliprane']}).status_code == 201
    result=clinical_client.get('/api/recherche/',params={'q':'Quels médicaments prend Nadia ?'}).json()
    assert [item['id'] for item in result['records']] == ['Doliprane']
    condition=clinical_client.get('/api/recherche/',params={'q':'Quelles conditions a Karim ?'}).json()
    assert condition['records'] == []
    assert 'Aucune relation aPourCondition enregistrée' in condition['reponse']
    unknown=clinical_client.get('/api/recherche/',params={'q':'Quels médicaments prend Inconnu ?'}).json()
    assert unknown['intention'] == 'clarification'
    assert unknown['records'] == []


@pytest.mark.parametrize('question',['Quels patients sont diabétiques ?', 'Quels patients n’ont pas de condition ?', 'Quels patients sans maladie ?'])
def test_nlp_does_not_silently_ignore_unsupported_constraints(clinical_client,question):
    body=clinical_client.get('/api/recherche/',params={'q':question}).json()
    assert body['intention'] == 'clarification'
    assert body['records'] == []


def test_write_outage_returns_503_without_success(clinical_client,monkeypatch):
    def offline(query):
        raise fuseki.FusekiUnavailable('unavailable')
    monkeypatch.setattr(fuseki,'query_update',offline)
    response=clinical_client.post('/api/conditions',json={'id':'Condition_Test','type':'Allergie'})
    assert response.status_code == 503


def test_query_and_update_share_configured_dataset(monkeypatch):
    monkeypatch.setenv('FUSEKI_URL','http://localhost:3030/custom/sparql')
    monkeypatch.delenv('FUSEKI_QUERY_URL',raising=False)
    monkeypatch.delenv('FUSEKI_UPDATE_URL',raising=False)
    assert fuseki.endpoint_for('query') == 'http://localhost:3030/custom/query'
    assert fuseki.endpoint_for('update') == 'http://localhost:3030/custom/update'
