import os
import psycopg2
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def get_mongo_client():
    """Crée et retourne une collection MongoDB."""
    client = MongoClient(
        host=os.getenv("MONGO_HOST"),
        port=int(os.getenv("MONGO_PORT")),
        username=os.getenv("MONGO_INITDB_ROOT_USERNAME"),
        password=os.getenv("MONGO_INITDB_ROOT_PASSWORD")
    )
    db = client[os.getenv("MONGO_DB_NAME")]
    return db[os.getenv("MONGO_COLLECTION_NAME")]

def get_pg_conn():
    """Crée et retourne une connexion PostgreSQL."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
    
def get_pg_conn_api():
    """Crée et retourne une connexion PostgreSQL."""
    return psycopg2.connect(
        host=os.getenv("DB_PG_HOST"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
    
def get_mongo_client_api():
    """Crée et retourne une collection MongoDB."""
    client = MongoClient(
        host=os.getenv("DB_MDB_HOST"),
        port=int(os.getenv("MONGO_PORT")),
        username=os.getenv("MONGO_INITDB_ROOT_USERNAME"),
        password=os.getenv("MONGO_INITDB_ROOT_PASSWORD")
    )
    db = client[os.getenv("MONGO_DB_NAME")]
    return db[os.getenv("MONGO_COLLECTION_NAME")]