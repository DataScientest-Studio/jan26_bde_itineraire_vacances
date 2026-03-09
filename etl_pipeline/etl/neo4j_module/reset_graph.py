from etl.neo4j_module.neo4j_connection import get_neo4j_driver

def reset_graph():
    driver = get_neo4j_driver()
    with driver.session() as session:
        print("[RESET] Suppression des relations...")
        session.run("MATCH ()-[r]->() DELETE r")

        print("[RESET] Suppression des noeuds...")
        session.run("MATCH (n) DELETE n")

    driver.close()
    print("[RESET] Neo4j vidé proprement.")
