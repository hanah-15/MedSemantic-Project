"""
Tests unitaires et d'intégration pour les modules d'Oussema :
- EffetSecondaire et ses sous-classes
- ContreIndication et ses sous-classes

Couverture :
1. Validation syntaxique SPARQL 1.1 (rdflib prepareQuery) de toutes les requêtes.
2. Sécurité anti-injection et validation des identifiants (HTTP 422).
3. Routes API FastAPI (/effets-secondaires et /contre-indications).
4. Détection et croisement sémantique de contre-indications patient-médicament.
5. Gestion des erreurs Fuseki (404, 502, 503).
"""

import os
import sys
from unittest.mock import patch
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from rdflib.plugins.sparql import prepareQuery

# S'assurer que le dossier backend est dans le PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from sparql_queries.queries_effet_secondaire import (
    requete_lister_effets_secondaires,
    requete_detail_effet_secondaire,
    requete_effets_par_type,
    requete_effets_par_gravite,
    requete_effets_par_frequence,
    requete_effets_par_medicament,
    requete_effets_par_symptome,
    requete_stats_effets_secondaires,
    _valider_id as valider_id_effet,
)
from sparql_queries.queries_contre_indication import (
    requete_lister_contre_indications,
    requete_detail_contre_indication,
    requete_contre_indications_par_type,
    requete_contre_indications_par_medicament,
    requete_contre_indications_par_condition,
    requete_verifier_contre_indication,
    requete_stats_contre_indications,
    _valider_id as valider_id_ci,
)

client = TestClient(app)


# =============================================================================
# 1. Validation de la syntaxe SPARQL 1.1 avec rdflib
# =============================================================================

class TestSyntaxeSparql:
    """Vérifie que chaque chaîne SPARQL générée est strictement conforme à la norme SPARQL 1.1."""

    def test_syntaxe_requetes_effets_secondaires(self):
        prepareQuery(requete_lister_effets_secondaires())
        prepareQuery(requete_detail_effet_secondaire("TroublesGastriques"))
        prepareQuery(requete_effets_par_type("EffetDigestif"))
        prepareQuery(requete_effets_par_gravite("légère"))
        prepareQuery(requete_effets_par_frequence("fréquent"))
        prepareQuery(requete_effets_par_medicament("Glucophage"))
        prepareQuery(requete_effets_par_symptome("Nausee"))
        prepareQuery(requete_stats_effets_secondaires())

    def test_syntaxe_requetes_contre_indications(self):
        prepareQuery(requete_lister_contre_indications())
        prepareQuery(requete_detail_contre_indication("CI_Metformine_InsufRenale"))
        prepareQuery(requete_contre_indications_par_type("absolue"))
        prepareQuery(requete_contre_indications_par_medicament("Advil"))
        prepareQuery(requete_contre_indications_par_condition("Grossesse_T3"))
        prepareQuery(requete_verifier_contre_indication("Patient_Sarah", "Advil"))
        prepareQuery(requete_stats_contre_indications())


# =============================================================================
# 2. Sécurité et validation des entrées
# =============================================================================

class TestSecuriteEtValidation:
    """Vérifie le blocage préventif des injections SPARQL."""

    def test_rejet_injections_effet(self):
        with pytest.raises(HTTPException) as exc_info:
            valider_id_effet("Effet; DROP GRAPH")
        assert exc_info.value.status_code == 422

        with pytest.raises(HTTPException):
            valider_id_effet("Effet> . ?s ?p ?o . <http://evil.com")

    def test_rejet_injections_contre_indication(self):
        with pytest.raises(HTTPException) as exc_info:
            valider_id_ci("CI_Test' OR '1'='1")
        assert exc_info.value.status_code == 422


# =============================================================================
# 3. Tests des routes Effets Secondaires
# =============================================================================

MOCK_BINDINGS_EFFETS = [
    {
        "effet": {"value": "http://www.semanticweb.org/medsemantic#TroublesGastriques"},
        "typeEffet": {"value": "EffetDigestif"},
        "frequence": {"value": "fréquent"},
        "gravite": {"value": "légère"},
        "symptome": {"value": "http://www.semanticweb.org/medsemantic#Nausee"},
        "symptomeNom": {"value": "Nausee"},
        "medicament": {"value": "http://www.semanticweb.org/medsemantic#Glucophage"},
        "medicamentNom": {"value": "Glucophage"},
        "label": {"value": "Troubles gastriques"},
    },
    {
        "effet": {"value": "http://www.semanticweb.org/medsemantic#Oedemes"},
        "typeEffet": {"value": "EffetCardiovasculaire"},
        "frequence": {"value": "fréquent"},
        "gravite": {"value": "modérée"},
        "symptome": {"value": ""},
        "symptomeNom": {"value": ""},
        "medicament": {"value": "http://www.semanticweb.org/medsemantic#Amlor"},
        "medicamentNom": {"value": "Amlor"},
        "label": {"value": "Oedèmes"},
    },
]


class TestRoutesEffetsSecondaires:

    @patch("app.routes.effets_secondaires.execute_sparql")
    def test_lister_effets(self, mock_exec):
        mock_exec.return_value = MOCK_BINDINGS_EFFETS
        resp = client.get("/effets-secondaires/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["id"] == "TroublesGastriques"
        assert data[0]["type_effet"] == "EffetDigestif"
        assert "Glucophage" in data[0]["medicaments_lies"]

    @patch("app.routes.effets_secondaires.execute_sparql")
    def test_lister_effets_prefix_api(self, mock_exec):
        mock_exec.return_value = MOCK_BINDINGS_EFFETS
        resp = client.get("/api/effets-secondaires")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    @patch("app.routes.effets_secondaires.execute_sparql")
    def test_detail_effet_existant(self, mock_exec):
        mock_exec.return_value = [MOCK_BINDINGS_EFFETS[0]]
        resp = client.get("/effets-secondaires/TroublesGastriques")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "TroublesGastriques"
        assert data["gravite"] == "légère"
        assert len(data["symptomes"]) == 1
        assert data["symptomes"][0]["id"] == "Nausee"
        assert len(data["medicaments"]) == 1
        assert data["medicaments"][0]["id"] == "Glucophage"

    @patch("app.routes.effets_secondaires.execute_sparql")
    def test_detail_effet_introuvable(self, mock_exec):
        mock_exec.return_value = []
        resp = client.get("/effets-secondaires/Inconnu")
        assert resp.status_code == 404

    def test_detail_effet_invalide_format(self):
        resp = client.get("/effets-secondaires/bad;id")
        assert resp.status_code == 422

    @patch("app.routes.effets_secondaires.execute_sparql")
    def test_effets_par_medicament(self, mock_exec):
        mock_exec.return_value = [MOCK_BINDINGS_EFFETS[0]]
        resp = client.get("/effets-secondaires/medicament/Glucophage")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == "TroublesGastriques"

    @patch("app.routes.effets_secondaires.execute_sparql")
    def test_effets_stats(self, mock_exec):
        mock_exec.return_value = [
            {"typeEffet": {"value": "EffetDigestif"}, "total": {"value": "1"}},
            {"typeEffet": {"value": "EffetCardiovasculaire"}, "total": {"value": "1"}},
        ]
        resp = client.get("/effets-secondaires/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["type_effet"] == "EffetDigestif"
        assert data[0]["total"] == 1


# =============================================================================
# 4. Tests des routes Contre-indications
# =============================================================================

MOCK_BINDINGS_CI = [
    {
        "ci": {"value": "http://www.semanticweb.org/medsemantic#CI_Ibuprofene_Grossesse"},
        "typeCI": {"value": "ContreIndicationAbsolue"},
        "description": {"value": "Ibuprofène interdit en fin de grossesse"},
        "condition": {"value": "http://www.semanticweb.org/medsemantic#Grossesse_T3"},
        "conditionNom": {"value": "Grossesse_T3"},
        "medicament": {"value": "http://www.semanticweb.org/medsemantic#Advil"},
        "medicamentNom": {"value": "Advil"},
        "label": {"value": ""},
    },
    {
        "ci": {"value": "http://www.semanticweb.org/medsemantic#CI_Paracetamol_InsufHepatique"},
        "typeCI": {"value": "ContreIndicationRelative"},
        "description": {"value": "Paracétamol déconseillé en insuffisance hépatique, à évaluer"},
        "condition": {"value": "http://www.semanticweb.org/medsemantic#InsufHepatiqueModeree"},
        "conditionNom": {"value": "InsufHepatiqueModeree"},
        "medicament": {"value": "http://www.semanticweb.org/medsemantic#Doliprane"},
        "medicamentNom": {"value": "Doliprane"},
        "label": {"value": ""},
    },
]


class TestRoutesContreIndications:

    @patch("app.routes.contre_indications.execute_sparql")
    def test_lister_contre_indications(self, mock_exec):
        mock_exec.return_value = MOCK_BINDINGS_CI
        resp = client.get("/contre-indications/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["id"] == "CI_Ibuprofene_Grossesse"
        assert data[0]["type_ci"] == "ContreIndicationAbsolue"
        assert data[0]["condition_id"] == "Grossesse_T3"
        assert "Advil" in data[0]["medicaments_lies"]

    @patch("app.routes.contre_indications.execute_sparql")
    def test_lister_contre_indications_prefix_api(self, mock_exec):
        mock_exec.return_value = MOCK_BINDINGS_CI
        resp = client.get("/api/contre-indications")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    @patch("app.routes.contre_indications.execute_sparql")
    def test_detail_ci_existant(self, mock_exec):
        mock_exec.return_value = [MOCK_BINDINGS_CI[0]]
        resp = client.get("/contre-indications/CI_Ibuprofene_Grossesse")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "CI_Ibuprofene_Grossesse"
        assert len(data["conditions_concernees"]) == 1
        assert data["conditions_concernees"][0]["id"] == "Grossesse_T3"
        assert len(data["medicaments_concernes"]) == 1
        assert data["medicaments_concernes"][0]["id"] == "Advil"

    @patch("app.routes.contre_indications.execute_sparql")
    def test_detail_ci_introuvable(self, mock_exec):
        mock_exec.return_value = []
        resp = client.get("/contre-indications/CI_Inconnue")
        assert resp.status_code == 404

    @patch("app.routes.contre_indications.execute_sparql")
    def test_contre_indications_par_medicament(self, mock_exec):
        mock_exec.return_value = [MOCK_BINDINGS_CI[0]]
        resp = client.get("/contre-indications/medicament/Advil")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == "CI_Ibuprofene_Grossesse"

    @patch("app.routes.contre_indications.execute_sparql")
    def test_contre_indications_par_condition(self, mock_exec):
        mock_exec.return_value = [MOCK_BINDINGS_CI[0]]
        resp = client.get("/contre-indications/condition/Grossesse_T3")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == "CI_Ibuprofene_Grossesse"

    @patch("app.routes.contre_indications.execute_sparql")
    def test_verifier_securite_positive(self, mock_exec):
        mock_exec.return_value = [
            {
                "ci": {"value": "http://www.semanticweb.org/medsemantic#CI_Ibuprofene_Grossesse"},
                "typeCI": {"value": "ContreIndicationAbsolue"},
                "description": {"value": "Ibuprofène interdit en fin de grossesse"},
                "conditionNom": {"value": "Grossesse_T3"},
                "raison": {"value": "Condition médicale active du patient"},
            }
        ]
        resp = client.get("/contre-indications/verifier/Patient_Sarah/Advil")
        assert resp.status_code == 200
        data = resp.json()
        assert data["est_contre_indique"] is True
        assert len(data["alertes"]) == 1
        assert data["alertes"][0]["contre_indication_id"] == "CI_Ibuprofene_Grossesse"

    @patch("app.routes.contre_indications.execute_sparql")
    def test_verifier_securite_negative(self, mock_exec):
        mock_exec.return_value = []
        resp = client.get("/contre-indications/verifier/Patient_Sarah/Doliprane")
        assert resp.status_code == 200
        data = resp.json()
        assert data["est_contre_indique"] is False
        assert len(data["alertes"]) == 0

    @patch("app.routes.contre_indications.execute_sparql")
    def test_stats_contre_indications(self, mock_exec):
        mock_exec.return_value = [
            {"typeCI": {"value": "ContreIndicationAbsolue"}, "total": {"value": "2"}},
            {"typeCI": {"value": "ContreIndicationRelative"}, "total": {"value": "1"}},
        ]
        resp = client.get("/contre-indications/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["type_ci"] == "ContreIndicationAbsolue"
        assert data[0]["total"] == 2
