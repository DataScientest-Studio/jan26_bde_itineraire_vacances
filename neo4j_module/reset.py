from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Nassima94!!"  


class Neo4jReset:

    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def wipe_database(self):
        with self.driver.session() as session:
            print("Suppression de tous les nœuds et relations...")
            session.run("MATCH (n) DETACH DELETE n")
            print("Base vidée.")

    def run_file_statements(self, filepath):
        """
        Exécute chaque statement séparément (Neo4j 5 n'accepte pas les blocs multiples).
        """
        print(f"Chargement de {filepath}...")
        with open(filepath, "r") as f:
            content = f.read()

        # Séparer les statements par ';'
        statements = [stmt.strip() for stmt in content.split(";") if stmt.strip()]

        with self.driver.session() as session:
            for stmt in statements:
                print(f"Exécution : {stmt[:60]}...")
                session.run(stmt)

    def reload_constraints(self):
        self.run_file_statements("neo4j_module/schema/constraints.cypher")
        print("Contraintes rechargées.")

    def reload_indexes(self):
        self.run_file_statements("neo4j_module/schema/indexes.cypher")
        print("Index rechargés.")


if __name__ == "__main__":
    reset = Neo4jReset()

    print("\n=== RESET NEO4J ===\n")

    reset.wipe_database()
    reset.reload_constraints()
    reset.reload_indexes()

    reset.close()

    print("\nRéinitialisation terminée.\n")
