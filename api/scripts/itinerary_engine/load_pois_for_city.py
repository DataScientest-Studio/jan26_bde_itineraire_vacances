from scripts.utils.db_connect import get_neo4j_driver

def load_pois_for_city(postal_code_insee, theme_label):
    """
    Récupère les POIs depuis Neo4j en utilisant les relations du graphe.
    """
    driver = get_neo4j_driver()
    
    query = """
    MATCH (c:City {postalcodeinsee: $postal_code_insee})<-[:LOCATED_IN]-(p:POI)-[:HAS_THEME]->(t:Theme)
    WHERE toLower(t.label) CONTAINS toLower(trim($theme_label))
    RETURN p.uuid AS poi_id, p.label AS label, p.latitude AS lat, p.longitude AS lon, t.label AS theme_name
    """
    
    with driver.session() as session:
        # C'EST ICI QUE ÇA PLANTAIT : le kwarg doit être postal_code_insee=postal_code_insee
        result = session.run(query, postal_code_insee=postal_code_insee, theme_label=theme_label)
        
        pois = []
        for record in result:
            try:
                pois.append({
                    "poi_id": record["poi_id"],
                    "label": record["label"] or "Sans nom",
                    "lat": float(record["lat"]),
                    "lon": float(record["lon"]),
                    "theme": record["theme_name"]
                })
            except (TypeError, ValueError):
                continue
        
    driver.close()
    
    print(f"🛠️  [DEBUG Neo4j] {len(pois)} POIs trouvés pour CP INSEE='{postal_code_insee}' / Thème='{theme_label}'")
    
    return pois