import spacy

# Chargement du modèle de langue française
nlp = spacy.load("fr_core_news_sm")

def analyser_requete_nlp(texte: str):
    """Analyse une phrase pour extraire l'intention et le médicament ciblé."""
    doc = nlp(texte.lower())
    
    intention = "inconnu"
    medicament_cible = None
    
    # 1. Détection de l'intention grâce à la lemmatisation (racine des mots)
    mots_cles = [token.lemma_ for token in doc]
    
    if "molécule" in mots_cles or "principe" in mots_cles or "composition" in texte:
        intention = "composition"
    elif "dosage" in mots_cles or "dose" in mots_cles:
        intention = "dosage"
    elif "forme" in mots_cles or "galénique" in mots_cles:
        intention = "forme_galenique"

    # 2. Extraction de l'entité (le nom du médicament)
    # SpaCy identifie les noms propres (PROPN) ou noms communs (NOUN)
    mots_ignores = ["molécule", "principe", "actif", "dosage", "dose", "forme", "galénique", "médicament", "quel", "quelle"]
    
    for token in doc:
        if token.pos_ in ["NOUN", "PROPN"] and token.lemma_ not in mots_ignores:
            # On capitalise la première lettre pour correspondre à l'ontologie (ex: doliprane -> Doliprane)
            medicament_cible = token.text.capitalize() 
            
    return {
        "intention": intention,
        "medicament": medicament_cible
    }