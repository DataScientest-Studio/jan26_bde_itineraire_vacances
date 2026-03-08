import pandas as pd
import json
import os

def merge_labels_and_texts():
    # Chemins des fichiers
    csv_path = "ml/data/samples_to_label.csv"
    json_path = "ml/data/gemini_classification.json"
    output_path = "ml/data/final_training_set.csv"

    # 1. Chargement des données
    if not os.path.exists(csv_path) or not os.path.exists(json_path):
        print("❌ Erreur : Fichiers source manquants.")
        return

    df_texts = pd.read_csv(csv_path)
    
    with open(json_path, "r", encoding='utf-8') as f:
        labels_data = json.load(f)
    df_labels = pd.DataFrame(labels_data)

    # 2. INNER JOIN
    # On ne garde que les POI qui sont présents dans les deux fichiers
    dataset = pd.merge(df_texts, df_labels, on="uuid", how="inner")
    initial_count = len(dataset)
    print(f"🔗 Après Inner Join : {initial_count} lignes.")

    # 3. SUPPRESSION DES DOUBLONS
    # On se base sur l'UUID pour garantir l'unicité
    dataset = dataset.drop_duplicates(subset=['uuid'])
    after_duplicates = len(dataset)
    print(f"🗑️ Doublons supprimés : {initial_count - after_duplicates} lignes.")

    # 4. SUPPRESSION SI THEME VIDE OU INVALIDE
    # On s'assure que themeId est présent, non nul, et supérieur à 0
    # On utilise pd.to_numeric pour forcer en nombre au cas où Gemini renverrait des strings
    dataset['themeId'] = pd.to_numeric(dataset['themeId'], errors='coerce')
    
    # On filtre : on garde seulement les lignes où themeId n'est pas NaN
    dataset = dataset.dropna(subset=['themeId'])
    
    # On s'assure que c'est un entier (plus propre pour le ML)
    dataset['themeId'] = dataset['themeId'].astype(int)
    
    final_count = len(dataset)
    print(f"🧹 Après suppression des thèmes vides/invalides : {final_count} lignes.")

    # 5. SAUVEGARDE
    dataset.to_csv(output_path, index=False, encoding='utf-8')
    print("-" * 30)
    print(f"✅ Dataset d'entraînement final prêt : {output_path}")
    print(f"📊 Répartition des thèmes :\n{dataset['themeId'].value_counts().sort_index()}")

if __name__ == "__main__":
    merge_labels_and_texts()