import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def reset_mongo():
    # Connexion
    client = MongoClient(
        host=os.getenv("MONGO_HOST"),
        port=int(os.getenv("MONGO_PORT")),
        username=os.getenv("MONGO_INITDB_ROOT_USERNAME"),
        password=os.getenv("MONGO_INITDB_ROOT_PASSWORD")
    )

    # Liste des bases à protéger (système)
    protected_dbs = ['admin', 'config', 'local']

    try:
        # Récupérer toutes les bases de données
        db_names = client.list_database_names()
        
        for db_name in db_names:
            if db_name not in protected_dbs:
                print(f"Suppression de la base de données : {db_name}...")
                client.drop_database(db_name)
                print(f"Base {db_name} supprimée.")
            else:
                print(f"Base système ignorée : {db_name}")

        print("\nNettoyage terminé. MongoDB est vide (hors système).")

    except Exception as e:
        print(f"Erreur lors du nettoyage : {e}")

if __name__ == "__main__":
    confirm = input("Êtes-vous sûr de vouloir supprimer TOUTES les bases de données non-système ? (y/n) : ")
    if confirm.lower() == 'y':
        reset_mongo()
    else:
        print("Opération annulée.")