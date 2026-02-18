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
    python scripts/ingestion/ingest_datatourisme.py
    ```

2.  **Traitement et Transfert des Données :**
    Pour traiter les données depuis MongoDB et les transférer vers PostgreSQL.
    ```bash
    python scripts/processing/mongo_to_postgres.py
    ```

## Accès aux Outils

*   **pgAdmin** : Accessible via `http://localhost:5050` (ou le port que vous avez défini dans votre `.env`).
*   **MongoDB** : Accessible sur `localhost:27017` (ou le port défini).
*   **PostgreSQL** : Accessible sur `localhost:5432` (ou le port défini).