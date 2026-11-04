"""Offline tests use real SPARQL evaluation, not hand-written fake results."""

import os
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient
from rdflib import Graph, URIRef, Literal

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services import fuseki  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture
def graph() -> Graph:
    graph = Graph()
    external = os.environ.get('MEDSEMANTIC_OWL_PATH')
    path = Path(external) if external else Path(__file__).parent / 'fixtures' / 'medsemantic-mini.ttl'
    graph.parse(path, format='turtle' if path.suffix == '.ttl' else None)
    return graph


@pytest.fixture
def client(graph: Graph, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    def fake_query(query: str):
        results = graph.query(query)
        bindings = []
        for row in results:
            binding = {}
            for key, value in row.asdict().items():
                if isinstance(value, URIRef):
                    binding[str(key)] = {'type': 'uri', 'value': str(value)}
                elif isinstance(value, Literal):
                    binding[str(key)] = {'type': 'literal', 'value': str(value)}
            bindings.append(binding)
        return bindings
    monkeypatch.setattr(fuseki, 'query_select', fake_query)
    monkeypatch.setattr(fuseki, 'query_update', graph.update)
    return TestClient(app)
