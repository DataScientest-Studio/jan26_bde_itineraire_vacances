from datetime import datetime, timedelta
import psycopg2.extras
from scripts.utils.db_connect import get_pg_conn_api, get_neo4j_driver
import os

print(f"ingestion_neo4j STARTED - PID: {os.getpid()}")

BATCH_SIZE = 10000

def setup_database(driver):
    print(">>> [INIT] Vérification des contraintes d'unicité Neo4j...")
    # On force l'unicité sur postalcodeinsee pour les villes
    queries = [
        "CREATE CONSTRAINT poi_uuid IF NOT EXISTS FOR (p:POI) REQUIRE p.uuid IS UNIQUE",
        "CREATE CONSTRAINT city_postalcodeinsee IF NOT EXISTS FOR (c:City) REQUIRE c.postalcodeinsee IS UNIQUE",
        "CREATE CONSTRAINT theme_id IF NOT EXISTS FOR (t:Theme) REQUIRE t.themeid IS UNIQUE"
    ]
    with driver.session() as session:
        for q in queries:
            session.run(q)

def chunked(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]

def run_delta_import():
    pg_conn = get_pg_conn_api()
    neo4j_driver = get_neo4j_driver()
    try:
        setup_database(neo4j_driver)
        # --- 1. HWM (High Water Mark) ---
        with neo4j_driver.session() as session:
            # On récupère les postalcodeinsee existants
            existing_cities = {r["id"] for r in session.run("MATCH (c:City) RETURN c.postalcodeinsee as id")}
            existing_themes = {r["id"] for r in session.run("MATCH (t:Theme) RETURN t.themeid as id")}
            
            res_ts = session.run("MATCH (p:POI) RETURN max(p.lastupdate) as last_ts").single()
            if res_ts and res_ts["last_ts"]:
                val = res_ts["last_ts"]
                if hasattr(val, "to_native"):
                    last_dt = datetime.fromordinal(val.to_ordinal())
                elif isinstance(val, str):
                    last_dt = datetime.fromisoformat(val.replace("Z", ""))
                else:
                    last_dt = val
                start_date = last_dt - timedelta(days=1)
            else:
                start_date = datetime(1900, 1, 1)

        # --- 2. RÉFÉRENTIELS (Nouveautés uniquement) ---
        with pg_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Dédoublonnage sur postalcodeinsee côté Postgres
            cur.execute("""
                SELECT DISTINCT ON (postalcodeinsee) postalcodeinsee, postalcode, city, cityinsee 
                FROM city 
                ORDER BY postalcodeinsee;
            """)
            new_cities = [dict(c) for c in cur.fetchall() if c['postalcodeinsee'] not in existing_cities]
            
            cur.execute("SELECT themeid, themelabel FROM theme")
            new_themes = [dict(t) for t in cur.fetchall() if t['themeid'] not in existing_themes]

        with neo4j_driver.session() as session:
            if new_cities:
                print(f">>> [REF] Ajout de {len(new_cities)} nouvelles villes.")
                session.execute_write(lambda tx: tx.run("""
                    UNWIND $rows AS row
                    MERGE (c:City {postalcodeinsee: row.postalcodeinsee})
                    SET c.name = row.city, c.postalcode = row.postalcode, c.cityinsee = row.cityinsee
                """, rows=new_cities))

            if new_themes:
                print(f">>> [REF] Ajout de {len(new_themes)} nouveaux thèmes.")
                session.execute_write(lambda tx: tx.run("""
                    UNWIND $rows AS row
                    MERGE (t:Theme {themeid: row.themeid})
                    SET t.label = row.themelabel
                """, rows=new_themes))

        # --- 3. EXTRACTION DÉDOUBLONNÉE DES POIS ---
        with pg_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # On récupère explicitement c.postalcodeinsee pour le lien
            cur.execute("""
                WITH deduplicated_pois AS (
                    SELECT 
                        p.uuid, p.label, p.lastupdate, p.lastupdatedatatourisme,
                        l.latitude, l.longitude, c.postalcodeinsee, t.themeid,
                        ROW_NUMBER() OVER(PARTITION BY p.uuid ORDER BY p.lastupdate DESC, c.postalcodeinsee ASC) as rn
                    FROM poi p
                    LEFT JOIN poilocation l ON p.uuid = l.uuid
                    LEFT JOIN city c ON l.postalcodeinsee = c.postalcodeinsee
                    LEFT JOIN poitheme pt ON p.uuid = pt.uuid
                    LEFT JOIN theme t ON pt.themeid = t.themeid
                    WHERE p.lastupdate > %s
                )
                SELECT * FROM deduplicated_pois 
                WHERE rn = 1
                ORDER BY lastupdate ASC;
            """, (start_date,))
            updated_pois = cur.fetchall()

        total_pois = len(updated_pois)
        if total_pois == 0:
            print("[DELTA] Aucun POI à mettre à jour.")
            return

        print(f">>> [INGESTION] {total_pois} POIs à traiter par lots de {BATCH_SIZE}...")

        rows_to_insert = [{
            "uuid": p['uuid'],
            "label": p['label'],
            "lastupdate": p['lastupdate'].isoformat() if p['lastupdate'] else None,
            "lastupdatedatatourisme": p['lastupdatedatatourisme'],
            "lat": p['latitude'],
            "lon": p['longitude'],
            "postalcodeinsee": p['postalcodeinsee'],
            "themeid": p['themeid']
        } for p in updated_pois]

        # --- 4. INGESTION MASSIVE ---
        cypher_query = """
        UNWIND $rows AS row
        
        MERGE (p:POI {uuid: row.uuid})
        SET p.label = row.label,
            p.lastupdate = row.lastupdate,
            p.lastupdatedatatourisme = row.lastupdatedatatourisme,
            p.latitude = row.lat,
            p.longitude = row.lon
            
        FOREACH (_ IN CASE WHEN row.postalcodeinsee IS NOT NULL THEN [1] ELSE [] END |
            MERGE (c:City {postalcodeinsee: row.postalcodeinsee})
            MERGE (p)-[:LOCATED_IN]->(c)
        )
        
        FOREACH (_ IN CASE WHEN row.themeid IS NOT NULL THEN [1] ELSE [] END |
            MERGE (t:Theme {themeid: row.themeid})
            MERGE (p)-[:HAS_THEME]->(t)
        )
        """

        with neo4j_driver.session() as session:
            for i, batch in enumerate(chunked(rows_to_insert, BATCH_SIZE)):
                session.execute_write(lambda tx: tx.run(cypher_query, rows=batch))
                print(f"    - Batch {i + 1}/{(total_pois // BATCH_SIZE) + 1} inséré.", end="\r")
        
        print("\n[DELTA] Terminé avec succès.")

    finally:
        pg_conn.close()
        neo4j_driver.close()

if __name__ == "__main__":
    run_delta_import()