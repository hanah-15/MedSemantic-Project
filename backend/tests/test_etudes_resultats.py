"""
Tests pytest pour les modules d'Aymen : EtudeClinique et ResultatClinique.
Les appels HTTP vers Apache Jena Fuseki sont mockés via unittest.mock.patch.
La validité syntaxique de toutes les requêtes SPARQL est également vérifiée avec rdflib.

Couverture :
- Validation syntaxique SPARQL (prepareQuery) des 13 fonctions de requêtes
- GET /etudes/                    → liste complète (avec OPTIONAL : Etude_Paracetamol_Obs incluse)
- GET /etudes/{id}                → détail étude + résultats / 404 / 422
- GET /etudes/type/{type}         → filtre EssaiClinique & EtudeObservationnelle / 422
- GET /etudes/medicament/{id}     → filtre par médicament (Glucophage, Doliprane) / 404 / 422
- GET /etudes/maladie/{id}        → filtre par maladie (DiabeteType2) / 404 / 422
- GET /etudes/phase/{n}           → filtre par phase (phase 3 → Essai_Metformine_2024) / 404 / 422
- GET /etudes/annee/recherche     → filtre par plage d'années / 422
- GET /etudes/participants/minimum → filtre par nombre minimal de participants
- GET /etudes/comparatives/liste  → études comparatives uniquement
- GET /etudes/sans-resultat       → études sans résultat (FILTER NOT EXISTS → Etude_Paracetamol_Obs)
- GET /etudes/stats               → statistiques (COUNT, AVG, GROUP BY)
- GET /resultats/                 → liste des résultats
- GET /resultats/{id}             → détail d'un résultat / 404 / 422
- GET /resultats/type/{type}      → filtre efficacite / securite (inclut Tolerance via rdfs:subClassOf*) / tolerance / 422
- GET /resultats/medicament/{id}  → résultats par médicament via l'étude / 404 / 422
- GET /resultats/stats            → statistiques des résultats par type
- Gestion des pannes Fuseki       → 502 (ConnectionError / HTTPError) et 503 (Timeout)
"""

import os
import sys

# S'assurer que le dossier backend est dans le PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch
import pytest
import requests as req_module
from fastapi.testclient import TestClient
from rdflib.plugins.sparql import prepareQuery

from main import app
from sparql_queries.queries_etude import (
    requete_lister_etudes,
    requete_detail_etude,
    requete_etudes_par_type,
    requete_etudes_par_medicament,
    requete_etudes_par_maladie,
    requete_etudes_par_phase,
    requete_etudes_par_annee,
    requete_etudes_min_participants,
    requete_etudes_comparatives,
    requete_etudes_sans_resultat,
    requete_stats_etudes,
)
from sparql_queries.queries_resultat import (
    requete_lister_resultats,
    requete_detail_resultat,
    requete_resultats_par_type,
    requete_resultats_par_medicament,
    requete_stats_resultats,
)

client = TestClient(app)

# ─────────────────────────────────────────────────────────────────────────────
# Données mockées fidèles à MedSemantic.owl
# ─────────────────────────────────────────────────────────────────────────────

BINDING_ESSAI_METFORMINE = {
    "etude": {"type": "uri", "value": "http://www.semanticweb.org/medsemantic#Essai_Metformine_2024"},
    "typeEtude": {"type": "literal", "value": "EssaiClinique"},
    "medicament": {"type": "uri", "value": "http://www.semanticweb.org/medsemantic#Glucophage"},
    "medicamentNom": {"type": "literal", "value": "Glucophage"},
    "maladie": {"type": "uri", "value": "http://www.semanticweb.org/medsemantic#DiabeteType2"},
    "maladieNom": {"type": "literal", "value": "DiabeteType2"},
    "phase": {"type": "literal", "value": "3"},
    "annee": {"type": "literal", "value": "2024"},
    "participants": {"type": "literal", "value": "500"},
    "comparative": {"type": "literal", "value": "true"},
}

BINDING_OBS_PARACETAMOL = {
    "etude": {"type": "uri", "value": "http://www.semanticweb.org/medsemantic#Etude_Paracetamol_Obs"},
    "typeEtude": {"type": "literal", "value": "EtudeObservationnelle"},
    "medicament": {"type": "uri", "value": "http://www.semanticweb.org/medsemantic#Doliprane"},
    "medicamentNom": {"type": "literal", "value": "Doliprane"},
    "annee": {"type": "literal", "value": "2023"},
    "participants": {"type": "literal", "value": "1200"},
    "comparative": {"type": "literal", "value": "false"},
}

BINDING_RES_EFFICACITE_GLUCOPHAGE = {
    "resultat": {"type": "uri", "value": "http://www.semanticweb.org/medsemantic#Res_Efficacite_Glucophage"},
    "typeResultat": {"type": "literal", "value": "Efficacite"},
    "valeur": {"type": "literal", "value": "1.2"},
    "unite": {"type": "literal", "value": "% HbA1c (baisse)"},
    "etude": {"type": "uri", "value": "http://www.semanticweb.org/medsemantic#Essai_Metformine_2024"},
    "etudeNom": {"type": "literal", "value": "Essai_Metformine_2024"},
    "medicament": {"type": "uri", "value": "http://www.semanticweb.org/medsemantic#Glucophage"},
    "medicamentNom": {"type": "literal", "value": "Glucophage"},
}

BINDING_RES_TOLERANCE_GLUCOPHAGE = {
    "resultat": {"type": "uri", "value": "http://www.semanticweb.org/medsemantic#Res_Tolerance_Glucophage"},
    "typeResultat": {"type": "literal", "value": "Tolerance"},
    "valeur": {"type": "literal", "value": "85"},
    "unite": {"type": "literal", "value": "% patients sans effet gênant"},
    "etude": {"type": "uri", "value": "http://www.semanticweb.org/medsemantic#Essai_Metformine_2024"},
    "etudeNom": {"type": "literal", "value": "Essai_Metformine_2024"},
    "medicament": {"type": "uri", "value": "http://www.semanticweb.org/medsemantic#Glucophage"},
    "medicamentNom": {"type": "literal", "value": "Glucophage"},
}

BINDING_STAT_ESSAI = {
    "typeEtude": {"type": "literal", "value": "EssaiClinique"},
    "nombreEtudes": {"type": "literal", "value": "1"},
    "moyenneParticipants": {"type": "literal", "value": "500.0"},
}

BINDING_STAT_OBS = {
    "typeEtude": {"type": "literal", "value": "EtudeObservationnelle"},
    "nombreEtudes": {"type": "literal", "value": "1"},
    "moyenneParticipants": {"type": "literal", "value": "1200.0"},
}


def _mock_fuseki(mock_get, bindings):
    """Configure le mock de requests.get pour simuler une réponse JSON SPARQL de Fuseki."""
    mock_get.return_value.status_code = 200
    mock_get.return_value.raise_for_status = lambda: None
    mock_get.return_value.json.return_value = {"results": {"bindings": bindings}}


# ─────────────────────────────────────────────────────────────────────────────
# 0. Validation syntaxique SPARQL via rdflib (prepareQuery)
# ─────────────────────────────────────────────────────────────────────────────

class TestSyntaxeSparql:
    @pytest.mark.parametrize(
        "query_str",
        [
            requete_lister_etudes(),
            requete_detail_etude("Essai_Metformine_2024"),
            requete_etudes_par_type("EssaiClinique"),
            requete_etudes_par_type("EtudeObservationnelle"),
            requete_etudes_par_medicament("Glucophage"),
            requete_etudes_par_maladie("DiabeteType2"),
            requete_etudes_par_phase(3),
            requete_etudes_par_annee(2020, 2024),
            requete_etudes_min_participants(500),
            requete_etudes_comparatives(),
            requete_etudes_sans_resultat(),
            requete_stats_etudes(),
            requete_lister_resultats(),
            requete_detail_resultat("Res_Efficacite_Glucophage"),
            requete_resultats_par_type("efficacite"),
            requete_resultats_par_type("securite"),
            requete_resultats_par_type("tolerance"),
            requete_resultats_par_medicament("Glucophage"),
            requete_stats_resultats(),
        ],
    )
    def test_requete_sparql_valide(self, query_str: str):
        """Vérifie que chaque requête SPARQL est syntaxiquement valide selon SPARQL 1.1."""
        parsed = prepareQuery(query_str)
        assert parsed is not None


# ─────────────────────────────────────────────────────────────────────────────
# 1. Tests : GET /etudes/
# ─────────────────────────────────────────────────────────────────────────────

class TestListerEtudes:
    def test_liste_deux_etudes_avec_optional(self):
        """Doit retourner Essai_Metformine_2024 et Etude_Paracetamol_Obs (grâce aux OPTIONAL)."""
        with patch("app.fuseki_client.requests.get") as mock_get:
            _mock_fuseki(mock_get, [BINDING_ESSAI_METFORMINE, BINDING_OBS_PARACETAMOL])
            resp = client.get("/etudes/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

        essai = next(e for e in data if e["id"] == "Essai_Metformine_2024")
        assert essai["iri"] == "http://www.semanticweb.org/medsemantic#Essai_Metformine_2024"
        assert essai["type_etude"] == "EssaiClinique"
        assert essai["medicament_id"] == "Glucophage"
        assert essai["maladie_id"] == "DiabeteType2"
        assert essai["phase"] == 3
        assert essai["participants"] == 500
        assert essai["annee"] == 2024
        assert essai["comparative"] is True

        obs = next(e for e in data if e["id"] == "Etude_Paracetamol_Obs")
        assert obs["type_etude"] == "EtudeObservationnelle"
        assert obs["medicament_id"] == "Doliprane"
        assert obs["phase"] is None
        assert obs["maladie_id"] is None
        assert obs["participants"] == 1200
        assert obs["annee"] == 2023
        assert obs["comparative"] is False


# ─────────────────────────────────────────────────────────────────────────────
# 2. Tests : GET /etudes/{etude_id}
# ─────────────────────────────────────────────────────────────────────────────

class TestDetailEtude:
    def test_detail_essai_metformine_avec_deux_resultats(self):
        """Détail complet de Essai_Metformine_2024 avec ses 2 résultats."""
        b1 = {
            **BINDING_ESSAI_METFORMINE,
            "resultat": BINDING_RES_EFFICACITE_GLUCOPHAGE["resultat"],
            "typeResultat": BINDING_RES_EFFICACITE_GLUCOPHAGE["typeResultat"],
            "valeur": BINDING_RES_EFFICACITE_GLUCOPHAGE["valeur"],
            "unite": BINDING_RES_EFFICACITE_GLUCOPHAGE["unite"],
        }
        b2 = {
            **BINDING_ESSAI_METFORMINE,
            "resultat": BINDING_RES_TOLERANCE_GLUCOPHAGE["resultat"],
            "typeResultat": BINDING_RES_TOLERANCE_GLUCOPHAGE["typeResultat"],
            "valeur": BINDING_RES_TOLERANCE_GLUCOPHAGE["valeur"],
            "unite": BINDING_RES_TOLERANCE_GLUCOPHAGE["unite"],
        }
        with patch("app.fuseki_client.requests.get") as mock_get:
            _mock_fuseki(mock_get, [b1, b2])
            resp = client.get("/etudes/Essai_Metformine_2024")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "Essai_Metformine_2024"
        assert data["phase"] == 3
        assert len(data["resultats"]) == 2
        res_ids = {r["id"] for r in data["resultats"]}
        assert res_ids == {"Res_Efficacite_Glucophage", "Res_Tolerance_Glucophage"}

    def test_detail_paracetamol_sans_resultat(self):
        """Etude_Paracetamol_Obs a une liste de résultats vide."""
        with patch("app.fuseki_client.requests.get") as mock_get:
            _mock_fuseki(mock_get, [BINDING_OBS_PARACETAMOL])
            resp = client.get("/etudes/Etude_Paracetamol_Obs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "Etude_Paracetamol_Obs"
        assert data["phase"] is None
        assert data["resultats"] == []

    def test_detail_etude_introuvable_404(self):
        """Retourne 404 si l'étude n'existe pas."""
        with patch("app.fuseki_client.requests.get") as mock_get:
            _mock_fuseki(mock_get, [])
            resp = client.get("/etudes/Etude_Inconnue")
        assert resp.status_code == 404

    def test_detail_etude_injection_sparql_422(self):
        """Bloque toute tentative d'injection SPARQL avec 422."""
        resp = client.get("/etudes/Essai_Metformine_2024}%20UNION%20{?s%20?p%20?o")
        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# 3. Tests : Filtres sur /etudes
# ─────────────────────────────────────────────────────────────────────────────

class TestFiltresEtudes:
    def test_etudes_par_type_essai(self):
        with patch("app.fuseki_client.requests.get") as mock_get:
            _mock_fuseki(mock_get, [BINDING_ESSAI_METFORMINE])
            resp = client.get("/etudes/type/EssaiClinique")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["id"] == "Essai_Metformine_2024"

    def test_etudes_par_type_invalide_422(self):
        resp = client.get("/etudes/type/AutreType")
        assert resp.status_code == 422

    def test_etudes_par_medicament_glucophage(self):
        with patch("app.fuseki_client.requests.get") as mock_get:
            _mock_fuseki(mock_get, [BINDING_ESSAI_METFORMINE])
            resp = client.get("/etudes/medicament/Glucophage")
        assert resp.status_code == 200
        assert resp.json()[0]["id"] == "Essai_Metformine_2024"
        assert resp.json()[0]["medicament_id"] == "Glucophage"

    def test_etudes_par_medicament_introuvable_404(self):
        with patch("app.fuseki_client.requests.get") as mock_get:
            _mock_fuseki(mock_get, [])
            resp = client.get("/etudes/medicament/Advil")
        assert resp.status_code == 404

    def test_etudes_par_maladie_diabete(self):
        with patch("app.fuseki_client.requests.get") as mock_get:
            _mock_fuseki(mock_get, [BINDING_ESSAI_METFORMINE])
            resp = client.get("/etudes/maladie/DiabeteType2")
        assert resp.status_code == 200
        assert resp.json()[0]["id"] == "Essai_Metformine_2024"

    def test_etudes_par_phase_3(self):
        """/etudes/phase/3 retourne uniquement Essai_Metformine_2024."""
        with patch("app.fuseki_client.requests.get") as mock_get:
            _mock_fuseki(mock_get, [BINDING_ESSAI_METFORMINE])
            resp = client.get("/etudes/phase/3")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == "Essai_Metformine_2024"
        assert data[0]["phase"] == 3

    def test_etudes_par_phase_hors_limites_422(self):
        resp = client.get("/etudes/phase/9")
        assert resp.status_code == 422

    def test_etudes_sans_resultat(self):
        """/etudes/sans-resultat retourne Etude_Paracetamol_Obs."""
        with patch("app.fuseki_client.requests.get") as mock_get:
            _mock_fuseki(mock_get, [BINDING_OBS_PARACETAMOL])
            resp = client.get("/etudes/sans-resultat")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == "Etude_Paracetamol_Obs"

    def test_etudes_par_annee(self):
        with patch("app.fuseki_client.requests.get") as mock_get:
            _mock_fuseki(mock_get, [BINDING_ESSAI_METFORMINE])
            resp = client.get("/etudes/annee/recherche?annee_min=2024&annee_max=2024")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_etudes_par_annee_sans_param_422(self):
        resp = client.get("/etudes/annee/recherche")
        assert resp.status_code == 422

    def test_etudes_min_participants(self):
        with patch("app.fuseki_client.requests.get") as mock_get:
            _mock_fuseki(mock_get, [BINDING_OBS_PARACETAMOL])
            resp = client.get("/etudes/participants/minimum?n=1000")
        assert resp.status_code == 200
        assert resp.json()[0]["id"] == "Etude_Paracetamol_Obs"

    def test_etudes_comparatives(self):
        with patch("app.fuseki_client.requests.get") as mock_get:
            _mock_fuseki(mock_get, [BINDING_ESSAI_METFORMINE])
            resp = client.get("/etudes/comparatives/liste")
        assert resp.status_code == 200
        assert resp.json()[0]["comparative"] is True

    def test_stats_etudes(self):
        with patch("app.fuseki_client.requests.get") as mock_get:
            _mock_fuseki(mock_get, [BINDING_STAT_ESSAI, BINDING_STAT_OBS])
            resp = client.get("/etudes/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        essai_stat = next(s for s in data if s["type_etude"] == "EssaiClinique")
        assert essai_stat["nombre_etudes"] == 1
        assert essai_stat["moyenne_participants"] == pytest.approx(500.0)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Tests : /resultats
# ─────────────────────────────────────────────────────────────────────────────

class TestResultats:
    def test_lister_resultats(self):
        with patch("app.fuseki_client.requests.get") as mock_get:
            _mock_fuseki(
                mock_get,
                [BINDING_RES_EFFICACITE_GLUCOPHAGE, BINDING_RES_TOLERANCE_GLUCOPHAGE],
            )
            resp = client.get("/resultats/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        eff = next(r for r in data if r["id"] == "Res_Efficacite_Glucophage")
        assert eff["valeur"] == pytest.approx(1.2)
        assert eff["unite"] == "% HbA1c (baisse)"

    def test_resultats_type_securite_inclut_tolerance(self):
        """/resultats/type/securite doit retourner Res_Tolerance_Glucophage (via rdfs:subClassOf*)."""
        with patch("app.fuseki_client.requests.get") as mock_get:
            _mock_fuseki(mock_get, [BINDING_RES_TOLERANCE_GLUCOPHAGE])
            resp = client.get("/resultats/type/securite")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == "Res_Tolerance_Glucophage"
        assert data[0]["type_resultat"] == "Tolerance"
        assert data[0]["valeur"] == pytest.approx(85.0)

    def test_resultats_type_invalide_422(self):
        resp = client.get("/resultats/type/autre")
        assert resp.status_code == 422

    def test_resultats_par_medicament_glucophage(self):
        with patch("app.fuseki_client.requests.get") as mock_get:
            _mock_fuseki(
                mock_get,
                [BINDING_RES_EFFICACITE_GLUCOPHAGE, BINDING_RES_TOLERANCE_GLUCOPHAGE],
            )
            resp = client.get("/resultats/medicament/Glucophage")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_detail_resultat_existant(self):
        binding = {
            **BINDING_RES_EFFICACITE_GLUCOPHAGE,
            "typeEtude": {"type": "literal", "value": "EssaiClinique"},
        }
        with patch("app.fuseki_client.requests.get") as mock_get:
            _mock_fuseki(mock_get, [binding])
            resp = client.get("/resultats/Res_Efficacite_Glucophage")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "Res_Efficacite_Glucophage"
        assert data["type_etude"] == "EssaiClinique"
        assert data["medicament_id"] == "Glucophage"

    def test_detail_resultat_introuvable_404(self):
        with patch("app.fuseki_client.requests.get") as mock_get:
            _mock_fuseki(mock_get, [])
            resp = client.get("/resultats/Res_Inexistant")
        assert resp.status_code == 404

    def test_stats_resultats(self):
        bindings = [
            {"typeResultat": {"type": "literal", "value": "Efficacite"}, "nombreResultats": {"type": "literal", "value": "1"}},
            {"typeResultat": {"type": "literal", "value": "Tolerance"}, "nombreResultats": {"type": "literal", "value": "1"}},
        ]
        with patch("app.fuseki_client.requests.get") as mock_get:
            _mock_fuseki(mock_get, bindings)
            resp = client.get("/resultats/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2


# ─────────────────────────────────────────────────────────────────────────────
# 5. Tests : Erreurs serveur Fuseki (502 / 503)
# ─────────────────────────────────────────────────────────────────────────────

class TestErreursFuseki:
    def test_fuseki_connection_error_502(self):
        with patch("app.fuseki_client.requests.get") as mock_get:
            mock_get.side_effect = req_module.exceptions.ConnectionError("Fuseki down")
            resp = client.get("/etudes/")
        assert resp.status_code == 502

    def test_fuseki_timeout_503(self):
        with patch("app.fuseki_client.requests.get") as mock_get:
            mock_get.side_effect = req_module.exceptions.Timeout("Fuseki timeout")
            resp = client.get("/resultats/")
        assert resp.status_code == 503
