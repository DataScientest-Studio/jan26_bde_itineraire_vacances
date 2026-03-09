import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

print(f"DEBUG - Host: {os.getenv('MONGO_HOST')}")
print(f"DEBUG - Port: {os.getenv('MONGO_PORT')}")
print(f"DEBUG - User: {os.getenv('MONGO_INITDB_ROOT_USERNAME')}")

# Connexion via les variables du .env
client = MongoClient(
    host=os.getenv("MONGO_HOST"),
    port=int(os.getenv("MONGO_PORT")),
    username=os.getenv("MONGO_INITDB_ROOT_USERNAME"),
    password=os.getenv("MONGO_INITDB_ROOT_PASSWORD")
)

try:
    # On tente d'insérer un document de test
    db = client[os.getenv("MONGO_DB_NAME")] # On peut utiliser le même nom de projet
    collection = db["test_collection"]
    collection.insert_one({"message": "Connexion réussie !"})
    print("Document inséré avec succès dans MongoDB.")
except Exception as e:
    print(f"Erreur de connexion : {e}")