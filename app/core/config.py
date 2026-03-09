from pydantic import BaseSettings

class Settings(BaseSettings):
    # PostgreSQL
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    # MongoDB
    MONGO_HOST: str
    MONGO_PORT: int
    MONGO_DB: str

    # Neo4j
    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str

    class Config:
        env_file = ".env.local"  # ou .env.docker selon ton contexte

settings = Settings()
