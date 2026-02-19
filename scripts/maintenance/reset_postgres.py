from scripts.utils.db_connect import get_pg_conn

def reset_postgres():
    print("⚠️  AVERTISSEMENT : Vous allez supprimer toutes les données de PostgreSQL.")
    confirm = input("Voulez-vous continuer ? (oui/non) : ")
    
    if confirm.lower() != 'oui':
        print("❌ Opération annulée.")
        return

    conn = get_pg_conn()
    conn.autocommit = True # Nécessaire pour certaines opérations de schéma
    cursor = conn.cursor()

    try:
        print("🧹 Nettoyage du schéma public...")
        # Suppression et recréation du schéma public pour raser toutes les tables d'un coup
        cursor.execute("DROP SCHEMA public CASCADE;")
        cursor.execute("CREATE SCHEMA public;")
        cursor.execute("GRANT ALL ON SCHEMA public TO public;")
        
        print("✨ PostgreSQL est maintenant vide et prêt pour une nouvelle installation.")
        
    except Exception as e:
        print(f"❌ Erreur lors du reset : {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    reset_postgres()