from etl.postgres_module.pg_connection import get_pg_conn

def get_all_pois():
    conn = get_pg_conn()
    query = """
        SELECT 
            p.uuid AS poi_id,
            p.label AS label,
            p.description AS description,
            p.shortdescription AS shortdescription,
            p.uri AS uri,
            p.legalname AS legalname,
            p.telephone AS telephone,
            p.email AS email,
            p.homepage AS homepage,
            p.lastupdate AS lastupdate,
            p.lastupdatedatatourisme AS lastupdatedatatourisme,
            l.latitude AS lat,
            l.longitude AS lon,
            c.city AS city,
            c.cityinsee AS cityinsee,
            c.postalcode AS postalcode,
            c.postalcodeinsee AS postalcodeinsee
        FROM poi p
        JOIN poilocation l ON p.uuid = l.uuid
        JOIN city c ON l.postalcodeinsee = c.postalcodeinsee
        JOIN poitheme pt ON p.uuid = pt.uuid;
    """
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


def get_all_cities():
    conn = get_pg_conn()
    query = """
        SELECT 
            postalcodeinsee,
            postalcode,
            city,
            cityinsee
        FROM city;
    """
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


def get_all_themes():
    conn = get_pg_conn()
    query = """
        SELECT 
            themeid AS theme_id,
            themelabel AS theme_label
        FROM theme;
    """
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


def get_all_poi_themes():
    conn = get_pg_conn()
    query = """
        SELECT 
            uuid AS poi_id,
            themeid
        FROM poitheme;
    """
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()
