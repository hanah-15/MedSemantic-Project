"""Read-only verification of the official ontology -> Fuseki -> FastAPI chain.

Run with both local servers started. Never creates datasets or uploads triples.
"""

import argparse
from pathlib import Path
import sys

import requests
from rdflib import Graph, Literal, XSD
from rdflib.compare import isomorphic

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.medical_records import build_records  # noqa: E402
from sparql_queries.queries_condition_medicale import select_conditions  # noqa: E402
from sparql_queries.queries_patient import select_patients  # noqa: E402


def normalize_strings(graph: Graph) -> Graph:
    """RDF 1.1 plain strings and xsd:string have the same meaning."""
    normalized = Graph()
    for subject, predicate, value in graph:
        if isinstance(value, Literal) and not value.language and value.datatype in (None, XSD.string):
            value = Literal(str(value), datatype=XSD.string)
        normalized.add((subject, predicate, value))
    return normalized


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ontology', type=Path, required=True)
    parser.add_argument('--fuseki', default='http://localhost:3030/medsemantic')
    parser.add_argument('--api', default='http://127.0.0.1:8000')
    args = parser.parse_args()
    official = Graph().parse(args.ontology)
    response = requests.get(args.fuseki.rstrip('/') + '/get', timeout=15)
    response.raise_for_status()
    live = Graph().parse(data=response.content, format=response.headers['Content-Type'].split(';')[0])
    if not isomorphic(normalize_strings(official), normalize_strings(live)):
        raise RuntimeError('Fuseki default graph differs from the supplied ontology; no data was changed')
    print(f'PASS: Fuseki default graph matches the official ontology ({len(live)} triples)')

    for domain, query in [('patients', select_patients()), ('conditions', select_conditions())]:
        rows = []
        for row in official.query(query):
            rows.append({str(key): {'value': str(value)} for key, value in row.asdict().items()})
        expected = build_records(rows, domain)
        response = requests.get(f'{args.api}/api/{domain}', timeout=15)
        response.raise_for_status()
        if response.json() != expected:
            raise RuntimeError(f'{domain} API response differs from direct official-ontology SPARQL results')
        for record in expected:
            detail = requests.get(f"{args.api}/api/{domain}/{record['id']}", timeout=15)
            detail.raise_for_status()
            if detail.json() != record:
                raise RuntimeError(f"Detail mismatch: {record['id']}")
            if domain == 'patients':
                conditions = requests.get(f"{args.api}/api/patients/{record['id']}/conditions", timeout=15)
                conditions.raise_for_status()
                if conditions.json() != [link['target'] for link in record['relations'] if link['predicate'] == 'aPourCondition']:
                    raise RuntimeError('Patient condition links differ from explicit ontology assertions')
        missing = requests.get(f'{args.api}/api/{domain}/NonexistentIntegrationRecord', timeout=15)
        invalid = requests.get(f'{args.api}/api/{domain}/Bad%29Identifier', timeout=15)
        if missing.status_code != 404 or invalid.status_code != 422:
            raise RuntimeError('Unexpected missing/invalid identifier response')
        print(f'PASS: {len(expected)} {domain}, all details, explicit links and identifier errors')
    docs = requests.get(args.api + '/docs', timeout=15)
    docs.raise_for_status()
    cors = requests.options(args.api + '/api/patients', headers={
        'Origin': 'http://localhost:5174', 'Access-Control-Request-Method': 'GET',
    }, timeout=15)
    if cors.headers.get('access-control-allow-origin') != 'http://localhost:5174':
        raise RuntimeError('Vite origin not allowed')
    print('PASS: Swagger and Vite CORS (5174)')


if __name__ == '__main__':
    main()
