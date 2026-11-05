"""Exercise Mariem's routes with real SPARQL against an isolated ontology graph."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from rdflib import Graph, URIRef

from app.routes import clinical
from main import app

NS = 'http://www.semanticweb.org/medsemantic#'


@pytest.fixture
def disease_client(monkeypatch):
    graph = Graph().parse(Path(__file__).resolve().parents[2] / 'ontology' / 'MedSemantic.owl')
    # Existing installations need no extra class settings for this ontology.
    monkeypatch.delenv('DISEASE_CLASS_URI', raising=False)
    monkeypatch.delenv('SYMPTOM_CLASS_URI', raising=False)

    def query(sparql):
        return json.loads(graph.query(sparql).serialize(format='json'))['results']['bindings']

    monkeypatch.setattr(clinical, 'query_fuseki', query)
    monkeypatch.setattr(clinical, 'ask_fuseki', lambda sparql: bool(graph.query(sparql).askAnswer))
    monkeypatch.setattr(clinical, 'update_fuseki', graph.update)
    return TestClient(app), graph


@pytest.mark.parametrize(('path', 'expected'), [
    ('/api/diseases', {'Grippe', 'DiabeteType2', 'Hypertension', 'Asthme'}),
    ('/api/symptoms', {'Fievre', 'Toux', 'Nausee'}),
    ('/api/diseases?symptom=Toux', {'Grippe', 'Asthme'}),
    ('/api/diseases?q=E11', {'DiabeteType2'}),
    ('/api/diseases?q=grippe', {'Grippe'}),
    ('/api/symptoms?q=absent', set()),
])
def test_list_search_and_subclasses(disease_client, path, expected):
    client, _ = disease_client
    response = client.get(path)
    assert response.status_code == 200, response.text
    assert {record['uri'].split('#')[-1] for record in response.json()} == expected


def test_create_patch_replace_and_delete(disease_client):
    client, graph = disease_client
    baseline = set(graph)
    symptom = client.post('/api/symptoms', json={'id':'NewSymptom','properties':{'intensite':['moderate']}})
    assert symptom.status_code == 201, symptom.text
    created = client.post('/api/diseases', json={
        'id':'NewDisease', 'properties':{'codeCIM10':['X00'],'estChronique':[False],'presenteSymptome':['NewSymptom']},
    })
    assert created.status_code == 201, created.text
    assert client.get('/api/diseases?symptom=NewSymptom').json()[0]['uri'] == NS+'NewDisease'
    assert client.post('/api/diseases', json={'id':'NewDisease'}).status_code == 409
    changed = client.patch('/api/diseases/NewDisease', json={'properties':{'estChronique':[True]}})
    assert changed.status_code == 200, changed.text
    props = {p['predicate'].split('#')[-1]:p for p in changed.json()['properties']}
    assert props['estChronique']['value'] == 'true'
    assert props['estChronique']['datatype'].endswith('#boolean')
    assert props['codeCIM10']['value'] == 'X00'
    assert client.delete('/api/symptoms/NewSymptom').status_code == 204
    assert not list(graph.triples((None, URIRef(NS+'presenteSymptome'),URIRef(NS+'NewSymptom'))))
    replaced = client.put('/api/diseases/NewDisease', json={'properties':{'codeCIM10':['X01']}})
    assert replaced.status_code == 200, replaced.text
    assert [p['value'] for p in replaced.json()['properties']] == ['X01']
    assert client.delete('/api/diseases/NewDisease').status_code == 204
    assert client.get('/api/diseases/NewDisease').status_code == 404
    assert set(graph) == baseline


@pytest.mark.parametrize('properties', [
    {'estChronique':['true']}, {'codeCIM10':[123]}, {'unknown':['x']},
    {'presenteSymptome':['NoSuchSymptom']}, {'presenteSymptome':['Glucophage']},
])
def test_invalid_properties_do_not_write(disease_client, properties):
    client, graph = disease_client
    baseline = set(graph)
    response = client.post('/api/diseases', json={'id':'InvalidDisease','properties':properties})
    assert response.status_code == 422, response.text
    assert set(graph) == baseline


def test_escaped_literals_and_collisions(disease_client):
    client, graph = disease_client
    literal = 'quote " slash \\ newline\n } DELETE WHERE { ?s ?p ?o }'
    created = client.post('/api/symptoms', json={'id':'QuotedSymptom','properties':{'intensite':[literal]}})
    assert created.status_code == 201, created.text
    assert created.json()['properties'][0]['value'] == literal
    assert client.get('/api/symptoms', params={'q':'" } DELETE WHERE { ?s ?p ?o }'}).status_code == 200
    assert client.post('/api/diseases', json={'id':'Fievre'}).status_code == 409
    assert len(graph) > 500


def test_patch_preflight_is_allowed():
    response = TestClient(app).options('/api/diseases/Grippe',headers={
        'Origin':'http://localhost:5173','Access-Control-Request-Method':'PATCH',
    })
    assert response.status_code == 200
