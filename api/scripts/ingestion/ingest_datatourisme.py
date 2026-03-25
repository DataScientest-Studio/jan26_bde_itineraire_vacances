import os
import requests
import time
from pymongo import ReplaceOne
from scripts.utils.db_connect import get_mongo_client_api

print(f"ingest_datatourisme STARTED - PID: {os.getpid()}")

def get_last_update_from_mongo(collection):
    """Récupère la date de lastUpdateDatatourisme la plus récente pour l'incrémental."""
    last_doc = collection.find_one(sort=[("lastUpdateDatatourisme", -1)])
    return last_doc["lastUpdateDatatourisme"] if last_doc else None

def ingest_data():
    # 1. Initialisation
    collection = get_mongo_client_api()
    api_keys = [os.getenv("DATA_TOURISME_API_KEY"), os.getenv("DATA_TOURISME_API_KEY_2")]
    
    # Nettoyage des clés vides
    api_keys = [k for k in api_keys if k]
    if not api_keys:
        raise SystemExit("❌ Aucune clé API trouvée dans les variables d'environnement.")

    # 2. Détermination de l'URL (Incrémental ou Initial)
    last_date = get_last_update_from_mongo(collection)
    
    if last_date:
        url = f"https://api.datatourisme.fr/v1/catalog?sort=lastUpdateDatatourisme&page_size=250&filters=lastUpdateDatatourisme[gte]={last_date}"
        print(f"🔄 Mode Incrémental : depuis le {last_date}")
    else:
        url = "https://api.datatourisme.fr/v1/catalog?sort=lastUpdateDatatourisme&page_size=250"
        print("🚀 Mode Initialisation : récupération totale")

    page_count = 0

    # 3. Boucle principale de pagination
    while url:
        page_count += 1
        response = None
        
        # Tentative avec les différentes clés
        for i, key in enumerate(api_keys):
            try:
                res = requests.get(url, headers={'X-API-Key': key}, timeout=30)
                
                if res.status_code == 200:
                    response = res
                    break # Clé OK, on sort du test des clés
                
                if res.status_code in [403, 429]:
                    print(f"⚠️ Clé n°{i+1} limitée (Status {res.status_code}). Tentative suivante...")
                    continue
                
                # Si autre erreur HTTP (ex: 500), on lève une exception
                res.raise_for_status()
                
            except requests.exceptions.RequestException as e:
                print(f"❌ Erreur réseau avec la clé n°{i+1} : {e}")
                continue

        # Vérification si une des clés a fonctionné
        if not response:
            print("🛑 ÉCHEC CRITIQUE : Toutes les clés API sont épuisées ou invalides.")
            raise RuntimeError("Quotas API épuisés pour toutes les clés. Ingestion incomplète.")

        # 4. Traitement des données de la page
        data = response.json()
        objects = data.get("objects", [])
        
        if not objects:
            print(f"🏁 Fin du flux : aucun objet sur la page {page_count}.")
            break

        operations = []
        for obj in objects:
            obj_id = obj["uuid"]
            obj["_id"] = obj_id
            operations.append(
                ReplaceOne(filter={"_id": obj_id}, replacement=obj, upsert=True)
            )
        
        if operations:
            res = collection.bulk_write(operations)
            print(f"📄 Page {page_count} : {len(objects)} objets traités (Upserts/MAJ: {res.upserted_count + res.modified_count})")

        # 5. Préparation de la page suivante
        url = data.get("meta", {}).get("next")
        
        # Petite pause pour ne pas saturer l'API et éviter les bans trop rapides
        if url:
            time.sleep(0.5)

    print(f"✅ Ingestion terminée. Total pages : {page_count}")

if __name__ == "__main__":
    try:
        ingest_data()
    except Exception as e:
        print(f"💥 Erreur fatale : {e}")
        raise