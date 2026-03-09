import os
from etl.neo4j_module.neo4j_connection import get_neo4j_driver
from etl.postgres_module.extract_full import (
    get_all_pois,
    get_all_cities,
    get_all_themes,
    get_all_poi_themes
)

BATCH_SIZE = 300

def chunked(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i:i+size]


def run_full_import():
    neo4j_driver = get_neo4j_driver()

    print(">>> Import FULL Neo4j")

    cities = get_all_cities()
    pois = get_all_pois()
    themes = get_all_themes()
    poi_themes = get_all_poi_themes()

    print(f"[FULL] {len(cities)} villes")
    print(f"[FULL] {len(themes)} thèmes")
    print(f"[FULL] {len(pois)} POIs")
    print(f"[FULL] {len(poi_themes)} relations POI->Thème")

    # -----------------------------
    # RESET
    # -----------------------------
    print(">>> RESET Neo4j")
    with neo4j_driver.session() as session:
        session.execute_write(lambda tx: tx.run("MATCH (n) DETACH DELETE n"))

    # -----------------------------
    # IMPORT CITIES
    # -----------------------------
    print(">>> Import cities...")
    for batch in chunked(cities, BATCH_SIZE):
        rows = [
            {
                "postalcodeinsee": c[0],
                "postalcode": c[1],
                "city": c[2],
                "cityinsee": c[3],
            }
            for c in batch
        ]

        with neo4j_driver.session() as session:
            session.execute_write(
                lambda tx: tx.run("""
                    UNWIND $rows AS row
                    MERGE (c:City {cityinsee: row.cityinsee})
                    SET c.name = row.city,
                        c.postalcode = row.postalcode,
                        c.postalcodeinsee = row.postalcodeinsee
                """, rows=rows)
            )

    # -----------------------------
    # IMPORT THEMES
    # -----------------------------
    print(">>> Import themes...")
    for batch in chunked(themes, BATCH_SIZE):
        rows = [{"id": t[0], "label": t[1]} for t in batch]

        with neo4j_driver.session() as session:
            session.execute_write(
                lambda tx: tx.run("""
                    UNWIND $rows AS row
                    MERGE (t:Theme {id: row.id})
                    SET t.label = row.label
                """, rows=rows)
            )

    # -----------------------------
    # IMPORT POIS
    # -----------------------------
    print(">>> Import POIs...")
    for batch in chunked(pois, BATCH_SIZE):
        rows = [
            {
                "uuid": p[0],
                "label": p[1],
                "description": p[2],
                "shortdescription": p[3],
                "uri": p[4],
                "legalname": p[5],
                "telephone": p[6],
                "email": p[7],
                "homepage": p[8],
                "lastupdate": p[9],
                "lastupdatedatatourisme": p[10],
                "lat": p[11],
                "lon": p[12],
            }
            for p in batch
        ]

        with neo4j_driver.session() as session:
            session.execute_write(
                lambda tx: tx.run("""
                    UNWIND $rows AS row
                    MERGE (p:POI {uuid: row.uuid})
                    SET p.label = row.label,
                        p.description = row.description,
                        p.shortdescription = row.shortdescription,
                        p.uri = row.uri,
                        p.legalname = row.legalname,
                        p.telephone = row.telephone,
                        p.email = row.email,
                        p.homepage = row.homepage,
                        p.lastupdate = row.lastupdate,
                        p.lastupdatedatatourisme = row.lastupdatedatatourisme,
                        p.latitude = row.lat,
                        p.longitude = row.lon
                """, rows=rows)
            )

    # -----------------------------
    # RELATION POI -> CITY
    # -----------------------------
    print(">>> Import relations POI -> City...")
    for batch in chunked(pois, BATCH_SIZE):
        rows = [{"uuid": p[0], "cityinsee": p[14]} for p in batch]

        with neo4j_driver.session() as session:
            session.execute_write(
                lambda tx: tx.run("""
                    UNWIND $rows AS row
                    MATCH (p:POI {uuid: row.uuid})
                    MATCH (c:City {cityinsee: row.cityinsee})
                    MERGE (p)-[:LOCATED_IN]->(c)
                """, rows=rows)
            )

    # -----------------------------
    # RELATION POI -> THEME
    # -----------------------------
    print(">>> Import relations POI -> Theme...")
    for batch in chunked(poi_themes, BATCH_SIZE):
        rows = [{"poi_id": pt[0], "themeid": pt[1]} for pt in batch]

        with neo4j_driver.session() as session:
            session.execute_write(
                lambda tx: tx.run("""
                    UNWIND $rows AS row
                    MATCH (p:POI {uuid: row.poi_id})
                    MATCH (t:Theme {id: row.themeid})
                    MERGE (p)-[:HAS_THEME]->(t)
                """, rows=rows)
            )

    print("[FULL] Import terminé.")



