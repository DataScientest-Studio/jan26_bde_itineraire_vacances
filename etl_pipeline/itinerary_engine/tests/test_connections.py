import psycopg2
from pymongo import MongoClient
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

# Charger les variables d'environnement
load_dotenv(".env.local")

# -----------------------------
# PostgreSQL
# -----------------------------
def test_postgres_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            dbname=os.getenv("POSTGRES_DB")
        )
        conn.close()
        print("✅ PostgreSQL : Connexion OK")
    except Exception as e:
        print("❌ PostgreSQL : Échec de connexion")
        print(e)

# -----------------------------
# MongoDB
# -----------------------------
def test_mongo_connection():
    try:
        client = MongoClient(
            host=os.getenv("MONGO_HOST"),
            port=int(os.getenv("MONGO_PORT"))
        )
        client.admin.command("ping")
        print("✅ MongoDB : Connexion OK")
    except Exception as e:
        print("❌ MongoDB : Échec de connexion")
        print(e)

# -----------------------------
# Neo4j
# -----------------------------
def test_neo4j_connection():
    try:
        driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
        )
        with driver.session() as session:
            session.run("RETURN 1")
        print("✅ Neo4j : Connexion OK")
    except Exception as e:
        print("❌ Neo4j : Échec de connexion")
        print(e)

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    print("🔍 Test des connexions aux bases de données...\n")
    test_postgres_connection()
    test_mongo_connection()
    test_neo4j_connection()
