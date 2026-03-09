import os
from dotenv import load_dotenv

# Charge le .env local du module
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

# Variables internes du builder
BUILDER_LOG_LEVEL = os.getenv("BUILDER_LOG_LEVEL", "INFO")
BUILDER_ENV = os.getenv("BUILDER_ENV", "production")
