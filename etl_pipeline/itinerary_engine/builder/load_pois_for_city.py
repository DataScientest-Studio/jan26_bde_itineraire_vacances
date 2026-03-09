import psycopg2
from psycopg2.extras import RealDictCursor
from neo4j_module.config import POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD


def load_pois_for_city(city, theme):
    """
    Charge les POIs depuis Postgres pour une ville et un thème donné.
    Retourne une liste de dicts :
    {
        "poi_id": "...",
        "label": "...",
        "lat": ...,
        "lon": ...,
        "themes": [...]
    }
    """

    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )

    query = """
        SELECT poi_id, label, lat, lon, themes
        FROM pois
        WHERE LOWER(city) = LOWER(%s)
        AND %s = ANY(themes)
        ORDER BY poi_id;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (city, theme))
        rows = cur.fetchall()

    conn.close()

    # Normalisation du format pour le builder
    pois = []
    for row in rows:
        pois.append({
            "poi_id": row["poi_id"],
            "label": row["label"],
            "lat": float(row["lat"]),
            "lon": float(row["lon"]),
            "themes": row["themes"] if isinstance(row["themes"], list) else [row["themes"]]
        })

    return pois
