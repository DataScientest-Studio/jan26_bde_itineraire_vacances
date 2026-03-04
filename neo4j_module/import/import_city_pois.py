from neo4j import GraphDatabase
import json
import sys
from neo4j_module.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

class CityPOIImporter:

    def __init__(self): 
        self.driver = GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USER, NEO4J_PASSWORD) 
            )

    def close(self):
        self.driver.close()

    def load_pois(self, json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def import_city(self, city_name, pois):
        with self.driver.session() as session:

            # Supprimer les anciens POI de la ville
            session.run(
                """
                MATCH (p:POI {city: $city})
                DETACH DELETE p
                """,
                city=city_name
            )

            # Importer les nouveaux POI
            for p in pois:
                session.run(
                    """
                    CREATE (poi:POI {
                        poi_id: $id,
                        label: $label,
                        lat: $lat,
                        lon: $lon,
                        themes: $themes,
                        city: $city
                    })
                    """,
                    id=p["poi_id"],
                    label=p["label"],
                    lat=p["lat"],
                    lon=p["lon"],
                    themes=p["themes"],
                    city=city_name
                )


def main():
    if len(sys.argv) != 3:
        print("Usage: python import_city_pois.py <city_name> <json_file>")
        return

    city = sys.argv[1]
    json_file = sys.argv[2]

    importer = CityPOIImporter()  # <-- correction ici

    pois = importer.load_pois(json_file)
    print(f"Import de {len(pois)} POI pour la ville : {city}")

    importer.import_city(city, pois)
    importer.close()

    print("Import terminé.")



if __name__ == "__main__":
    main()
