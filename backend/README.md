# MedSemantic API: diseases and symptoms

The API reads and updates RDF individuals in Apache Jena Fuseki. It uses the
ontology's `Maladie`, `Symptome`, and property IRIs from `.env` and the
`http://www.semanticweb.org/medsemantic#` vocabulary. It does not expose
arbitrary SPARQL updates.

## Configure

Keep your existing `backend/.env`. For a new setup, copy `.env.example` to `.env`. Set:

- `FUSEKI_URL` to the Fuseki dataset URL, for example
  `http://localhost:3030/medsemantic`.
- Optional `DISEASE_CLASS_URI` override (defaults to `http://www.semanticweb.org/medsemantic#Maladie`).
- Optional `SYMPTOM_CLASS_URI` override (defaults to `http://www.semanticweb.org/medsemantic#Symptome`).

Start Fuseki with the ontology dataset loaded, then run `python main.py`. Open
`http://127.0.0.1:8000/docs` to try the endpoints.

## Read, search, and filter

- `GET /api/diseases` and `GET /api/symptoms` list instances (including
  instances typed as subclasses).
- `GET /api/diseases/{id}` and `GET /api/symptoms/{id}` fetch one individual.
- `?uri=<absolute-individual-IRI>` is also supported on collection routes.
- `?q=<text>` searches an individual's URI, label, comment, or literal values.
- `GET /api/diseases?symptom=Fievre` filters diseases by their
  `presenteSymptome` relation. The value can be an individual ID or a full URI.

Results contain the individual URI, optional `rdfs:label` and `rdfs:comment`,
and its outgoing non-type properties as RDF predicate/value pairs. The API
returns at most 500 individuals per collection request.

## CRUD

Create a disease:

```json
{
  "id": "ExempleMaladie",
  "properties": {
    "codeCIM10": ["X00"],
    "estChronique": [false],
    "presenteSymptome": ["Fievre", "Toux"]
  }
}
```

Create a symptom:

```json
{
  "id": "ExempleSymptome",
  "properties": {
    "intensite": ["moderee"]
  }
}
```

Each `properties` value is an array so multivalued RDF properties are supported.
Only these ontology properties are accepted:

- Diseases: `codeCIM10` (string), `estChronique` (boolean),
  `presenteSymptome` (IDs/URIs of existing symptoms).
- Symptoms: `intensite` (string).

Available operations for both resources:

- `POST /api/diseases` or `POST /api/symptoms` creates an individual.
- `PUT /api/diseases/{id}` or `PUT /api/symptoms/{id}` replaces all properties
  managed by this API; omitted properties are cleared.
- `PATCH /api/diseases/{id}` or `PATCH /api/symptoms/{id}` replaces only the
  properties included in the request; other properties are preserved.
- `DELETE /api/diseases/{id}` or `DELETE /api/symptoms/{id}` removes the
  individual and its outgoing triples. Deleting a symptom also removes
  disease-to-symptom `presenteSymptome` links. References from other modules
  are not modified.

IDs are local names in the ontology namespace. Property names, value types,
related-individual existence, and target class are validated before updates.
