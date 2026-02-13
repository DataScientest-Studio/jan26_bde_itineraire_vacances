from datetime import datetime, timedelta
from psycopg2 import extras
from scripts.utils.db_connect import get_mongo_client, get_pg_conn

def sync_data():
    collection = get_mongo_client()
    pg_conn = get_pg_conn()

    cursor = pg_conn.cursor()

    # --- ÉTAPE 1 : RÉCUPÉRATION DU WATERMARK ---
    # On cherche la date la plus récente déjà présente dans Postgres.
    cursor.execute("SELECT MAX(lastUpdateDatatourisme) FROM poi")
    # Get le premier élément de la première ligne retournée par la query
    last_sync = cursor.fetchone()[0]
    
    # Si la base est vide, on prend une date très ancienne.
    if not last_sync:
        last_sync = datetime(1900, 1, 1)
    else:
        # On recule d'un jour (la veille) pour être sûr de ne rien rater 
        # en cas de mise à jour tardive côté API. On pourrait modifier ce "days" si souci.
        last_sync = last_sync - timedelta(days=1)

    # --- ÉTAPE 2 : REQUÊTE MONGO ---
    # .isoformat() transforme un objet datetime Python en string car dans Mongo c'est stocké en String
    query = {"lastUpdateDatatourisme": {"$gt": last_sync.isoformat()}}
    
    # On trie par date pour que si le script s'arrête, on ait traité les plus anciens d'abord.
    mongo_cursor = collection.find(query).sort("lastUpdateDatatourisme", 1)#.limit(10000) #⚠️ A ENLEVER APRES LES TESTS

    # --- ÉTAPE 3 : PRÉPARATION DES BATCHS ---
    #On choisi des batchs de 1000 pour aller plus vite, et pas trop pour ne pas saturer la mémoire.
    batch_size = 1000
    poi_batch = []
    loc_batch = []
    # Accumulateur pour stocker les types du batch en cours afin de les traiter après l'insert POI
    type_accumulator = []

    #on va boucler sur chaque doc, et une fois atteint le batch_size, on envoie tout à Postgres d'un coup
    for doc in mongo_cursor:
        uuid = doc.get('uuid')
        try:

            # Extraction sécurisée des objets listes
            # Extraction sécurisée des objets listes
            descs = doc.get('hasDescription')
            contacts = doc.get('hasContact')

            # Analyse de la description
            if descs and len(descs) > 0:
                first_desc_obj = descs[0]
                
                # --- Extraction sécurisée de la description courte ---
                s_desc_val = first_desc_obj.get('shortDescription')
                # Si c'est une liste non vide, on prend le premier @fr, sinon si c'est un dict on prend le @fr, sinon None
                if isinstance(s_desc_val, list) and len(s_desc_val) > 0:
                    short_desc_fr = s_desc_val[0].get('@fr')
                elif isinstance(s_desc_val, dict):
                    short_desc_fr = s_desc_val.get('@fr')
                else:
                    short_desc_fr = None

                # --- Extraction sécurisée de la description longue ---
                l_desc_val = first_desc_obj.get('description')
                if isinstance(l_desc_val, list) and len(l_desc_val) > 0:
                    desc_fr = l_desc_val[0].get('@fr')
                elif isinstance(l_desc_val, dict):
                    desc_fr = l_desc_val.get('@fr')
                else:
                    desc_fr = None
            else:
                short_desc_fr = None
                desc_fr = None

            # doc.get('champ', {}) : si 'champ' n'existe pas, il renvoie un dictionnaire vide {}.
            # Cela évite que le code plante si une clé est absente (ex: pas de contact).
            # doc.get('champ', []) : pareil, mais pour les listes.
            # On met 'None' si la donnée est absente. En SQL, cela insérera une valeur NULL.
            
            # Préparation des données POI
            poi_batch.append((
                uuid, 
                doc.get('label', {}).get('@fr'), #existe toujours
                # Descriptions
                desc_fr,
                short_desc_fr,
                doc.get('uri'), #existe toujours
                doc.get('hasBeenCreatedBy', {}).get('legalName'),
                # Contacts (sécurité double : liste hasContact + liste interne)
                contacts[0].get('telephone', [None])[0] if contacts else None,
                contacts[0].get('email', [None])[0] if contacts else None,
                contacts[0].get('homepage', [None])[0] if contacts else None,
                doc.get('lastUpdate'), #existe toujours
                doc.get('lastUpdateDatatourisme') #existe toujours
            ))

            # Préparation des données Localisation
            loc = doc.get('isLocatedAt', [{}])[0]
            addr = loc.get('address', [{}])[0]
            # On récupère la liste des rues
            street_list = addr.get('streetAddress', [])
            # On les joint avec une virgule si la liste n'est pas vide, sinon None
            full_street = ", ".join(street_list) if street_list else None

            loc_batch.append((
                uuid,
                full_street,
                addr.get('postalCode'),
                addr.get('hasAddressCity', {}).get('insee'),
                addr.get('addressLocality'),
                addr.get('hasAddressCity', {}).get('label', {}).get('@fr'),
                loc.get('geo', {}).get('latitude'),
                loc.get('geo', {}).get('longitude')
            ))

            # --- ÉTAPE 4 : GESTION DES TYPES ---
            # On stocke les types dans l'accumulateur pour les traiter après l'envoi du batch POI
            type_accumulator.append({
                'uuid': uuid,
                'types': doc.get('type', [])
            })

            # --- ÉTAPE 5 : ENVOI DES BATCHS ---
            if len(poi_batch) >= batch_size:
                # On appelle la fonction d'orchestration pour respecter l'ordre des Foreign Keys
                execute_sequenced_batch(cursor, poi_batch, loc_batch, type_accumulator)
                pg_conn.commit() # On valide la transaction
                poi_batch, loc_batch, type_accumulator = [], [], []
                print(f"Sync : {batch_size} nouveaux documents traités.")

        except AttributeError as e:
            # Si le code plante sur un .get() ou un accès d'attribut
            print(f"\n❌ Erreur d'attribut sur le document UUID : {uuid}")
            print(f"Détail de l'erreur : {e}")
            # On affiche le contenu du champ qui pose souvent problème pour inspecter
            print(f"Contenu de descs : {descs}")
            raise e # On stoppe le script pour pouroivr analyser
            
        except Exception as e:
            # Pour toute autre erreur (IndexError, etc.)
            print(f"\n❌ Erreur inattendue sur le document UUID : {uuid}")
            print(f"Type d'erreur : {type(e).__name__}")
            raise e

    # On n'oublie pas le dernier batch incomplet
    if poi_batch:
        execute_sequenced_batch(cursor, poi_batch, loc_batch, type_accumulator)
        pg_conn.commit()

    cursor.close()
    pg_conn.close()

def execute_sequenced_batch(cursor, poi_data, loc_data, type_data):
    """Effectue l'insertion de masse en respectant l'ordre hiérarchique des tables."""
    
    # --- INSERTION TABLE POI (PARENT) ---
    # ON CONFLICT (uuid) DO UPDATE : C'est le 'Upsert'.
    # Si l'UUID existe déjà, Postgres met à jour les colonnes listées après SET.
    # EXCLUDED représente la nouvelle valeur qu'on essaye d'insérer.
    poi_query = """
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
    extras.execute_values(cursor, poi_query, poi_data)

    # --- INSERTION TABLE LOCATION (ENFANT) ---
    loc_query = """
        INSERT INTO poiLocation (uuid, streetAddress, postalCode, postalCodeInsee, city, cityInsee, latitude, longitude)
        VALUES %s
        ON CONFLICT (uuid) DO UPDATE SET
            streetAddress = EXCLUDED.streetAddress,
            postalCode = EXCLUDED.postalCode,
            postalCodeInsee = EXCLUDED.postalCodeInsee,
            city = EXCLUDED.city,
            cityInsee = EXCLUDED.cityInsee,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude;
    """
    extras.execute_values(cursor, loc_query, loc_data)

    # --- GESTION DES TYPES (ENFANT) ---
    for item in type_data:
        uuid = item['uuid']
        # On supprime les anciens types de ce POI pour les remplacer par les nouveaux.
        # Le (uuid,) avec une virgule crée un 'tuple' à un seul élément (requis par psycopg2).
        cursor.execute("DELETE FROM poiType WHERE uuid = %s", (uuid,))
        
        for t_label in item['types']:
            # ON CONFLICT sur typeRef : si le type existe déjà, on ne fait rien (DO NOTHING),
            # mais on récupère quand même l'ID existant grâce au RETURNING.
            # Note : On utilise DO UPDATE SET pour forcer le RETURNING même si le libellé existe.
            cursor.execute("""
                INSERT INTO type (typeLabel) VALUES (%s) 
                ON CONFLICT (typeLabel) DO UPDATE SET typeLabel = EXCLUDED.typeLabel
                RETURNING typeId;
            """, (t_label,))
            t_id = cursor.fetchone()[0]
            
            # On lie le POI à son type
            #On ajoute quand même un "on conflit" au car où dans le même document on ait plusieurs fois le m^me type.
            cursor.execute("INSERT INTO poiType (uuid, typeId) VALUES (%s, %s) ON CONFLICT DO NOTHING", (uuid, t_id))

if __name__ == "__main__":
    sync_data()