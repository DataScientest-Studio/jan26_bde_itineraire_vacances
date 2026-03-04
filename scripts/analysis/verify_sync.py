from scripts.utils.db_connect import get_mongo_client, get_pg_conn

def verify_integrity():
    mongo_col = get_mongo_client()
    pg_conn = get_pg_conn()
    pg_cur = pg_conn.cursor()

    print("🔍 Démarrage de la vérification des données...\n")

    # --- 1. VÉRIFICATION DU NOMBRE TOTAL ---
    mongo_count = mongo_col.count_documents({})
    pg_cur.execute("SELECT COUNT(*) FROM poi")
    pg_count = pg_cur.fetchone()[0]

    print(f"📊 VOLUMÉTRIE :")
    print(f"   - MongoDB  : {mongo_count} documents")
    print(f"   - Postgres : {pg_count} lignes")
    
    if mongo_count == pg_count:
        print("   ✅ Le nombre de POI correspond parfaitement.")
    else:
        print(f"   ❌ Écart détecté ! Différence : {abs(mongo_count - pg_count)}")

    # --- 2. VÉRIFICATION DE LA COHÉRENCE DES TYPES (Échantillon) ---
    # On prend 5 POI au hasard pour une vérification granulaire
    print(f"\n🧪 VÉRIFICATION GRANULAIRE (Types) sur un échantillon :")
    
    # On récupère 5 UUIDs aléatoires dans Postgres
    pg_cur.execute("SELECT uuid FROM poi ORDER BY RANDOM() LIMIT 50")
    sample_uuids = [str(row[0]) for row in pg_cur.fetchall()]

    for uuid in sample_uuids:
        # Récupération dans Mongo
        mongo_doc = mongo_col.find_one({"uuid": uuid})
        mongo_types = sorted(mongo_doc.get('type', [])) if mongo_doc else []

        # Récupération dans Postgres (via la table de jointure)
        pg_cur.execute("""
            SELECT t.typeLabel 
            FROM type t
            JOIN poiType pt ON t.typeId = pt.typeId
            WHERE pt.uuid = %s
        """, (uuid,))
        pg_types = sorted([row[0] for row in pg_cur.fetchall()])

        if mongo_types == pg_types:
            print(f"   ✅ POI {uuid[:8]}... : Types identiques ({len(pg_types)})")
        else:
            print(f"   ❌ POI {uuid[:8]}... : ERREUR DE TYPES !")
            print(f"      Mongo    : {mongo_types}")
            print(f"      Postgres : {pg_types}")

    # --- 3. VÉRIFICATION DES LOCALISATIONS ORPHELINES ---
    pg_cur.execute("""
        SELECT COUNT(*) FROM poi p 
        LEFT JOIN poiLocation l ON p.uuid = l.uuid 
        WHERE l.uuid IS NULL
    """)
    orphans = pg_cur.fetchone()[0]
    
    print(f"\n📍 VÉRIFICATION LOCALISATION :")
    if orphans == 0:
        print("   ✅ Tous les POI ont une entrée dans poiLocation.")
    else:
        print(f"   ⚠️  Attention : {orphans} POI n'ont pas de coordonnées GPS.")

    pg_cur.close()
    pg_conn.close()

if __name__ == "__main__":
    verify_integrity()