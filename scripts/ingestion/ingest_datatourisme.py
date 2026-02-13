import os
import requests
from pymongo import MongoClient, ReplaceOne
from dotenv import load_dotenv
#from datetime import datetime, timedelta

# Charge les variables du fichier .env
load_dotenv()

def get_last_update_from_mongo(collection):
    """Récupère la date de lastUpdateDatatourisme la plus récente pour l'incrémental."""
    # On cherche le document avec la date la plus élevée
    last_doc = collection.find_one(sort=[("lastUpdateDatatourisme", -1)])
    return last_doc["lastUpdateDatatourisme"] if last_doc else None

def ingest_data():
    # Connexion MongoDB via les variables d'environnement
    client = MongoClient(
        host=os.getenv("MONGO_HOST"),
        port=int(os.getenv("MONGO_PORT")),
        username=os.getenv("MONGO_INITDB_ROOT_USERNAME"),
        password=os.getenv("MONGO_INITDB_ROOT_PASSWORD")
    )
    
    # Utilisation de tes variables pour la DB et la Collection
    db = client[os.getenv("MONGO_DB_NAME")]
    collection = db[os.getenv("MONGO_COLLECTION_NAME")]

    # 1. Détermination de la date de départ (Incrémental)
    last_date = get_last_update_from_mongo(collection)
    
    if last_date:
        # On reprend à partir de la dernière date connue 
        url = f"https://api.datatourisme.fr/v1/catalog?sort=lastUpdateDatatourisme&page_size=250&filters=lastUpdateDatatourisme[gte]={last_date}"
        print(f"Mode Incrémental : synchronisation depuis le {last_date}")
    else:
        # Premier lancement : on récupère tout 
        url = "https://api.datatourisme.fr/v1/catalog?sort=lastUpdateDatatourisme&page_size=250"
        print("Mode Initialisation : récupération totale de la base")

    # 2. Boucle de traitement des pages de l'API
    while url:
        try:
            headers = {
                'X-API-Key': os.getenv("DATA_TOURISME_API_KEY")
            }
            print(url)
            response = requests.get(url, headers=headers)
    
            # 1. Vérifie si le code est 200, sinon lève une HTTPError
            response.raise_for_status()
    
            # 2. Si on arrive ici, c'est que c'est un succès (200)
            data = response.json()
    
            objects = data.get("objects", [])
            print(f"Récupération de {len(objects)} objets réussie.")
            
            if not objects:
                print("Fin de la récupération : aucun nouvel objet.")
                break

            operations = []
            for obj in objects:
                # On utilise l'UUID comme PK (_id) pour identifier les doublons 
                obj_id = obj["uuid"]
                obj["_id"] = obj_id
                
                # ReplaceOne avec upsert=True : remplace tout le document s'il existe 
                operations.append(
                    ReplaceOne(
                        filter={"_id": obj_id},
                        replacement=obj,
                        upsert=True
                    )
                )
            
            if operations:
                res = collection.bulk_write(operations)
                print(f"Batch traité - Insérés/MAJ : {res.upserted_count + res.modified_count}")

            # Pagination : passage à l'URL suivante fournie par l'API 
            url = data.get("meta", {}).get("next")

        except requests.exceptions.HTTPError as http_err:
            # Erreur spécifique au protocole HTTP (ex: 401 Unauthorized)
            raise SystemExit(f"Erreur HTTP : {http_err}")
        except Exception as err:
            # Autres erreurs (ex: problème de connexion réseau)
            raise SystemExit(f"Une erreur est survenue : {err}")

    print("Ingestion terminée avec succès.")

if __name__ == "__main__":
    ingest_data()