from scripts.utils.db_connect import get_pg_conn

def setup_tables():
    conn = get_pg_conn()
    cursor = conn.cursor()
    
    try:
        # Lire le fichier SQL
        with open('scripts/sql/create_tables.sql', 'r') as f:
            sql_script = f.read()
        
        print("🏗️  Création des tables en cours...")
        cursor.execute(sql_script)
        conn.commit()
        print("✅ Tables créées avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création : {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    setup_tables()