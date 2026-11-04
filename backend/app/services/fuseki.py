"""Fuseki SELECT transport: real responses only, no hard-coded individuals."""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

# Loads backend/.env even if launched from the repository root.
load_dotenv(Path(__file__).resolve().parents[2] / '.env')


class FusekiUnavailable(Exception):
    """Raised when Apache Jena Fuseki cannot respond to a query."""


def query_select(sparql: str) -> list[dict[str, dict[str, str]]]:
    base = os.getenv('FUSEKI_URL', 'http://localhost:3030/medsemantic').rstrip('/')
    endpoint = base if base.endswith('/query') else base + '/query'
    try:
        response = requests.post(
            endpoint,
            data={'query': sparql},
            headers={'Accept': 'application/sparql-results+json'},
            timeout=12,
        )
        response.raise_for_status()
        payload = response.json()
        return payload['results']['bindings']
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        raise FusekiUnavailable('Cannot query the medsemantic dataset in Fuseki') from exc
