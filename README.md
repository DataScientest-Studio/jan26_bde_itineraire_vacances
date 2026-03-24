# Itinéraire de Vacances

Ce projet est un pipeline de données conçu pour collecter, traiter et stocker des informations touristiques provenant de la source de données "datatourisme". Il utilise une architecture basée sur des conteneurs Docker pour gérer les bases de données (MongoDB, PostgreSQL) et des scripts Python pour orchestrer le flux de données.

## Prérequis

Avant de commencer, assurez-vous d'avoir installé les outils suivants sur votre machine :
*   [Docker](https://www.docker.com/get-started)
*   [Docker Compose](https://docs.docker.com/compose/install/)
*   [Python 3.9+](https://www.python.org/downloads/)

## Installation et Configuration

Suivez ces étapes pour mettre en place votre environnement de développement local.

1.  **Cloner le dépôt :**
    ```bash
    git clone <URL_DU_DEPOT>
    cd <NOM_DU_DOSSIER_PROJET>
    ```

2.  **Configurer les Variables d'Environnement :**
    Le projet utilise un fichier `.env` pour gérer les configurations sensibles (clés d'API, mots de passe, etc.).
    
    Copiez le fichier d'exemple pour créer votre propre configuration :
    ```bash
    cp .env.example .env
    ```
    Ouvrez ensuite le fichier `.env` et **modifiez les variables**, notamment en ajoutant votre propre clé d'API pour `DATA_TOURISME_API_KEY`.

3.  **Lancer les Services Docker :**
    Démarrez les conteneurs des bases de données (MongoDB, PostgreSQL) et de l'outil d'administration (pgAdmin) en arrière-plan :
    ```bash
    docker-compose up -d
    ```

4.  **Mettre en Place l'Environnement Python :**
    Il est recommandé d'utiliser un environnement virtuel pour isoler les dépendances du projet.
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
    *Sur Windows, l'activation se fait avec : `.venv\Scripts\activate`*

5.  **Installer les Dépendances Python :**
    Installez toutes les bibliothèques nécessaires listées dans `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

## Utilisation

Une fois l'installation terminée, vous pouvez utiliser les scripts pour interagir avec les données.

1.  **Ingestion des Données :**
    Pour récupérer les données de la source "datatourisme" et les stocker dans MongoDB.
    ```bash
    python -m api.scripts.ingestion.ingest_datatourisme
    ```
    > **Note :** L'API `datatourisme` limite le nombre d'appels. Lors de la première exécution complète, il est possible que le script s'interrompe. Il faudra alors attendre environ 1 heure avant de le relancer pour terminer l'ingestion, ou configurer une seconde clé d'API dans le code.

2.  **Traitement et Transfert des Données :**
    Pour traiter les données depuis MongoDB et les transférer vers PostgreSQL.
    ```bash
    python -m api.scripts.processing.mongo_to_postgres
    ```

3.  **Catégorisation des POIs (Machine Learning) :**
    Lancer la prédiction des thèmes des points d'intérêt (POIs).
    ```bash
    python -m api.scripts.ml.predict_all_pois
    ```

## Accès aux Outils

*   **pgAdmin** : Accessible via `http://localhost:5050` (ou le port que vous avez défini dans votre `.env`).
*   **MongoDB** : Accessible sur `localhost:27017` (ou le port défini).
*   **PostgreSQL** : Accessible sur `localhost:5432` (ou le port défini).

## Structure du Projet

Voici un aperçu de la structure du projet et de l'objectif de chaque dossier :

```
.
├── .github/        # Contient les workflows d'intégration continue (CI/CD).
├── data/           # Volumes des bases de données persistantes (gérés par Docker).
├── notebooks/      # Notebooks Jupyter pour l'exploration et l'analyse.
├── api/            # API
├── requirements.txt # Liste des dépendances Python.
│   ├── scripts/    # Scripts python
├──------------ ml/             # Code pour les modèles de Machine Learning.
│                ├── models/     # Modèles de ML entraînés.
│                └── train/    # Scripts pour l'entraînement et la prédiction.
│                ├── ingestion/  # Scripts pour importer les données depuis des sources externes.
│                ├── maintenance/# Scripts pour la maintenance des BDD (reset, setup).
│                ├── processing/ # Scripts pour nettoyer, transformer et transférer les données.
|                |   neo4j_db    #
│                ├── sql/        # Fichiers SQL (création de schémas de BDD).
│                └── utils/      # Fonctions utilitaires partagées.
|---streamlit       # ux
├── .env.example    # Fichier d'exemple pour les variables d'environnement.
├── .gitignore      # Fichiers et dossiers ignorés par Git.
├── docker-compose.yml # Fichier de configuration pour les services Docker.
├── LICENSE         # Licence du projet.
└── script_streamlit.py # Script pour un dashboard Streamlit.
```

#api fastapi
requirements.txt mis à jour pour fastapi
main.py dans répertoire "...\scripts\api" du repo
lancement depuis la racine du repo (là où se trouve le ".env"): "uvicorn scripts.api.main:app_iv --reload"

une fois lancée, le root de l'api est ici: http://127.0.0.1:8000
doc swagger api: http://127.0.0.1:8000/docs

token bearer associé à admin à utiliser pour authentification:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTgwMzQ3MDE4MH0.i7CqDbcbsjUYYcOxiNfFMlEWOzajP6ddWuDI-vX_pkU",
  "token_type": "bearer"
}

Quelques variables sont mises dans .env du projet.

Endpoints disponibles:
POST http://127.0.0.1:8000/token : peut être appelé par user admin pour générer un token,
GET http://127.0.0.1:8000/cities : appelé par ux pour renseigner la liste des villes dans la combo localité de l’ux.
POST http://127.0.0.1:8000/ppl_batch_1 : appelé par Airflow pour le traitement batch d’ingestion des données DATAtourisme.
POST http://127.0.0.1:8000/ppl_batch_2 : appelé par Airflow pour le traitement batch mongoDB  vers PostgreSQL.
POST http://127.0.0.1:8000/ppl_batch_3 : appelé par Airflow pour le traitement Machine Learning.
POST http://127.0.0.1:8000/ppl_batch_4 : appelé par Airflow pour le traitement batch d’ingestion des données dans Neo4j.
GET http://127.0.0.1:8000/generer-itineraire : appelé par ux avec les 3 paramètres city, days, category, renseignés par l’utilisateur de l’application pour générer et retourner un itinéraire.
Les endpoints ppl_batch_x sont de type async combiné avec la commande await pour garantir un non blocage de l’api tout en attendant la fin de traitement avant de renvoyer la réponse de l’appel du endpoint.


