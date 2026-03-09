from etl.neo4j_module.neo4j_connection import get_neo4j_driver

def setup_indexes():
    driver = get_neo4j_driver()
    with driver.session() as session:
        print("[NEO4J] Création de l'index spatial POI...")
        session.run("""
            CREATE INDEX poi_location_index IF NOT EXISTS
            FOR (p:POI)
            ON (p.location)
        """)
    driver.close()
    print("[NEO4J] Index spatial créé.")
