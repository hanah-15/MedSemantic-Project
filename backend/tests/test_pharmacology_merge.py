"""Exercise both modules and real SPARQL updates on an isolated RDF graph."""

from pathlib import Path

import pytest
import requests
from fastapi.testclient import TestClient
from rdflib import Graph

from main import app
from app.services.sparql_service import fuseki_endpoint


@pytest.fixture
def pharmacology_graph():
    graph = Graph().parse(Path(__file__).parent / 'fixtures' / 'medsemantic-mini.ttl')
    graph.parse(data='''
        @prefix med: <http://www.semanticweb.org/medsemantic#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        med:Antalgique rdfs:subClassOf med:Medicament .
        med:AntiInflammatoire rdfs:subClassOf med:Medicament .
        med:Antidiabetique rdfs:subClassOf med:Medicament .
        med:Antihypertenseur rdfs:subClassOf med:Medicament .
        med:Doliprane a med:Antalgique ; med:nomCommercial "Doliprane" ;
          med:dosage "1000 mg" ; med:formeGalenique "comprimé" ;
          med:contientPrincipeActif med:Paracetamol ; med:contientExcipient med:Lactose .
        med:Advil a med:Antalgique, med:AntiInflammatoire ; med:nomCommercial "Advil" ;
          med:dosage "400 mg" ; med:formeGalenique "comprimé" ; med:contientPrincipeActif med:Ibuprofene .
        med:Glucophage a med:Antidiabetique ; med:nomCommercial "Glucophage" ;
          med:dosage "850 mg" ; med:formeGalenique "comprimé" .
        med:Amlor a med:Antihypertenseur ; med:nomCommercial "Amlor" ;
          med:dosage "5 mg" ; med:formeGalenique "gélule" .
        med:Paracetamol med:formuleChimique "C8H9NO2" .
        med:Lactose med:formuleChimique "C12H22O11" .
    ''',format='turtle')
    return graph


@pytest.fixture
def merged_client(pharmacology_graph, monkeypatch):
    def post(url, *, data, **kwargs):
        response = requests.Response()
        response.status_code = 200
        if 'query' in data:
            assert url.endswith('/query')
            rows = pharmacology_graph.query(data['query'])
            response._content = rows.serialize(format='json')
        else:
            assert url.endswith('/update')
            pharmacology_graph.update(data['update'])
            response._content = b'{}'
        return response
    monkeypatch.setattr(requests,'post',post)
    return TestClient(app)


def test_both_modules_and_multiclass_medication_are_preserved(merged_client):
    assert len(merged_client.get('/api/patients').json()) == 3
    assert len(merged_client.get('/api/conditions').json()) == 4
    medications = merged_client.get('/api/medicaments/').json()
    assert len(medications) == 4
    assert [item['uri'] for item in medications].count('Advil') == 1


def test_medication_details_and_composition(merged_client):
    detail = merged_client.get('/api/medicaments/details/Doliprane')
    assert detail.status_code == 200
    assert detail.json()['dosage'] == '1000 mg'
    composition = merged_client.get('/api/medicaments/Doliprane')
    assert composition.status_code == 200
    assert {molecule['nom'] for molecule in composition.json()} == {'Paracetamol','Lactose'}
    assert detail.json()['molecules'] == composition.json()


def test_crud_round_trip_preserves_other_records_and_literal_values(merged_client):
    patients = merged_client.get('/api/patients').json()
    original = merged_client.get('/api/medicaments/details/Doliprane').json()
    name = 'Essai "médicament"\navec guillemets'
    payload = {'uri':'Merge_Test', 'nom_commercial':name, 'dosage':'10 mg', 'forme_galenique':'sirop',
               'molecules':[{'nom':'TestMolecule','type_molecule':'Principe actif','formule_chimique':'C2H6'}]}
    created = merged_client.post('/api/medicaments/',json=payload)
    assert created.status_code == 201, created.text
    detail = merged_client.get('/api/medicaments/details/Merge_Test').json()
    assert detail['nom_commercial'] == name
    assert detail['molecules'][0]['formule_chimique'] == 'C2H6'
    updated = merged_client.put('/api/medicaments/Merge_Test',json={'dosage':'20 mg','nom_commercial':'Nom "modifié"'})
    assert updated.status_code == 200, updated.text
    assert merged_client.get('/api/medicaments/details/Merge_Test').json()['dosage'] == '20 mg'
    assert merged_client.post('/api/medicaments/',json=payload).status_code == 400
    assert merged_client.delete('/api/medicaments/Merge_Test').status_code == 200
    assert merged_client.get('/api/medicaments/details/Merge_Test').status_code == 404
    assert merged_client.get('/api/medicaments/details/Doliprane').json() == original
    assert merged_client.get('/api/patients').json() == patients


@pytest.mark.parametrize(('question','intention','answer'),[
    ('Quel est le dosage du Doliprane ?', 'dosage', '1000 mg'),
    ("Quelle est la composition de l'Advil ?", 'composition', 'Ibuprofene'),
    ('Forme galénique du Glucophage', 'forme_galenique', 'comprimé'),
])
def test_nlp_uses_the_same_sparql_dataset(merged_client, question, intention, answer):
    response = merged_client.get('/api/recherche/',params={'q':question})
    assert response.status_code == 200
    assert response.json()['intention'] == intention
    assert answer in response.json()['reponse']


@pytest.mark.parametrize('method',['GET','POST','PUT','DELETE'])
def test_local_frontend_can_access_both_read_and_write_routes(merged_client, method):
    response = merged_client.options('/api/medicaments/',headers={
        'Origin':'http://localhost:5173','Access-Control-Request-Method':method,
        'Access-Control-Request-Headers':'content-type',
    })
    assert response.status_code == 200


@pytest.mark.parametrize('suffix',['','/query','/sparql'])
def test_transport_accepts_dataset_and_query_urls(monkeypatch,suffix):
    monkeypatch.setenv('FUSEKI_URL','http://localhost:3030/team_dataset'+suffix)
    monkeypatch.delenv('FUSEKI_QUERY_URL',raising=False)
    monkeypatch.delenv('FUSEKI_UPDATE_URL',raising=False)
    assert fuseki_endpoint('query') == 'http://localhost:3030/team_dataset/query'
    assert fuseki_endpoint('update') == 'http://localhost:3030/team_dataset/update'


def test_pharmacology_outage_is_not_reported_as_an_empty_dataset(monkeypatch):
    def offline(*args,**kwargs):
        raise requests.ConnectionError('offline')
    monkeypatch.setattr(requests,'post',offline)
    response = TestClient(app).get('/api/medicaments/')
    assert response.status_code == 503
