from etl.postgres_module.pg_connection import get_pg_conn
from etl.utils.state_manager import load_last_import_timestamp


def get_delta_pois():
    """
    Retourne les POI modifiés depuis le dernier import,
    avec localisation, ville et thème.
    """
    last_ts = load_last_import_timestamp()
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
            c.postalcodeinsee AS postalcodeinsee,
            t.id AS theme_id,
            t.label AS theme_label
        FROM poi p
        JOIN poilocation l ON p.uuid = l.uuid
        JOIN city c ON l.postalcodeinsee = c.postalcodeinsee
        JOIN poitheme pt ON p.uuid = pt.uuid
        JOIN theme t ON pt.themeid = t.id
        WHERE p.lastupdate > %s;
    """

    with conn.cursor() as cur:
        cur.execute(query, (last_ts,))
        return cur.fetchall()


def get_delta_cities():
    """
    Pas de delta city : la table city n’a pas de colonnes de mise à jour.
    On retourne toujours une liste vide.
    """
    return []


def get_delta_themes():
    """
    Pas de delta theme : la table theme n’a pas de colonnes de mise à jour.
    On retourne toujours une liste vide.
    """
    return []


def get_delta_poi_themes():
    """
    Pas de delta poitheme : la table poitheme n’a pas de colonnes de mise à jour.
    On retourne toujours une liste vide.
    """
    return []


