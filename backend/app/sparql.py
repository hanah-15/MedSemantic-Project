import os
import re
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlsplit

from dotenv import load_dotenv
from rdflib import Literal, URIRef
from SPARQLWrapper import JSON, POST, SPARQLWrapper
from SPARQLWrapper.SPARQLExceptions import SPARQLWrapperException

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

_LOCAL_ID = re.compile(r"^[A-Za-z][A-Za-z0-9._~-]{0,99}$")
_RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
_RDFS_SUBCLASS = "http://www.w3.org/2000/01/rdf-schema#subClassOf"
_RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"
_RDFS_COMMENT = "http://www.w3.org/2000/01/rdf-schema#comment"


class FusekiConfigurationError(Exception):
    pass


class FusekiQueryError(Exception):
    pass


def validate_uri(value: str, name: str) -> str:
    parsed = urlsplit(value)
    forbidden_characters = '<>"{}|^`\\'
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or value != value.strip()
        or any(char in forbidden_characters or ord(char) <= 0x20 for char in value)
    ):
        raise ValueError(f"{name} must be an absolute HTTP or HTTPS URI")
    return f"<{value}>"


def namespace_for(class_uri: str) -> str:
    validate_uri(class_uri, "class_uri")
    if "#" in class_uri:
        return class_uri.rsplit("#", 1)[0] + "#"
    return class_uri.rsplit("/", 1)[0] + "/"


def instance_uri(class_uri: str, entity_id: str) -> str:
    if not _LOCAL_ID.fullmatch(entity_id):
        raise ValueError("id must start with a letter and contain only letters, digits, '.', '_', '~', or '-'")
    return namespace_for(class_uri) + entity_id


def _literal(value: str | int | bool, datatype: str) -> str:
    return Literal(value, datatype=URIRef(datatype)).n3()


def build_instances_query(
    class_uri: str,
    entity_uri: str | None = None,
    search: str | None = None,
    symptom_uri: str | None = None,
) -> str:
    class_ref = validate_uri(class_uri, "class_uri")
    entity_filter = ""
    if entity_uri is not None:
        entity_filter = f"VALUES ?entity {{ {validate_uri(entity_uri, 'uri')} }}"

    filters = []
    if search:
        search_literal = Literal(search.casefold()).n3()
        filters.append(
            f"""
                FILTER(
                    CONTAINS(LCASE(STR(?entity)), {search_literal}) ||
                    EXISTS {{
                        ?entity <{_RDFS_LABEL}> ?searchLabel .
                        FILTER(CONTAINS(LCASE(STR(?searchLabel)), {search_literal}))
                    }} ||
                    EXISTS {{
                        ?entity <{_RDFS_COMMENT}> ?searchComment .
                        FILTER(CONTAINS(LCASE(STR(?searchComment)), {search_literal}))
                    }} ||
                    EXISTS {{
                        ?entity ?searchPredicate ?searchValue .
                        FILTER(isLiteral(?searchValue) &&
                               CONTAINS(LCASE(STR(?searchValue)), {search_literal}))
                    }}
                )
            """
        )
    if symptom_uri is not None:
        relation_uri = namespace_for(class_uri) + "presenteSymptome"
        filters.append(
            f"FILTER EXISTS {{ ?entity {validate_uri(relation_uri, 'relation_uri')} "
            f"{validate_uri(symptom_uri, 'symptom_uri')} }}"
        )

    return f"""
        PREFIX rdf: <{_RDF_TYPE.rsplit('type', 1)[0]}>
        PREFIX rdfs: <{_RDFS_SUBCLASS.rsplit('subClassOf', 1)[0]}>
        SELECT DISTINCT ?entity ?label ?description ?predicate ?value
        WHERE {{
            {{
                SELECT DISTINCT ?entity
                WHERE {{
                    {entity_filter}
                    ?entity rdf:type/rdfs:subClassOf* {class_ref} .
                    {' '.join(filters)}
                }}
                ORDER BY ?entity
                LIMIT 500
            }}
            OPTIONAL {{ ?entity rdfs:label ?label }}
            OPTIONAL {{ ?entity rdfs:comment ?description }}
            OPTIONAL {{
                ?entity ?predicate ?value .
                FILTER(?predicate != rdf:type &&
                       ?predicate != rdfs:label &&
                       ?predicate != rdfs:comment)
            }}
        }}
        ORDER BY ?entity ?label
    """


def build_instance_exists_query(class_uri: str, entity_uri: str) -> str:
    return f"""
        PREFIX rdf: <{_RDF_TYPE.rsplit('type', 1)[0]}>
        PREFIX rdfs: <{_RDFS_SUBCLASS.rsplit('subClassOf', 1)[0]}>
        ASK {{
            {validate_uri(entity_uri, 'uri')} rdf:type/rdfs:subClassOf* {validate_uri(class_uri, 'class_uri')} .
        }}
    """


def build_uri_referenced_query(entity_uri: str) -> str:
    uri_ref = validate_uri(entity_uri, "uri")
    return f"ASK {{ {{ {uri_ref} ?predicate ?value }} UNION {{ ?subject ?predicate {uri_ref} }} }}"


def build_object_exists_query(class_uri: str, object_uri: str) -> str:
    return build_instance_exists_query(class_uri, object_uri)


def build_insert_query(class_uri: str, entity_uri: str, properties: dict[str, list[str]]) -> str:
    triples = [f"{validate_uri(entity_uri, 'uri')} <{_RDF_TYPE}> {validate_uri(class_uri, 'class_uri')} ."]
    for predicate_uri, values in properties.items():
        predicate = validate_uri(predicate_uri, "predicate")
        triples.extend(
            f"{validate_uri(entity_uri, 'uri')} {predicate} {value} ." for value in values
        )
    return f"INSERT DATA {{ {' '.join(triples)} }}"


def build_replace_query(
    class_uri: str,
    entity_uri: str,
    properties: dict[str, list[str]],
) -> str:
    subject = validate_uri(entity_uri, "uri")
    class_ref = validate_uri(class_uri, "class_uri")
    deletes = []
    optionals = []
    inserts = []
    for index, (predicate_uri, values) in enumerate(properties.items()):
        predicate = validate_uri(predicate_uri, "predicate")
        old_value = f"?old{index}"
        deletes.append(f"{subject} {predicate} {old_value} .")
        optionals.append(f"OPTIONAL {{ {subject} {predicate} {old_value} }}")
        inserts.extend(f"{subject} {predicate} {value} ." for value in values)

    return f"""
        PREFIX rdf: <{_RDF_TYPE.rsplit('type', 1)[0]}>
        PREFIX rdfs: <{_RDFS_SUBCLASS.rsplit('subClassOf', 1)[0]}>
        DELETE {{ {' '.join(deletes)} }}
        INSERT {{ {' '.join(inserts)} }}
        WHERE {{
            FILTER EXISTS {{ {subject} rdf:type/rdfs:subClassOf* {class_ref} }}
            {' '.join(optionals)}
        }}
    """


def build_delete_query(entity_uri: str, incoming_predicate_uri: str | None = None) -> str:
    subject = validate_uri(entity_uri, "uri")
    if incoming_predicate_uri is None:
        return f"DELETE WHERE {{ {subject} ?predicate ?value }}"

    predicate = validate_uri(incoming_predicate_uri, "predicate")
    return f"""
        DELETE {{ {subject} ?predicate ?value . ?source {predicate} {subject} }}
        WHERE {{
            {{ {subject} ?predicate ?value }}
            UNION
            {{ ?source {predicate} {subject} }}
        }}
    """


def _dataset_url(operation: str) -> str:
    base_url = os.getenv("FUSEKI_URL", "http://localhost:3030/medsemantic").rstrip("/")
    if not base_url:
        raise FusekiConfigurationError("FUSEKI_URL is not configured in backend/.env")
    for suffix in ("/query", "/sparql", "/update"):
        if base_url.endswith(suffix):
            base_url = base_url[: -len(suffix)]
            break
    return f"{base_url}/{operation}"


def query_fuseki(query: str) -> list[dict]:
    client = SPARQLWrapper(_dataset_url("query"))
    client.setTimeout(10)
    client.setReturnFormat(JSON)
    client.setQuery(query)
    try:
        result = client.query().convert()
    except (SPARQLWrapperException, URLError, TimeoutError) as error:
        raise FusekiQueryError("Fuseki query failed") from error
    return result["results"]["bindings"]


def ask_fuseki(query: str) -> bool:
    client = SPARQLWrapper(_dataset_url("query"))
    client.setTimeout(10)
    client.setReturnFormat(JSON)
    client.setQuery(query)
    try:
        result = client.query().convert()
    except (SPARQLWrapperException, URLError, TimeoutError) as error:
        raise FusekiQueryError("Fuseki query failed") from error
    return result["boolean"]


def update_fuseki(update: str) -> None:
    client = SPARQLWrapper(_dataset_url("update"))
    client.setTimeout(10)
    client.setMethod(POST)
    client.setQuery(update)
    try:
        client.query()
    except (SPARQLWrapperException, URLError, TimeoutError) as error:
        raise FusekiQueryError("Fuseki update failed") from error


def parse_instances(bindings: list[dict]) -> list[dict]:
    instances: dict[str, dict] = {}
    for binding in bindings:
        entity_uri = binding["entity"]["value"]
        instance = instances.setdefault(
            entity_uri,
            {"uri": entity_uri, "label": None, "description": None, "properties": []},
        )
        if binding.get("label"):
            instance["label"] = binding["label"]["value"]
        if binding.get("description"):
            instance["description"] = binding["description"]["value"]
        if binding.get("predicate") and binding.get("value"):
            value = binding["value"]
            prop = {
                "predicate": binding["predicate"]["value"],
                "value": value["value"],
                "value_type": value["type"],
            }
            if value.get("datatype"):
                prop["datatype"] = value["datatype"]
            if value.get("xml:lang"):
                prop["language"] = value["xml:lang"]
            if prop not in instance["properties"]:
                instance["properties"].append(prop)
    return list(instances.values())
