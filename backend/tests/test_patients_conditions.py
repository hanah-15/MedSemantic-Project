from fastapi.testclient import TestClient
from app.services import fuseki
from app.services.medical_records import age_class
from sparql_queries.queries_patient import select_patients
from sparql_queries.queries_condition_medicale import select_conditions
import pytest


def test_patient_query_rejects_injection():
    with pytest.raises(ValueError):
        select_patients('Patient_Karim) . ?s ?p ?o')
    with pytest.raises(ValueError):
        select_conditions('urn:external')


@pytest.mark.parametrize(('age', 'expected'), [
    (0, 'Enfant'), (17, 'Enfant'), (18, 'Adulte'),
    (64, 'Adulte'), (65, 'PersonneAgee'), (None, None), (-1, None),
])
def test_age_category_is_explicit_computation(age, expected):
    assert age_class(age) == expected


def test_patient_collection_uses_ontology(client: TestClient):
    response = client.get('/api/patients')
    assert response.status_code == 200
    patients = response.json()
    assert {p['id'] for p in patients} == {'Patient_Sarah', 'Patient_Karim', 'Patient_Fatma'}
    karim = next(p for p in patients if p['id'] == 'Patient_Karim')
    assert karim['properties']['age'] == '45'
    assert karim['properties']['sexe'] == 'M'
    assert karim['properties']['ageCategory'] == 'Adulte'
    assert {'predicate': 'aPourMaladie', 'target': 'DiabeteType2'} in karim['relations']
    assert {'predicate': 'prend', 'target': 'Glucophage'} in karim['relations']


def test_patient_detail_and_missing(client: TestClient):
    assert client.get('/api/patients/Patient_Sarah').json()['properties']['ageCategory'] == 'Enfant'
    assert client.get('/api/patients/UnknownPerson').status_code == 404
    assert client.get('/api/patients/Bad%29Identifier').status_code == 422


def test_no_invented_patient_conditions(client: TestClient):
    response = client.get('/api/patients/Patient_Karim/conditions')
    assert response.status_code == 200
    assert response.json() == []


def test_medical_conditions_include_subclass_instances(client: TestClient):
    response = client.get('/api/conditions')
    assert response.status_code == 200
    conditions = response.json()
    assert {p['id'] for p in conditions} == {
        'Grossesse_T3', 'InsufRenaleSevere', 'InsufHepatiqueModeree', 'AllergiePenicilline'
    }
    renal = next(p for p in conditions if p['id'] == 'InsufRenaleSevere')
    assert renal['type'] == 'InsuffisanceRenale'
    assert renal['properties']['category'] == 'EtatPathologique'
    assert renal['properties']['severite'] == 'sévère'
    assert client.get('/api/conditions/Grossesse_T3').json()['type'] == 'Grossesse'
    assert client.get('/api/conditions/Unknown').status_code == 404


def test_fuseki_unavailable_returns_503(client: TestClient, monkeypatch):
    def offline(*args):
        raise fuseki.FusekiUnavailable('Cannot query the medsemantic dataset in Fuseki')
    monkeypatch.setattr(fuseki, 'query_select', offline)
    response = client.get('/api/patients')
    assert response.status_code == 503
    assert 'Fuseki' in response.json()['detail']


def test_cors_allows_local_vite(client: TestClient):
    response = client.options('/api/patients', headers={
        'Origin': 'http://localhost:5173',
        'Access-Control-Request-Method': 'GET',
    })
    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == 'http://localhost:5173'


def test_explicit_patient_condition_link_is_returned(client: TestClient, graph):
    from rdflib import URIRef
    ns = 'http://www.semanticweb.org/medsemantic#'
    graph.add((URIRef(ns + 'Patient_Karim'), URIRef(ns + 'aPourCondition'), URIRef(ns + 'InsufRenaleSevere')))
    response = client.get('/api/patients/Patient_Karim/conditions')
    assert response.status_code == 200
    assert response.json() == ['InsufRenaleSevere']
    profile = client.get('/api/patients/Patient_Karim').json()
    assert {'predicate': 'aPourCondition', 'target': 'InsufRenaleSevere'} in profile['relations']


def test_fuseki_query_uses_configured_dataset(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None
        def json(self):
            return {'results': {'bindings': [{'entity': {'type': 'uri', 'value': 'urn:test'}}]}}

    captured = {}
    def fake_post(url, **kwargs):
        captured['url'] = url
        captured.update(kwargs)
        return Response()

    monkeypatch.setenv('FUSEKI_URL', 'http://localhost:3030/medsemantic')
    monkeypatch.setattr(fuseki.requests, 'post', fake_post)
    assert fuseki.query_select('SELECT * WHERE { ?s ?p ?o }') == [{'entity': {'type': 'uri', 'value': 'urn:test'}}]
    assert captured['url'] == 'http://localhost:3030/medsemantic/query'
    assert captured['timeout'] == 12
    assert captured['data']['query'].startswith('SELECT')
