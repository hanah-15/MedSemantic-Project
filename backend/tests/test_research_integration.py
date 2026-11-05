"""Run the merged research routes against the project's actual ontology."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from rdflib import Graph

from app.routes import etudes, resultats
from main import app


@pytest.fixture
def research_client(monkeypatch):
    graph = Graph().parse(Path(__file__).resolve().parents[2] / 'ontology' / 'MedSemantic.owl')

    def query(sparql):
        return json.loads(graph.query(sparql).serialize(format='json'))['results']['bindings']

    monkeypatch.setattr(etudes, 'execute_sparql', query)
    monkeypatch.setattr(resultats, 'execute_sparql', query)
    return TestClient(app)


@pytest.mark.parametrize(('path', 'expected'), [
    ('/etudes/', {'Essai_Metformine_2024', 'Etude_Paracetamol_Obs'}),
    ('/etudes/type/EssaiClinique', {'Essai_Metformine_2024'}),
    ('/etudes/type/EtudeObservationnelle', {'Etude_Paracetamol_Obs'}),
    ('/etudes/phase/3', {'Essai_Metformine_2024'}),
    ('/etudes/sans-resultat', {'Etude_Paracetamol_Obs'}),
    ('/etudes/comparatives/liste', {'Essai_Metformine_2024'}),
    ('/etudes/medicament/Glucophage', {'Essai_Metformine_2024'}),
    ('/etudes/maladie/DiabeteType2', {'Essai_Metformine_2024'}),
    ('/etudes/annee/recherche?annee_min=2024', {'Essai_Metformine_2024'}),
    ('/etudes/participants/minimum?n=1000', {'Etude_Paracetamol_Obs'}),
    ('/resultats/', {'Res_Efficacite_Glucophage', 'Res_Tolerance_Glucophage'}),
    ('/resultats/type/efficacite', {'Res_Efficacite_Glucophage'}),
    ('/resultats/type/securite', {'Res_Tolerance_Glucophage'}),
    ('/resultats/type/tolerance', {'Res_Tolerance_Glucophage'}),
    ('/resultats/medicament/Glucophage', {'Res_Efficacite_Glucophage', 'Res_Tolerance_Glucophage'}),
])
def test_research_filters_use_real_assertions(research_client, path, expected):
    response = research_client.get(path)
    assert response.status_code == 200, response.text
    assert {item['id'] for item in response.json()} == expected


def test_study_result_links_and_missing_values(research_client):
    study = research_client.get('/etudes/Essai_Metformine_2024').json()
    assert study['participants'] == 500
    assert study['phase'] == 3
    assert {r['id'] for r in study['resultats']} == {'Res_Efficacite_Glucophage', 'Res_Tolerance_Glucophage'}
    observation = research_client.get('/etudes/Etude_Paracetamol_Obs').json()
    assert observation['phase'] is None
    assert observation['maladie_id'] is None
    assert observation['resultats'] == []
    result = research_client.get('/resultats/Res_Tolerance_Glucophage').json()
    assert result['valeur'] == 85
    assert result['etude_id'] == study['id']
    assert result['medicament_id'] == 'Glucophage'


def test_research_aggregates_and_missing_records(research_client):
    stats = {s['type_etude']: s for s in research_client.get('/etudes/stats').json()}
    assert stats['EssaiClinique']['nombre_etudes'] == 1
    assert stats['EtudeObservationnelle']['moyenne_participants'] == 1200
    assert sum(s['nombre_resultats'] for s in research_client.get('/resultats/stats').json()) == 2
    assert research_client.get('/etudes/UnknownStudy').status_code == 404
    assert research_client.get('/resultats/UnknownResult').status_code == 404
