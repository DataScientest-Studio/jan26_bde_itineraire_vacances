import os
from pymongo import MongoClient
from dotenv import load_dotenv
from collections import Counter

load_dotenv()

def flatten_keys(obj, prefix=''):
    """Explore récursivement l'objet et retourne les clés en notation point."""
    keys = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{prefix}.{k}" if prefix else k
            keys.append(new_key)
            keys.extend(flatten_keys(v, new_key))
    elif isinstance(obj, list):
        for item in obj:
            keys.extend(flatten_keys(item, prefix))
    return list(set(keys)) # On évite les doublons si une clé existe plusieurs fois dans une liste

def analyze_deep_schema(sample_size=10000):
    client = MongoClient(
        host=os.getenv("MONGO_HOST"),
        port=int(os.getenv("MONGO_PORT")),
        username=os.getenv("MONGO_INITDB_ROOT_USERNAME"),
        password=os.getenv("MONGO_INITDB_ROOT_PASSWORD")
    )
    db = client[os.getenv("MONGO_DB_NAME")]
    collection = db[os.getenv("MONGO_COLLECTION_NAME")]

    # On échantillonne pour la performance, ou on prend tout (None)
    total_to_scan = collection.count_documents({})
    limit = sample_size if sample_size else total_to_scan
    
    print(f"Analyse de {limit} documents (sur {total_to_scan})...")
    
    key_counter = Counter()
    cursor = collection.find({}).limit(limit) if sample_size else collection.find({})

    for doc in cursor:
        keys = flatten_keys(doc)
        key_counter.update(keys)

    print(f"\n{'Clé (Notation Point)':<50} | {'Présence (%)':<10}")
    print("-" * 65)

    # Trier par fréquence
    # 
    for key, count in key_counter.most_common():
        percentage = (count / limit) * 100
        if percentage > 5: # On affiche uniquement ce qui est significatif
            print(f"{key[:48]:<50} | {percentage:>8.1f}%")

if __name__ == "__main__":
    # analyze_deep_schema(sample_size=10000)
    analyze_deep_schema(sample_size=None) 
    # Pour analyser tout, mais ça peut être long selon la taille de la collection