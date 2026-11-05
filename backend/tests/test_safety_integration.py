"""Check semantic results on the official ontology, not canned HTTP bindings."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from rdflib import Graph, Namespace, Literal
from rdflib.plugins.sparql import prepareQuery
from rdflib.namespace import RDF

from app.routes import effets_secondaires, contre_indications, molecules
from app.services import safety_nlp
from main import app
from sparql_queries.queries_effet_secondaire import requete_effets_par_gravite, requete_effets_par_frequence

NS = Namespace('http://www.semanticweb.org/medsemantic#')


@pytest.fixture
def safety_client(monkeypatch):
    graph = Graph().parse(Path(__file__).resolve().parents[2]/'ontology'/'MedSemantic.owl')
    def query(sparql):
        return json.loads(graph.query(sparql).serialize(format='json'))['results']['bindings']
    for module in [effets_secondaires,contre_indications]:
        monkeypatch.setattr(module,'execute_sparql',query)
    monkeypatch.setattr(molecules,'query_select',query)
    monkeypatch.setattr(safety_nlp,'query_select',query)
    return TestClient(app),graph


@pytest.mark.parametrize(('path','expected'),[
    ('/api/effets-secondaires',{'TroublesGastriques','Oedemes','EruptionCutanee'}),
    ('/api/effets-secondaires?type_effet=digestif&frequence=rare',set()),
    ('/api/effets-secondaires?type_effet=digestif&medicament=Glucophage',{'TroublesGastriques'}),
    ('/api/effets-secondaires/medicament/Glucophage',{'TroublesGastriques'}),
    ('/api/effets-secondaires/symptome/Nausee',{'TroublesGastriques'}),
    ('/api/contre-indications?type_ci=relative&medicament=Advil',set()),
    ('/api/contre-indications?type_ci=absolue&medicament=Advil',{'CI_Ibuprofene_Grossesse'}),
    ('/api/contre-indications?condition=InsufRenaleSevere',{'CI_Metformine_InsufRenale'}),
    ('/api/contre-indications/medicament/Glucophage',{'CI_Metformine_InsufRenale'}),
    ('/api/molecules',{'Paracetamol','Metformine','Amlodipine','Ibuprofene','Lactose','NAPQI'}),
])
def test_collections_and_combined_filters(safety_client,path,expected):
    client,_=safety_client
    response=client.get(path)
    assert response.status_code==200,response.text
    assert {item['id'] for item in response.json()}==expected


def test_effect_detail_and_medication_links(safety_client):
    client,_=safety_client
    record=client.get('/api/effets-secondaires/TroublesGastriques').json()
    assert record['symptomes'][0]['id']=='Nausee'
    assert record['medicaments'][0]['id']=='Glucophage'
    filtered=client.get('/api/effets-secondaires/medicament/Glucophage').json()
    assert filtered[0]['medicaments_lies']==['Glucophage']
    ci=client.get('/api/contre-indications/CI_Ibuprofene_Grossesse').json()
    assert ci['conditions_concernees'][0]['id']=='Grossesse_T3'


def test_contraindication_matches_only_asserted_patient_links(safety_client):
    client,graph=safety_client
    path='/api/contre-indications/verifier/Patient_Karim/Glucophage'
    assert client.get(path).json()['est_contre_indique'] is False
    graph.add((NS.Patient_Karim,NS.aPourCondition,NS.InsufRenaleSevere))
    alert=client.get(path).json()
    assert alert['est_contre_indique'] is True
    assert alert['alertes'][0]['contre_indication_id']=='CI_Metformine_InsufRenale'


def test_molecule_metabolism_and_incoming_composition(safety_client):
    client,_=safety_client
    record=client.get('/api/molecules/Paracetamol').json()
    assert record['properties']['formuleChimique']=='C8H9NO2'
    assert {'predicate':'seMetaboliseEn','target':'NAPQI'} in record['relations']
    assert any(link['source']=='Doliprane' for link in record['incomingRelations'])
    assert client.get('/api/molecules/NoSuchMolecule').status_code==404
    assert client.get('/api/molecules/Bad)Id').status_code==422


@pytest.mark.parametrize('builder',[requete_effets_par_gravite,requete_effets_par_frequence])
def test_filter_literals_cannot_escape_the_query(builder,safety_client):
    _,graph=safety_client
    for value in ['quote " slash \\ newline\n', '\\") } UNION { ?s ?p ?o } #']:
        query=builder(value)
        prepareQuery(query)
        assert list(graph.query(query))==[]


def test_invalid_types_cannot_query_another_root_class(safety_client):
    client,_=safety_client
    assert client.get('/api/effets-secondaires?type_effet=Medicament').status_code==422
    assert client.get('/api/contre-indications?type_ci=Patient').status_code==422


@pytest.mark.parametrize(('question','expected'),[
    ('Quels effets secondaires du Glucophage ?',{'TroublesGastriques'}),
    ('Quelles contre-indications pour Advil ?',{'CI_Ibuprofene_Grossesse'}),
])
def test_local_safety_nlp_executes_its_returned_query(safety_client,question,expected):
    client,graph=safety_client
    response=client.get('/api/recherche/',params={'q':question})
    assert response.status_code==200,response.text
    answer=response.json()
    assert {item['id'] for item in answer['records']}==expected
    assert 'spaCy' in answer['tools']
    direct={str(row['entity']).split('#')[-1] for row in graph.query(answer['sparql'])}
    assert direct==expected


def test_absence_question_does_not_claim_medication_safety(safety_client):
    client,_=safety_client
    answer=client.get('/api/recherche/',params={'q':'Quels médicaments sont sans contre-indication ?'}).json()
    assert answer['intention']=='clarification'
    assert answer['sparql'] is None
    assert answer['records']==[]
