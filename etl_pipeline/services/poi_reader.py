from psycopg2.extras import RealDictCursor
from etl.postgres_module.pg_connection import get_pg_conn


def get_pois_for_city(city: str):
    """
    Récupère tous les POI d'une ville depuis PostgreSQL,
    avec localisation et thème.
    """
    conn = get_pg_conn()

    query = """
        SELECT 
            p.uuid AS poi_id,
            p.label AS label,
            p.description AS description,
            p.shortdescription AS shortdescription,
            l.latitude AS lat,
            l.longitude AS lon,
            c.city AS city,
            t.id AS theme_id,
            t.label AS theme_label
        FROM poi p
        JOIN poilocation l ON p.uuid = l.uuid
        JOIN city c ON l.postalcodeinsee = c.postalcodeinsee
        JOIN poitheme pt ON p.uuid = pt.uuid
        JOIN theme t ON pt.themeid = t.id
        WHERE c.city = %s;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (city,))
        rows = cur.fetchall()

    conn.close()
    return rows


def get_themes():
    conn = get_pg_conn()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT id AS theme_id, label AS theme_label FROM theme;")
        rows = cur.fetchall()
    conn.close()
    return rows


def get_poi_themes(city: str):
    conn = get_pg_conn()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT pt.uuid AS poi_id, pt.themeid AS theme_id
            FROM poitheme pt
            JOIN poi p ON p.uuid = pt.uuid
            JOIN poilocation l ON p.uuid = l.uuid
            JOIN city c ON l.postalcodeinsee = c.postalcodeinsee
            WHERE c.city = %s;
        """, (city,))
        rows = cur.fetchall()
    conn.close()
    return rows


def get_all_cities():
    conn = get_pg_conn()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT DISTINCT city FROM city ORDER BY city;")
        rows = cur.fetchall()
    conn.close()
    return [r["city"] for r in rows]

