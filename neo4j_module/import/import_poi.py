"""
import_poi.py
-------------
Importe les POI dans Neo4j depuis :
- un fichier JSON local (mode test)
- ou une base PostgreSQL (mode production)

Pour changer la source :
    USE_JSON = True   -> JSON
    USE_JSON = False  -> PostgreSQL
"""

import json
import psycopg2
from neo4j import GraphDatabase

# -----------------------------
# CONFIGURATION
# -----------------------------

USE_JSON = True  # <--- Mets False pour utiliser PostgreSQL

JSON_PATH = "neo4j_module/test_data/poi_sample_Paris.json"

POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "datatourisme",
    "user": "postgres",
    "password": "postgres"
}

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Nassima94!!"  


# -----------------------------
# IMPORTER CLASS
# -----------------------------

class POIImporter:

    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    # -----------------------------
    # 1) Chargement JSON
    # -----------------------------
    def load_poi_from_json(self):
        print(f"Chargement du fichier JSON : {JSON_PATH}")
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"{len(data)} POI chargés depuis le JSON.")
        return data

    # -----------------------------
    # 2) Chargement PostgreSQL
    # -----------------------------
    def load_poi_from_postgres(self):
        print("Connexion à PostgreSQL...")
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cur = conn.cursor()

        query = """
            SELECT poi_id, label, lat, lon, short_description, type,
                   theme, city_id, city_name, postal_code, insee_code
            FROM poi_table;
        """

        cur.execute(query)
        rows = cur.fetchall()

        columns = [desc[0] for desc in cur.description]
        data = [dict(zip(columns, row)) for row in rows]

        cur.close()
        conn.close()

        print(f"{len(data)} POI chargés depuis PostgreSQL.")
        return data

    # -----------------------------
    # 3) Import dans Neo4j
    # -----------------------------
    def import_poi(self, pois):
        with self.driver.session() as session:
            for poi in pois:

                # POI node
                session.run(
                    """
                    MERGE (p:POI {poi_id: $poi_id})
                    SET p.label = $label,
                        p.lat = $lat,
                        p.lon = $lon,
                        p.short_description = $short_description,
                        p.type = $type,
                        p.theme = $theme,
                        p.city_id = $city_id
                    """,
                    **poi
                )

                # City node
                session.run(
                    """
                    MERGE (c:City {city_id: $city_id})
                    SET c.name = $city_name,
                        c.postal_code = $postal_code,
                        c.insee_code = $insee_code
                    """,
                    **poi
                )

                # Theme node
                session.run(
                    """
                    MERGE (t:Theme {name: $theme})
                    """,
                    **poi
                )

                # Relations
                session.run(
                    """
                    MATCH (p:POI {poi_id: $poi_id})
                    MATCH (c:City {city_id: $city_id})
                    MERGE (p)-[:IN_CITY]->(c)
                    """,
                    **poi
                )

                session.run(
                    """
                    MATCH (p:POI {poi_id: $poi_id})
                    MATCH (t:Theme {name: $theme})
                    MERGE (p)-[:HAS_THEME]->(t)
                    """,
                    **poi
                )

        print("Import terminé.")

def create_near_relations_for_city(self, city_id, max_distance=3000):
    """
    Crée des relations :NEAR entre POI d'une même ville,
    uniquement si la distance est inférieure à max_distance (en mètres).
    """
    with self.driver.session() as session:
        session.run(
            """
            MATCH (p1:POI {city_id: $city})
            MATCH (p2:POI {city_id: $city})
            WHERE p1 <> p2
            WITH p1, p2,
                 point.distance(
                     point({latitude: p1.lat, longitude: p1.lon}),
                     point({latitude: p2.lat, longitude: p2.lon})
                 ) AS d
            WHERE d <= $max_distance
            MERGE (p1)-[r:NEAR]->(p2)
            SET r.distance = d
            """,
            city=city_id,
            max_distance=max_distance
        )

    print(f"Relations NEAR créées pour la ville {city_id}")



# -----------------------------
# MAIN
# -----------------------------

if __name__ == "__main__":
    importer = POIImporter()

    if USE_JSON:
        pois = importer.load_poi_from_json()
    else:
        pois = importer.load_poi_from_postgres()

    importer.import_poi(pois)

    importer.close()

    print("\nImport terminé.\n")


