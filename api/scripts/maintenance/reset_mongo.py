from ..utils.db_connect import get_mongo_client

def reset_mongo():
    print("⚠️  AVERTISSEMENT : Vous allez supprimer TOUTES les bases de données (hors système) de MongoDB.")
    confirm = input("Voulez-vous continuer ? (oui/non) : ")
    
    if confirm.lower() != 'oui':
        print("❌ Opération annulée.")
        return

    # On récupère le client via ta fonction utilitaire
    client = get_mongo_client().client 
    
    # Liste des bases système à ne JAMAIS supprimer
    protected_dbs = ['admin', 'config', 'local']

    try:
        print("🧹 Analyse des bases de données MongoDB...")
        # Récupérer toutes les bases existantes
        db_names = client.list_database_names()
        
        deleted_count = 0
        for db_name in db_names:
            if db_name not in protected_dbs:
                print(f"🗑️  Suppression de la base : {db_name}...")
                client.drop_database(db_name)
                deleted_count += 1
            else:
                print(f"🛡️  Base système préservée : {db_name}")

        if deleted_count > 0:
            print(f"\n✨ Nettoyage terminé. {deleted_count} base(s) supprimée(s). MongoDB est propre.")
        else:
            print("\n✅ Aucune base utilisateur à supprimer.")

    except Exception as e:
        print(f"❌ Erreur lors du reset MongoDB : {e}")
    finally:
        client.close()

if __name__ == "__main__":
    reset_mongo()