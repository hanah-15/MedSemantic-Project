"""Fuseki SELECT transport: real responses only, no hard-coded individuals."""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

# Loads backend/.env even if launched from the repository root.
load_dotenv(Path(__file__).resolve().parents[2] / '.env')


class FusekiUnavailable(Exception):
    """Raised when Apache Jena Fuseki cannot respond to a query."""


def endpoint_for(operation: str) -> str:
    base = os.getenv('FUSEKI_URL', 'http://localhost:3030/medsemantic').rstrip('/')
    for suffix in ('/query', '/sparql', '/update'):
        if base.endswith(suffix):
            base = base[:-len(suffix)]
            break
    return os.getenv(f'FUSEKI_{operation.upper()}_URL') or base + '/' + operation


def query_select(sparql: str) -> list[dict[str, dict[str, str]]]:
    try:
        response = requests.post(
            endpoint_for('query'),
            data={'query': sparql},
            headers={'Accept': 'application/sparql-results+json'},
            timeout=12,
        )
        response.raise_for_status()
        payload = response.json()
        bindings = payload['results']['bindings']
        if not isinstance(bindings, list) or any(
            not isinstance(row, dict) or any(
                not isinstance(term, dict) or not isinstance(term.get('value'), str)
                for term in row.values()
            ) for row in bindings
        ):
            raise ValueError('Invalid SPARQL result bindings')
        return bindings
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        raise FusekiUnavailable('Cannot query the medsemantic dataset in Fuseki') from exc


def query_update(sparql: str) -> None:
    try:
        response = requests.post(endpoint_for('update'), data={'update': sparql}, timeout=12)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FusekiUnavailable('Records could not be saved. Please try again.') from exc
