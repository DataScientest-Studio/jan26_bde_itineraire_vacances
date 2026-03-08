from datetime import datetime, timedelta
from psycopg2 import extras
from ..utils.db_connect import get_mongo_client, get_pg_conn

# --- MÉMOIRE CACHE GLOBALE ---
# Utilisé pour ne pas solliciter Postgres sur les types déjà connus
TYPE_CACHE = {} 

def get_watermark(cursor):
    """Récupère la date de la dernière mise à jour dans PostgreSQL."""
    cursor.execute("SELECT MAX(lastUpdateDatatourisme) FROM poi")
    last_sync = cursor.fetchone()[0]
    
    if not last_sync:
        return datetime(1900, 1, 1)
    return last_sync - timedelta(days=1)

def extract_descriptions(doc):
    """Extrait proprement les descriptions (courte et longue) depuis le document."""
    descs = doc.get('hasDescription')
    if not descs or len(descs) == 0:
        return None, None

    first_desc_obj = descs[0]
    
    # Description Courte
    s_desc_val = first_desc_obj.get('shortDescription')
    if isinstance(s_desc_val, list) and len(s_desc_val) > 0:
        short_desc_fr = s_desc_val[0].get('@fr')
    elif isinstance(s_desc_val, dict):
        short_desc_fr = s_desc_val.get('@fr')
    else:
        short_desc_fr = None

    # Description Longue
    l_desc_val = first_desc_obj.get('description')
    if isinstance(l_desc_val, list) and len(l_desc_val) > 0:
        desc_fr = l_desc_val[0].get('@fr')
    elif isinstance(l_desc_val, dict):
        desc_fr = l_desc_val.get('@fr')
    else:
        desc_fr = None

    return short_desc_fr, desc_fr

def extract_contacts(doc):
    """Extrait le téléphone, l'email et le site web."""
    contacts = doc.get('hasContact')
    if not contacts:
        return None, None, None
        
    telephone = contacts[0].get('telephone', [None])[0]
    email = contacts[0].get('email', [None])[0]
    homepage = contacts[0].get('homepage', [None])[0]
    
    return telephone, email, homepage

def get_or_create_type_id(cursor, type_label):
    """
    Vérifie si le type existe dans le cache ou en base.
    Le crée proprement (sans sauter d'ID) s'il n'existe pas.
    """
    # 1. Vérification dans le cache Python (très rapide)
    if type_label in TYPE_CACHE:
        return TYPE_CACHE[type_label]
        
    # 2. Vérification en base (si un autre run a créé le type)
    cursor.execute("SELECT typeId FROM type WHERE typeLabel = %s", (type_label,))
    result = cursor.fetchone()
    
    if result:
        t_id = result[0]
    else:
        # 3. Création "douce" sans ON CONFLICT pour préserver la séquence
        cursor.execute(
            "INSERT INTO type (typeLabel) VALUES (%s) RETURNING typeId;", 
            (type_label,)
        )
        t_id = cursor.fetchone()[0]
        
    # 4. Ajout au cache pour la prochaine fois
    TYPE_CACHE[type_label] = t_id
    return t_id

def insert_cities(cursor, city_data):
    """Insère un lot de villes avec dédoublonnage."""
    if not city_data:
        return
        
    query = """
        INSERT INTO city (postalCodeInsee, postalCode, city, cityInsee)
        VALUES %s
        ON CONFLICT (postalCodeInsee) DO NOTHING;
    """
    extras.execute_values(cursor, query, list(city_data.values()))

def insert_pois(cursor, poi_data):
    """Insère un lot de POI (Upsert)."""
    if not poi_data:
        return
        
    query = """
        INSERT INTO poi (uuid, label, description, shortDescription, uri, legalName, telephone, email, homepage, lastUpdate, lastUpdateDatatourisme)
        VALUES %s
        ON CONFLICT (uuid) DO UPDATE SET
            label = EXCLUDED.label,
            description = EXCLUDED.description,
            shortDescription = EXCLUDED.shortDescription,
            uri = EXCLUDED.uri,
            legalName = EXCLUDED.legalName,
            telephone = EXCLUDED.telephone,
            email = EXCLUDED.email,
            homepage = EXCLUDED.homepage,
            lastUpdate = EXCLUDED.lastUpdate,
            lastUpdateDatatourisme = EXCLUDED.lastUpdateDatatourisme;
    """
    extras.execute_values(cursor, query, poi_data)

def insert_locations(cursor, loc_data):
    """Insère un lot de localisations (Upsert)."""
    if not loc_data:
        return
        
    query = """
        INSERT INTO poiLocation (uuid, streetAddress, postalCodeInsee, latitude, longitude)
        VALUES %s
        ON CONFLICT (uuid) DO UPDATE SET
            streetAddress = EXCLUDED.streetAddress,
            postalCodeInsee = EXCLUDED.postalCodeInsee,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude;
    """
    extras.execute_values(cursor, query, loc_data)

def insert_poi_types(cursor, type_data):
    """Insère les liens entre POI et Types."""
    if not type_data:
        return
        
    # On vide les anciens types pour tous les UUID du batch en une seule requête (plus rapide)
    uuids = tuple(item['uuid'] for item in type_data)
    if uuids:
        cursor.execute("DELETE FROM poiType WHERE uuid IN %s", (uuids,))

    # On prépare la liste des relations (uuid, typeId)
    relations_to_insert = []
    for item in type_data:
        uuid = item['uuid']
        for t_label in item['types']:
            t_id = get_or_create_type_id(cursor, t_label)
            relations_to_insert.append((uuid, t_id))

    # Insertion de masse des relations
    if relations_to_insert:
        query = """
            INSERT INTO poiType (uuid, typeId) 
            VALUES %s 
            ON CONFLICT DO NOTHING;
        """
        extras.execute_values(cursor, query, relations_to_insert)

def process_batch(cursor, pg_conn, city_batch, poi_batch, loc_batch, type_batch):
    """Orchestre l'insertion d'un batch entier dans le bon ordre."""
    insert_cities(cursor, city_batch)
    insert_pois(cursor, poi_batch)
    insert_locations(cursor, loc_batch)
    insert_poi_types(cursor, type_batch)
    
    pg_conn.commit()

def sync_data():
    collection = get_mongo_client()
    pg_conn = get_pg_conn()
    cursor = pg_conn.cursor()

    # 1. Setup
    last_sync = get_watermark(cursor)
    query = {"lastUpdateDatatourisme": {"$gt": last_sync.isoformat()}}
    
    total_docs = collection.count_documents(query)
    print(f"🔄 Synchronisation : {total_docs} documents depuis {last_sync.date()}")

    mongo_cursor = collection.find(query).sort("lastUpdateDatatourisme", 1)

    # 2. Variables de Batch
    batch_size = 1000
    poi_batch, loc_batch, type_batch = [], [], []
    city_batch = {}
    
    processed_count = 0

    # 3. Boucle Principale
    for doc in mongo_cursor:
        uuid = doc.get('uuid')
        try:
            short_desc, long_desc = extract_descriptions(doc)
            telephone, email, homepage = extract_contacts(doc)

            # --- POI Data ---
            poi_batch.append((
                uuid, 
                doc.get('label', {}).get('@fr'),
                long_desc, short_desc,
                doc.get('uri'),
                doc.get('hasBeenCreatedBy', {}).get('legalName'),
                telephone, email, homepage,
                doc.get('lastUpdate'),
                doc.get('lastUpdateDatatourisme')
            ))

            # --- Location Data ---
            loc = doc.get('isLocatedAt', [{}])[0]
            addr = loc.get('address', [{}])[0]
            city_insee = addr.get('hasAddressCity', {}).get('insee')

            if city_insee:
                city_batch[city_insee] = (
                    city_insee,
                    addr.get('postalCode'),
                    addr.get('addressLocality'),
                    addr.get('hasAddressCity', {}).get('label', {}).get('@fr')
                )

            street_list = addr.get('streetAddress', [])
            full_street = ", ".join(street_list) if street_list else None

            loc_batch.append((
                uuid, full_street, city_insee,
                loc.get('geo', {}).get('latitude'),
                loc.get('geo', {}).get('longitude')
            ))

            # --- Type Data ---
            type_batch.append({
                'uuid': uuid,
                'types': doc.get('type', [])
            })

            # --- Flush Batch ---
            processed_count += 1
            if len(poi_batch) >= batch_size:
                process_batch(cursor, pg_conn, city_batch, poi_batch, loc_batch, type_batch)
                print(f"✅ {processed_count} / {total_docs} traités...")
                poi_batch, loc_batch, type_batch, city_batch = [], [], [], {}

        except Exception as e:
            print(f"\n❌ Erreur sur UUID : {uuid} -> {e}")
            raise e

    # Flush du dernier batch
    if poi_batch:
        process_batch(cursor, pg_conn, city_batch, poi_batch, loc_batch, type_batch)
        print(f"✅ {processed_count} / {total_docs} traités...")

    cursor.close()
    pg_conn.close()

if __name__ == "__main__":
    sync_data()