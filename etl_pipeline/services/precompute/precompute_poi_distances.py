import math
from neo4j import GraphDatabase
from services.poi_reader import get_pois_for_city, get_all_cities


BATCH_SIZE = 5000


def _chunkify(lst, size):
    """Découpe une liste en chunks."""
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def _prepare_pairs(pois):
    """
    Génère toutes les paires POI → POI pour une ville.
    Optimisé : pas de self-pair, pas de doublons inversés.
    """
    pairs = []
    for i in range(len(pois)):
        for j in range(i + 1, len(pois)):
            a = pois[i]
            b = pois[j]
            pairs.append({
                "a_id": a["poi_id"],
                "a_lat": a["lat"],
                "a_lon": a["lon"],
                "b_id": b["poi_id"],
                "b_lat": b["lat"],
                "b_lon": b["lon"],
            })
    return pairs


def _write_pairs_to_neo4j(driver, pairs):
    """
    Envoie les paires en batch UNWIND dans Neo4j.
    Optimisation ×100 : un seul round-trip par batch.
    """
    query = """
        UNWIND $pairs AS pair
        MATCH (a:POI {id: pair.a_id})
        MATCH (b:POI {id: pair.b_id})
        MERGE (a)-[d:DISTANCE_TO]->(b)
        SET d.km = point.distance(
            point({latitude: pair.a_lat, longitude: pair.a_lon}),
            point({latitude: pair.b_lat, longitude: pair.b_lon})
        ) / 1000
    """

    with driver.session() as session:
        for chunk in _chunkify(pairs, BATCH_SIZE):
            session.run(query, pairs=chunk)


def compute_distances_for_city(driver, city: str):
    """
    Précompute optimisé ×100 pour une ville.
    """
    pois = get_pois_for_city(city)

    if len(pois) < 2:
        print(f"[SKIP] {city} : pas assez de POIs")
        return

    print(f"[INFO] Précompute {city} : {len(pois)} POIs")

    pairs = _prepare_pairs(pois)
    print(f"[INFO] {city} : {len(pairs)} paires générées")

    _write_pairs_to_neo4j(driver, pairs)

    print(f"[DONE] Précompute terminé pour {city}")


def precompute_all_cities(driver):
    """
    FULL : précompute pour toutes les villes.
    """
    cities = get_all_cities()
    print(f"[INFO] {len(cities)} villes détectées")

    for city in cities:
        compute_distances_for_city(driver, city)

