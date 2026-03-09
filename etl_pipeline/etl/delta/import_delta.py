import os
from datetime import datetime
from etl.neo4j_module.neo4j_connection import get_neo4j_driver
from etl.postgres_module.pg_connection import get_pg_conn
from etl.utils.state_manager import load_last_import_timestamp, save_last_import_timestamp


def run_delta_import():
    """
    Import DELTA : POIs modifiés, localisation, relations City et Theme.
    Pas de distances, pas de builder.
    """

    last_import_ts = load_last_import_timestamp()
    print(f"[DELTA] Dernier import : {last_import_ts.isoformat()}")

    pg_conn = get_pg_conn()
    neo4j_driver = get_neo4j_driver()

    try:
        # --- DELTA POIS (basé sur lastupdate) ---
        with pg_conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    p.uuid,
                    p.label,
                    p.description,
                    p.shortdescription,
                    p.uri,
                    p.legalname,
                    p.telephone,
                    p.email,
                    p.homepage,
                    p.lastupdate,
                    p.lastupdatedatatourisme,
                    l.latitude,
                    l.longitude,
                    c.city AS city_name,
                    c.cityinsee,
                    c.postalcode,
                    c.postalcodeinsee,
                    t.id AS theme_id,
                    t.label AS theme_label
                FROM poi p
                JOIN poilocation l ON p.uuid = l.uuid
                JOIN city c ON l.postalcodeinsee = c.postalcodeinsee
                JOIN poitheme pt ON p.uuid = pt.uuid
                JOIN theme t ON pt.themeid = t.id
                WHERE p.lastupdate > %s;
            """, (last_import_ts,))
            updated_pois = cur.fetchall()

        print(f"[DELTA] {len(updated_pois)} POIs modifiés.")

        if not updated_pois:
            print("[DELTA] Aucun POI modifié. Fin.")
            return

        with neo4j_driver.session() as session:

            # --- UPDATE POI ---
            session.run("""
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
            """, rows=[
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
                for p in updated_pois
            ])

            # --- UPDATE RELATION POI -> CITY ---
            session.run("""
            UNWIND $rows AS row
            MATCH (p:POI {uuid: row.uuid})
            MATCH (c:City {cityinsee: row.cityinsee})
            MERGE (p)-[:LOCATED_IN]->(c)
            """, rows=[
                {"uuid": p[0], "cityinsee": p[14]}
                for p in updated_pois
            ])

            # --- UPDATE RELATION POI -> THEME ---
            session.run("""
            UNWIND $rows AS row
            MATCH (p:POI {uuid: row.uuid})
            MATCH (t:Theme {id: row.theme_id})
            MERGE (p)-[:HAS_THEME]->(t)
            """, rows=[
                {"uuid": p[0], "theme_id": p[16]}
                for p in updated_pois
            ])

        # --- UPDATE TIMESTAMP ---
        now = datetime.utcnow()
        save_last_import_timestamp(now)
        print(f"[DELTA] Import terminé. Nouveau timestamp : {now.isoformat()}")

    finally:
        pg_conn.close()
        neo4j_driver.close()
