from scripts.utils.db_connect import get_pg_conn_api

def load_pois_for_city(postalcodeinsee: str, themeid: int):
    """
    Charge les POIs depuis Postgres :
    - poi
    - poitheme
    - theme
    - poilocation
    - city
    """
    conn = get_pg_conn_api()
    cur = conn.cursor()

    query = """
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
            pl.latitude,
            pl.longitude,
            t.themeid,
            c.postalcodeinsee
        FROM poi p
        JOIN poitheme pt ON pt.uuid = p.uuid
        JOIN theme t ON t.themeid = pt.themeid
        JOIN poilocation pl ON pl.uuid = p.uuid
        JOIN city c ON c.postalcodeinsee = pl.postalcodeinsee
        WHERE c.postalcodeinsee = %s
          AND t.themeid = %s
    """

    cur.execute(query, (postalcodeinsee, themeid))
    rows = cur.fetchall()

    cur.close()
    conn.close()

    pois = []
    for r in rows:
        pois.append({
            "uuid": r[0],
            "label": r[1],
            "description": r[2],
            "shortdescription": r[3],
            "uri": r[4],
            "legalname": r[5],
            "telephone": r[6],
            "email": r[7],
            "homepage": r[8],
            "lastupdate": r[9],
            "lastupdatedatatourisme": r[10],
            "latitude": float(r[11]) if r[11] is not None else None,
            "longitude": float(r[12]) if r[12] is not None else None,
            "themeid": r[13],
            "postalcodeinsee": r[14],
        })

    print(f"[DEBUG Postgres] {len(pois)} POIs chargés depuis Postgres")
    return pois
