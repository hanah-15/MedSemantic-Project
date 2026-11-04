import spacy
from spacy.matcher import PhraseMatcher
import difflib

# Chargement du modèle de langue française
nlp = spacy.load("fr_core_news_sm")

# Dictionnaire d'intentions avec leurs mots-clés, lemmes et synonymes
INTENTIONS_KEYWORDS = {
    "composition": {
        "molécule", "molecule", "principe", "excipient", "composition", "composer",
        "contenir", "ingrédient", "ingredient", "substance", "formule", "chimique"
    },
    "dosage": {
        "dosage", "dose", "doser", "quantité", "quantite", "combien", "mg",
        "gramme", "g", "concentration", "force", "posologie", "taux"
    },
    "forme_galenique": {
        "forme", "galénique", "galenique", "format", "présentation", "presentation",
        "pilule", "comprimé", "comprime", "gélule", "gelule", "sirop", "sachet",
        "pommade", "injectable", "type", "goutte", "suppositoire"
    }
}

# Médicaments de référence connus dans l'ontologie pour tolérance typo et match exact
MEDICAMENTS_CONNUS = [
    "Doliprane", "Advil", "Glucophage", "Amlor", "Paracetamol",
    "Metformine", "Ibuprofene", "Amlodipine", "Aspirine"
]

# Matcher insensible à la casse pour les médicaments
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
patterns = [nlp.make_doc(nom) for nom in MEDICAMENTS_CONNUS]
matcher.add("MEDICAMENT", patterns)

def corriger_typo(terme: str):
    """Tente de corriger une faute de frappe avec les médicaments connus."""
    terme_clean = terme.strip().lower()
    mapping = {m.lower(): m for m in MEDICAMENTS_CONNUS}
    matches = difflib.get_close_matches(terme_clean, list(mapping.keys()), n=1, cutoff=0.7)
    if matches:
        return mapping[matches[0]]
    return None

def analyser_requete_nlp(texte: str):
    """Analyse une phrase pour extraire l'intention et le médicament ciblé."""
    doc = nlp(texte)

    # 1. Détection de l'entité médicament via PhraseMatcher en priorité
    matches = matcher(doc)
    medicament_cible = None

    if matches:
        match_id, start, end = matches[0]
        medicament_cible = doc[start:end].text.capitalize()
    else:
        # Recherche robuste de médicament même avec fautes de frappe ou mauvais tag POS
        mots_ignores = {
            "quel", "quelle", "quels", "quelles", "est", "sont", "le", "la", "les", "l",
            "du", "de", "des", "d", "un", "une", "médicament", "medicament", "donne", "moi"
        }

        # Test 1 : recherche de match flou sur chaque token
        for token in doc:
            token_str = token.text.lower()
            token_lemma = token.lemma_.lower()
            if token_str in mots_ignores or token_lemma in mots_ignores:
                continue

            match_found = corriger_typo(token_lemma) or corriger_typo(token_str)
            if match_found:
                medicament_cible = match_found
                break

        # Test 2 : si aucun médicament connu n'a matché, prendre le premier nom propre / nom commun pertinent
        if not medicament_cible:
            for token in doc:
                token_lemma = token.lemma_.lower()
                if token.pos_ in ["PROPN", "NOUN", "X"] and token_lemma not in mots_ignores:
                    est_mot_cle = any(token_lemma in s for s in INTENTIONS_KEYWORDS.values())
                    if not est_mot_cle:
                        medicament_cible = token.text.capitalize()
                        break

    # 2. Détection de l'intention par lemmes et mots-clés
    lemmes_phrase = {token.lemma_.lower() for token in doc}
    mots_phrase = set(texte.lower().split())
    tokens_vus = lemmes_phrase.union(mots_phrase)

    intention = "inconnu"
    for intent, keywords in INTENTIONS_KEYWORDS.items():
        if tokens_vus.intersection(keywords):
            intention = intent
            break

    return {
        "intention": intention,
        "medicament": medicament_cible,
        "texte_original": texte
    }
