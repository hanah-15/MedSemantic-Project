"""Shared SPARQL helpers. Never interpolate unvalidated user input in a query."""

import re
from rdflib import Literal

NAMESPACE = "http://www.semanticweb.org/medsemantic#"
PREFIXES = f"""PREFIX med: <{NAMESPACE}>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""

# Ontology individual IDs, not URIs or arbitrary SPARQL fragments.
_VALID_LOCAL_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def safe_individual_id(identifier: str) -> str:
    if not _VALID_LOCAL_NAME.fullmatch(identifier):
        raise ValueError("Invalid ontology individual identifier")
    return identifier


def literal(value: str | int) -> str:
    return Literal(value).n3()
