import pandas as pd
import joblib
import os
import re
import unicodedata
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report

def clean_text(text):
    """
    Nettoie le texte pour faciliter l'apprentissage du modèle :
    Minuscules, suppression accents, ponctuation, et espaces superflus.
    """
    if not text or pd.isna(text):
        return ""
    
    # 1. Passage en minuscules
    text = str(text).lower()
    
    # 2. Suppression des accents (Normalisation NFD)
    text = ''.join((c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn'))
    
    # 3. Remplacement des apostrophes et tirets par des espaces
    text = text.replace("'", " ").replace("’", " ").replace("-", " ")
    
    # 4. Suppression de la ponctuation et caractères spéciaux (on garde lettres et chiffres)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    
    # 5. Suppression des doubles espaces et espaces en début/fin
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def train_model():
    # --- PRÉPARATION DES MOTS VIDES (STOP WORDS) ---
    # EXtrait C/C au lieu d'utilisaer une librairie car je n'ai pas réussi.
    FRENCH_STOP_WORDS = [
        "a", "au", "aux", "avec", "ce", "ces", "dans", "de", "des", "du", "elle", "en", "et", "eux", 
        "il", "je", "la", "le", "leur", "lui", "ma", "mais", "me", "même", "mes", "moi", "mon", 
        "ne", "nos", "notre", "nous", "on", "ou", "par", "pas", "pour", "qu", "que", "qui", "sa", 
        "se", "ses", "son", "sur", "ta", "te", "tes", "toi", "ton", "tu", "un", "une", "vos", "votre", 
        "vous", "c", "d", "j", "l", "m", "n", "s", "t", "y", "été", "étée", "étées", "étés", "étant", 
        "suis", "es", "est", "sommes", "êtes", "sont", "serai", "seras", "sera", "serons", "serez", 
        "seront", "serais", "serait", "serions", "seriez", "seraient", "étais", "était", "étions", 
        "étiez", "étaient", "fus", "fut", "fûmes", "fûtes", "furent", "sois", "soit", "soyons", 
        "soyez", "soient", "fusse", "fusses", "fût", "fussions", "fussiez", "fussent", "ayant", 
        "eu", "eue", "eues", "eus", "ai", "as", "a", "avons", "avez", "ont", "aurai", "auras", 
        "aura", "aurons", "aurez", "auront", "aurais", "aurait", "aurions", "auriez", "auraient", 
        "avais", "avait", "avions", "aviez", "avaient", "eut", "eûmes", "eûtes", "eurent", "aie", 
        "aies", "ait", "ayons", "ayez", "aient", "eusse", "eusses", "eût", "eussions", "eussiez", "eussent"
    ]
    
    # --- ÉTAPE 1 : CHARGEMENT ET NETTOYAGE DES DONNÉES ---
    file_path = "ml/data/final_training_set.csv"
    if not os.path.exists(file_path):
        print(f"❌ Erreur : Le fichier {file_path} est introuvable.")
        return

    df = pd.read_csv(file_path)
    
    # Nettoyage profond du texte avant l'entraînement
    print("🧹 Nettoyage du texte en cours...")
    df['input_text_clean'] = df['input_text'].apply(clean_text)
    
    # Suppression des lignes devenues vides après nettoyage
    df = df[df['input_text_clean'] != ""]
    
    X = df['input_text_clean']
    y = df['themeId']

    # --- ÉTAPE 2 : SÉPARATION DES DONNÉES (SPLIT) ---
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=0.2, #seulement 20% pour le test, vu la taille limitée du dataset
        random_state=42, 
        stratify=y # Important pour garder l'équilibre des classes
    )

    print(f"📊 Entraînement sur {len(X_train)} lignes, test sur {len(X_test)} lignes.")

    # --- ÉTAPE 3 : CRÉATION DU PIPELINE ---
    # Le Pipeline regroupe la vectorisation et la classification en un seul objet
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            ngram_range=(1, 2), # Unigrammes et Bigrammes
            max_features=5000, 
            stop_words=FRENCH_STOP_WORDS
        )),
        ('clf', RandomForestClassifier(
            n_estimators=200, 
            random_state=42, 
            class_weight='balanced', # Crucial pour compenser les thèmes rares (3 et 4)
            n_jobs=-1
        ))
    ])

    # --- ÉTAPE 4 : ENTRAÎNEMENT ---
    print("⏳ Entraînement du modèle avec rééquilibrage des classes...")
    pipeline.fit(X_train, y_train)

    # --- ÉTAPE 5 : ÉVALUATION ---
    y_pred = pipeline.predict(X_test)
    print("\n✅ Rapport de Classification final :")
    print(classification_report(y_test, y_pred))

    # --- ÉTAPE 6 : SAUVEGARDE ---
    # On sauvegarde le pipeline entier : il contient les StopWords et la logique de vectorisation
    model_dir = "ml/models"
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "poi_theme_classifier.joblib")
    
    # Sauvegarde de l'objet complet
    joblib.dump(pipeline, model_path)
    print(f"💾 Pipeline complet (Vect + Model) sauvegardé : {model_path}")

if __name__ == "__main__":
    train_model()