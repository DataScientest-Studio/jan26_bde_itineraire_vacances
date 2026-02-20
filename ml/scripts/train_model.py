import pandas as pd
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report

def train_model():

    # --- PRÉPARATION DES MOTS VIDES ---
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
   
    # ASTUCE : On peut y ajouter des mots spécifiques à notre domaine
    # qui n'apportent aucune valeur sémantique
    CUSTOM_WORDS = [] # à ajouter ici
    FRENCH_STOP_WORDS.extend(CUSTOM_WORDS)



    # --- ÉTAPE 1 : CHARGEMENT DES DONNÉES ---
    # On récupère le dataset que tu as fait labelliser par Gemini
    file_path = "ml/data/final_training_set.csv"
    if not os.path.exists(file_path):
        print(f"❌ Erreur : Le fichier {file_path} est introuvable.")
        return

    df = pd.read_csv(file_path)
    
    # Sécurité : on supprime les éventuelles lignes où le texte est manquant
    df = df.dropna(subset=['input_text'])
    
    # X (Features) : Ce que le modèle lit pour apprendre (le texte préparé)
    # y (Target) : Ce que le modèle doit deviner (le thème ID de 1 à 6)
    X = df['input_text']
    y = df['themeId']

    # --- ÉTAPE 2 : SÉPARATION DES DONNÉES (SPLIT) ---
    # On divise les données en deux sets pour valider la performance du modèle.
    X_train, X_test, y_train, y_test = train_test_split(
        X, 
        y, 
        test_size=0.2,       # 20% des données serviront d'examen final (set de test)
        random_state=42,     # Graine aléatoire pour garantir des résultats reproductibles
        stratify=y           # Maintient la proportion de chaque thème (1 à 6) dans les deux sets
    )

    print(f"📊 Entraînement sur {len(X_train)} lignes, test sur {len(X_test)} lignes.")

    # --- ÉTAPE 3 : CRÉATION DU PIPELINE ---
    # Le Pipeline est une chaîne de production : le texte entre, la prédiction sort.
    pipeline = Pipeline([
        # 1. TF-IDF : Traduit le texte en chiffres exploitables par l'algorithme
        ('tfidf', TfidfVectorizer(
            # ngram_range(1,2) : analyse les mots seuls et les duos de mots (ex: "parc" + "attraction")
            ngram_range=(1, 2), 
            # max_features : limite le vocabulaire aux 10 000 termes les plus fréquents pour la performance
            max_features=5000, 
            # stop_words=None : on garde tout, car tes types filtrés contiennent déjà l'essentiel
            stop_words=FRENCH_STOP_WORDS 
        )),
        
        # 2. Random Forest : La forêt d'arbres de décision qui va "apprendre" les règles
        ('clf', RandomForestClassifier(
            # n_estimators : 100 arbres vont voter pour choisir la meilleure catégorie
            n_estimators=200, 
            # random_state : garantit que la forêt est construite de la même manière à chaque fois
            random_state=42, 
            class_weight='balanced', # Gère les classes déséquilibrées en donnant plus de poids aux thèmes rares
            # n_jobs=-1 : utilise toute la puissance de ton processeur (multi-threading)
            n_jobs=-1
        ))
    ])

    # --- ÉTAPE 4 : ENTRAÎNEMENT ---
    # C'est ici que le modèle fait le lien entre les mots et les thèmes
    print("⏳ Entraînement du modèle en cours...")
    pipeline.fit(X_train, y_train)

    # --- ÉTAPE 5 : ÉVALUATION ---
    # On demande au modèle de prédire les thèmes des 20% de données "inconnues" (X_test)
    y_pred = pipeline.predict(X_test)
    
    print("\n✅ Rapport de Classification (Qualité du modèle) :")
    # Affiche la précision pour chaque catégorie de 1 à 6
    print(classification_report(y_test, y_pred))

    # --- ÉTAPE 6 : SAUVEGARDE ---
    # On enregistre l'objet 'pipeline' complet (vectoriseur + modèle) dans un fichier
    model_dir = "ml/models"
    model_path = os.path.join(model_dir, "poi_theme_classifier.joblib")
    
    joblib.dump(pipeline, model_path)
    print(f"💾 Modèle sauvegardé avec succès : {model_path}")

if __name__ == "__main__":
    train_model()