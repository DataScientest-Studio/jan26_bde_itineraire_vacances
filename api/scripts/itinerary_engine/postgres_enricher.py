from psycopg2.extras import RealDictCursor
from scripts.utils.db_connect import get_pg_conn

def enrich_pois_with_postgres(poi_ids):
    if not poi_ids:
        return {}

    conn = get_pg_conn()
    
    # On utilise ANY() pour interroger tous les UUIDs nécessaires en un seul aller-retour
    query = """
        SELECT 
            p.uuid, 
            p.shortdescription, 
            p.telephone, 
            p.homepage,
            l.streetaddress
        FROM poi p
        LEFT JOIN poilocation l ON p.uuid = l.uuid
        WHERE p.uuid = ANY(%s::uuid[])
    """
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (poi_ids,))
        rows = cur.fetchall()
        
    conn.close()
    
    # Retourne un dictionnaire {uuid: {données}} pour une injection ultra-rapide (O(1))
    return {
        row["uuid"]: {
            "description": row["shortdescription"],
            "telephone": row["telephone"],
            "website": row["homepage"],
            "address": row["streetaddress"]
        }
        for row in rows
    }