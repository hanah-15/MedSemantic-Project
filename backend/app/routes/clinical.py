import os
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr
from rdflib import Literal, URIRef

from app.sparql import (
    FusekiConfigurationError,
    FusekiQueryError,
    ask_fuseki,
    build_delete_query,
    build_instance_exists_query,
    build_instances_query,
    build_insert_query,
    build_replace_query,
    build_uri_referenced_query,
    instance_uri,
    namespace_for,
    parse_instances,
    query_fuseki,
    update_fuseki,
)

router = APIRouter(prefix="/api", tags=["Maladies et symptômes"])
PropertyValue = StrictStr | StrictInt | StrictBool

_DOMAIN_CONFIG = {
    "diseases": {
        "class_env": "DISEASE_CLASS_URI",
        "properties": {
            "codeCIM10": ("string", None),
            "estChronique": ("boolean", None),
            "presenteSymptome": ("object", "SYMPTOM_CLASS_URI"),
        },
    },
    "symptoms": {
        "class_env": "SYMPTOM_CLASS_URI",
        "properties": {
            "intensite": ("string", None),
        },
    },
}


class EntityCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Annotated[str, Field(pattern=r"^[A-Za-z][A-Za-z0-9._~-]{0,99}$")]
    properties: dict[str, list[PropertyValue]] = Field(default_factory=dict)


class EntityUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    properties: dict[str, list[PropertyValue]]


def _class_uri(domain: str) -> str:
    class_env = _DOMAIN_CONFIG[domain]["class_env"]
    class_uri = os.getenv(class_env)
    if not class_uri:
        raise HTTPException(
            status_code=503,
            detail=f"{class_env} is not configured in backend/.env",
        )
    return class_uri


def _run_fuseki(operation):
    try:
        return operation()
    except FusekiConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except FusekiQueryError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


def _entity_uri(domain: str, entity_id: str) -> str:
    try:
        return instance_uri(_class_uri(domain), entity_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


def _get_instances(
    domain: str,
    uri: str | None = None,
    search: str | None = None,
    symptom: str | None = None,
) -> list[dict]:
    class_uri = _class_uri(domain)
    symptom_uri = None
    if symptom is not None:
        if domain != "diseases":
            raise HTTPException(status_code=400, detail="Symptom filtering is only available for diseases")
        symptom_uri = _resolve_object_uri("SYMPTOM_CLASS_URI", symptom)
        if not _run_fuseki(
            lambda: ask_fuseki(build_instance_exists_query(_class_uri("symptoms"), symptom_uri))
        ):
            raise HTTPException(status_code=404, detail="Symptom not found")

    try:
        query = build_instances_query(class_uri, uri, search, symptom_uri)
        return parse_instances(_run_fuseki(lambda: query_fuseki(query)))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


def _resolve_object_uri(class_env: str, value: str) -> str:
    class_uri = os.getenv(class_env)
    if not class_uri:
        raise HTTPException(
            status_code=503,
            detail=f"{class_env} is not configured in backend/.env",
        )
    namespace = namespace_for(class_uri)
    if value.startswith(("http://", "https://")):
        if not value.startswith(namespace):
            raise HTTPException(status_code=422, detail="Related entity must belong to this ontology")
        entity_uri = value
        entity_id = value[len(namespace) :]
        try:
            instance_uri(class_uri, entity_id)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
    else:
        try:
            entity_uri = instance_uri(class_uri, value)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    exists = _run_fuseki(
        lambda: ask_fuseki(build_instance_exists_query(class_uri, entity_uri))
    )
    if not exists:
        raise HTTPException(status_code=422, detail=f"Related entity does not exist: {value}")
    return entity_uri


def _prepare_properties(domain: str, properties: dict[str, list[PropertyValue]]) -> dict[str, list[str]]:
    class_uri = _class_uri(domain)
    namespace = namespace_for(class_uri)
    schema = _DOMAIN_CONFIG[domain]["properties"]
    prepared = {}

    for property_name, values in properties.items():
        spec = schema.get(property_name)
        if spec is None:
            raise HTTPException(status_code=422, detail=f"Property is not allowed for {domain}: {property_name}")
        kind, target_class_env = spec
        predicate_uri = namespace + property_name
        converted = []

        for value in values:
            if kind == "string":
                if type(value) is not str:
                    raise HTTPException(status_code=422, detail=f"{property_name} values must be strings")
                converted.append(Literal(value, datatype=URIRef("http://www.w3.org/2001/XMLSchema#string")).n3())
            elif kind == "boolean":
                if type(value) is not bool:
                    raise HTTPException(status_code=422, detail=f"{property_name} values must be booleans")
                converted.append(Literal(value, datatype=URIRef("http://www.w3.org/2001/XMLSchema#boolean")).n3())
            else:
                if type(value) is not str:
                    raise HTTPException(status_code=422, detail=f"{property_name} values must be entity IDs or URIs")
                object_uri = _resolve_object_uri(target_class_env, value)
                converted.append(f"<{object_uri}>")
        prepared[predicate_uri] = converted
    return prepared


def _find_one(domain: str, entity_uri: str) -> dict:
    instances = _get_instances(domain, uri=entity_uri)
    if not instances:
        raise HTTPException(status_code=404, detail="Entity not found")
    return instances[0]


def _ensure_instance(domain: str, entity_uri: str) -> None:
    exists = _run_fuseki(
        lambda: ask_fuseki(build_instance_exists_query(_class_uri(domain), entity_uri))
    )
    if not exists:
        raise HTTPException(status_code=404, detail="Entity not found")


def _create(domain: str, payload: EntityCreate) -> dict:
    class_uri = _class_uri(domain)
    entity_uri = _entity_uri(domain, payload.id)
    if _run_fuseki(lambda: ask_fuseki(build_uri_referenced_query(entity_uri))):
        raise HTTPException(status_code=409, detail="An RDF resource with this URI already exists")

    properties = _prepare_properties(domain, payload.properties)
    update = build_insert_query(class_uri, entity_uri, properties)
    _run_fuseki(lambda: update_fuseki(update))
    return _find_one(domain, entity_uri)


def _replace(domain: str, entity_id: str, payload: EntityUpdate, partial: bool) -> dict:
    class_uri = _class_uri(domain)
    entity_uri = _entity_uri(domain, entity_id)
    _ensure_instance(domain, entity_uri)

    submitted = payload.properties
    if not partial:
        submitted = {
            property_name: submitted.get(property_name, [])
            for property_name in _DOMAIN_CONFIG[domain]["properties"]
        }
    if not submitted:
        raise HTTPException(status_code=422, detail="Provide at least one property to update")

    properties = _prepare_properties(domain, submitted)
    update = build_replace_query(class_uri, entity_uri, properties)
    _run_fuseki(lambda: update_fuseki(update))
    return _find_one(domain, entity_uri)


def _delete(domain: str, entity_id: str) -> None:
    entity_uri = _entity_uri(domain, entity_id)
    _ensure_instance(domain, entity_uri)
    incoming_predicate = None
    if domain == "symptoms":
        incoming_predicate = namespace_for(_class_uri("diseases")) + "presenteSymptome"
    _run_fuseki(
        lambda: update_fuseki(build_delete_query(entity_uri, incoming_predicate))
    )


@router.get("/diseases")
def list_diseases(
    uri: str | None = Query(default=None, description="Optional ontology URI to look up"),
    q: str | None = Query(default=None, min_length=1, max_length=100, description="Search URI, label, comment, or literal properties"),
    symptom: str | None = Query(default=None, description="Filter by symptom ID or ontology URI"),
) -> list[dict]:
    """List and search disease individuals; optionally filter by a linked symptom."""
    return _get_instances("diseases", uri, q, symptom)


@router.get("/diseases/{entity_id}")
def get_disease(entity_id: str) -> dict:
    return _find_one("diseases", _entity_uri("diseases", entity_id))


@router.post("/diseases", status_code=status.HTTP_201_CREATED)
def create_disease(payload: EntityCreate) -> dict:
    return _create("diseases", payload)


@router.put("/diseases/{entity_id}")
def replace_disease(entity_id: str, payload: EntityUpdate) -> dict:
    return _replace("diseases", entity_id, payload, partial=False)


@router.patch("/diseases/{entity_id}")
def update_disease(entity_id: str, payload: EntityUpdate) -> dict:
    return _replace("diseases", entity_id, payload, partial=True)


@router.delete("/diseases/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_disease(entity_id: str) -> Response:
    _delete("diseases", entity_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/symptoms")
def list_symptoms(
    uri: str | None = Query(default=None, description="Optional ontology URI to look up"),
    q: str | None = Query(default=None, min_length=1, max_length=100, description="Search URI, label, comment, or literal properties"),
) -> list[dict]:
    """List and search symptom individuals."""
    return _get_instances("symptoms", uri, q)


@router.get("/symptoms/{entity_id}")
def get_symptom(entity_id: str) -> dict:
    return _find_one("symptoms", _entity_uri("symptoms", entity_id))


@router.post("/symptoms", status_code=status.HTTP_201_CREATED)
def create_symptom(payload: EntityCreate) -> dict:
    return _create("symptoms", payload)


@router.put("/symptoms/{entity_id}")
def replace_symptom(entity_id: str, payload: EntityUpdate) -> dict:
    return _replace("symptoms", entity_id, payload, partial=False)


@router.patch("/symptoms/{entity_id}")
def update_symptom(entity_id: str, payload: EntityUpdate) -> dict:
    return _replace("symptoms", entity_id, payload, partial=True)


@router.delete("/symptoms/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_symptom(entity_id: str) -> Response:
    _delete("symptoms", entity_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
