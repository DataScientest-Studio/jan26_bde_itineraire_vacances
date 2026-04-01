import os
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests

# On récupère les variables d'environnement définies dans le .env
API_URL = os.getenv("API_URL") 
USERNAME = os.getenv("API_USER")
PASSWORD = os.getenv("API_PWD")

def get_token():
    url = f"{API_URL}/token"
    data = {"username": USERNAME, "password": PASSWORD}
    response = requests.post(url, data=data)
    response.raise_for_status()
    
    token = response.json()["access_token"]
    
    # En retournant 'token', Airflow le stocke en base de données 
    # sous la clé "return_value" associée à la tâche 'get_auth_token'
    return token

def run_batch(endpoint, **kwargs):
    # 'ti' pour Task Instance car Airflow l'injecte automatiquement via **kwargs.
    ti = kwargs['ti']
    
    # On doit utiliser xcom car notre token est stocké ici (retour de la fonction)
    token_recupere = ti.xcom_pull(task_ids='get_auth_token')
    
    print(f"Token récupéré via XCom : {token_recupere[:10]}...")
    
    url = f"{API_URL}/{endpoint}"
    headers = {"Authorization": f"Bearer {token_recupere}"}
    
    response = requests.post(url, headers=headers)
    return response.json()

# 2. Définition du DAG
with DAG(
    dag_id="full_tourisme_pipeline",
    # 2 fois par jours, mais on pourra le changer au besoin
    schedule_interval="0 8,20 * * *", 
    start_date=datetime(2026, 1, 1),
    catchup=False, #ici on doit mettre faux sinon airflow va relancer tous les runs dans le passé!!
    tags=['api']
) as dag:

    # Tâche 0 : Authentification
    auth_task = PythonOperator(
        task_id="get_auth_token",
        python_callable=get_token
    )

    # Tâches 1 à 4
    task_1 = PythonOperator(
        task_id="ingestion_mongo",
        python_callable=run_batch,
        op_kwargs={"endpoint": "ppl_batch_1"}
    )

    task_2 = PythonOperator(
        task_id="processing_postgres",
        python_callable=run_batch,
        op_kwargs={"endpoint": "ppl_batch_2"}
    )

    task_3 = PythonOperator(
        task_id="ml_prediction",
        python_callable=run_batch,
        op_kwargs={"endpoint": "ppl_batch_3"}
    )

    task_4 = PythonOperator(
        task_id="ingestion_neo4j",
        python_callable=run_batch,
        op_kwargs={"endpoint": "ppl_batch_4"}
    )

    # Définition de l'ordre du workflow
    auth_task >> task_1 >> task_2 >> task_3 >> task_4