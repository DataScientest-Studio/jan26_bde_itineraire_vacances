from scripts.utils.db_connect import get_neo4j_driver

def reset_graph():
    driver = get_neo4j_driver()
    
    # Pour utiliser les transactions manuelles, on doit spécifier la base de données 
    # (ou utiliser une configuration de session basique si on est sur la base par défaut)
    with driver.session() as session:
        print("[RESET] Suppression du graphe par lots de 10 000...")
        
        # La requête Cypher gère le batching toute seule
        query = """
        MATCH (n)
        CALL {
            WITH n
            DETACH DELETE n
        } IN TRANSACTIONS OF 10000 ROWS
        """
        
        session.run(query)

    driver.close()
    print("[RESET] Neo4j vidé proprement (RAM préservée).")

if __name__ == "__main__":
    reset_graph()