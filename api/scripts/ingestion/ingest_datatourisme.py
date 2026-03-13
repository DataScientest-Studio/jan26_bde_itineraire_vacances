import os
import requests
from pymongo import ReplaceOne
from scripts.utils.db_connect import get_mongo_client_api

print(f"ingest_datatourisme STARTED - PID: {os.getpid()}")

def get_last_update_from_mongo(collection):
    """Récupère la date de lastUpdateDatatourisme la plus récente pour l'incrémental."""
    last_doc = collection.find_one(sort=[("lastUpdateDatatourisme", -1)])
    return last_doc["lastUpdateDatatourisme"] if last_doc else None

def ingest_data():
    # Connexion MongoDB via les variables d'environnement
    collection = get_mongo_client_api()

    # Liste des clés API pour la bascule (failover)
    api_keys = [os.getenv("DATA_TOURISME_API_KEY"), os.getenv("DATA_TOURISME_API_KEY_2")]

    # 1. Détermination de la date de départ (Incrémental)
    last_date = get_last_update_from_mongo(collection)
    
    if last_date:
        url = f"https://api.datatourisme.fr/v1/catalog?sort=lastUpdateDatatourisme&page_size=250&filters=lastUpdateDatatourisme[gte]={last_date}"
        print(f"Mode Incrémental : synchronisation depuis le {last_date}")
    else:
        url = "https://api.datatourisme.fr/v1/catalog?sort=lastUpdateDatatourisme&page_size=250"
        print("Mode Initialisation : récupération totale de la base")

    # 2. Boucle de traitement des pages de l'API
    while url:
        response = None

        try:
            # Tentative d'appel API avec gestion des clés
            for key in api_keys:
                if not key:
                    continue
                
                res = requests.get(url, headers={'X-API-Key': key}, timeout=30)
                
                # Si quota atteint ou accès refusé, on tente la clé suivante
                if res.status_code in [403, 429]:
                    print(f"Clé API limitée (Status {res.status_code}). Essai avec la clé suivante...")
                    continue
                
                # Vérifie les autres erreurs HTTP (404, 500, etc.)
                res.raise_for_status()
                
                # Succès !
                response = res
                break 

            if not response:
                raise Exception("Toutes les clés API ont échoué ou sont limitées.")

            # 3. Traitement des données
            data = response.json()
            objects = data.get("objects", [])
            
            if not objects:
                print("Fin de la récupération : aucun nouvel objet.")
                break

            print(f"Récupération de {len(objects)} objets réussie.")

            operations = []
            for obj in objects:
                obj_id = obj["uuid"]
                obj["_id"] = obj_id
                
                operations.append(
                    ReplaceOne(
                        filter={"_id": obj_id},
                        replacement=obj,
                        upsert=True
                    )
                )
            
            if operations:
                res = collection.bulk_write(operations)
                print(f"Batch traité - MAJ/Upsert : {res.upserted_count + res.modified_count}")

            # Passage à la page suivante
            url = data.get("meta", {}).get("next")

        except requests.exceptions.HTTPError as http_err:
            raise SystemExit(f"Erreur HTTP critique : {http_err}")
        except Exception as err:
            raise SystemExit(f"Erreur lors de l'ingestion : {err}")

    print("Ingestion terminée avec succès.")

if __name__ == "__main__":
    ingest_data()