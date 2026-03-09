from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Charge automatiquement le fichier .env
load_dotenv()

def get_neo4j_driver():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")

    # Debug temporaire
    print(">>> URI =", uri)
    print(">>> USER =", user)
    print(">>> PASSWORD =", password)

    return GraphDatabase.driver(uri, auth=(user, password))

