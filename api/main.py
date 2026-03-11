from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
import subprocess
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from scripts.utils.db_connect import get_pg_conn_api
import json
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from pathlib import Path
import sys
import psutil
import asyncio
import os

load_dotenv()

#Configuration
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 525600

app_iv = FastAPI()

def script_already_running(script_name: str):
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        cmdline = proc.info['cmdline']
        if cmdline and script_name in " ".join(cmdline):
            return True
    return False

async def run_script_1():
    script_path = Path("scripts/ingestion/ingest_datatourisme.py")

    if script_already_running(str(script_path)):
        print("Script déjà en cours, lancement ignoré")
        return

    python_executable = sys.executable  # assure le même Python que FastAPI
    process = await asyncio.create_subprocess_exec(
        python_executable, str(script_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    
    return process.returncode, stdout.decode(), stderr.decode()

async def run_script_2():
    script_path = Path("scripts/processing/mongo_to_postgres.py")

    if script_already_running(str(script_path)):
        print("Script déjà en cours, lancement ignoré")
        return

    python_executable = sys.executable  # assure le même Python que FastAPI
    process = await asyncio.create_subprocess_exec(
        python_executable, str(script_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    
    return process.returncode, stdout.decode(), stderr.decode()
    
async def run_script_3():
    script_path = Path("scripts/ml/predict_all_pois.py")

    if script_already_running(str(script_path)):
        print("Script déjà en cours, lancement ignoré")
        return

    python_executable = sys.executable  # assure le même Python que FastAPI
    process = await asyncio.create_subprocess_exec(
        python_executable, str(script_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    
    return process.returncode, stdout.decode(), stderr.decode()

async def run_script_4():
    script_path = Path("scripts/neo4j_db/ingestion_neo4j.py")

    if script_already_running(str(script_path)):
        print("Script déjà en cours, lancement ignoré")
        return

    python_executable = sys.executable  # assure le même Python que FastAPI
    process = await asyncio.create_subprocess_exec(
        python_executable, str(script_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    
    return process.returncode, stdout.decode(), stderr.decode()

#Hash mot de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

#Fake base utilisateur
fake_users_db = {
    "admin": {
        "username": os.getenv("API_USER"),
        "hashed_password": pwd_context.hash("Pwd_iv_26!@"),
    }
}

#Modèles
class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str

#Vérification mot de passe
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

#Récupérer utilisateur
def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

#Création token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

#Route login
@app_iv.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects",
        )
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

#Dépendance utilisateur courant
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token invalide")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide")
    return {"username": username}

#Routes protégées
@app_iv.get("/users/me")
def read_users_me(current_user: dict = Depends(get_current_user)):
    return {"user": current_user}
    
@app_iv.get("/internal")
def api_response(current_user: dict = Depends(get_current_user)):
    return {"message": "Bienvenue sur API itinéraire_vacances 🚀"}
    
@app_iv.get("/cities")
def api_response(current_user: dict = Depends(get_current_user)):
    try:
        with get_pg_conn_api() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT city FROM city ORDER BY city ASC;")
                rows = cursor.fetchall()
                json_data = json.dumps(rows, indent=2)
                return rows
    except Exception as e:
        return {
            "database": "error",
            "message": str(e)
        }
        
@app_iv.post("/ppl_batch_1")
async def api_call(current_user: dict = Depends(get_current_user)):
    returncode, out, err = await run_script_1()
    
    if returncode != 0:
        return JSONResponse(
            content={"message": "Script en erreur", "code": returncode, "error": err, "stdout": out},
            status_code=500
        )

    return JSONResponse(
        content={"message": "Script terminé", "code": returncode, "stdout": out, "stderr": err},
        status_code=200
    )

@app_iv.post("/ppl_batch_2")
async def api_call(current_user: dict = Depends(get_current_user)):
    returncode, out, err = await run_script_2()
    
    if returncode != 0:
        return JSONResponse(
            content={"message": "Script en erreur", "code": returncode, "error": err, "stdout": out},
            status_code=500
        )

    return JSONResponse(
        content={"message": "Script terminé", "code": returncode, "stdout": out, "stderr": err},
        status_code=200
    )
    
@app_iv.post("/ppl_batch_3")
async def api_call(current_user: dict = Depends(get_current_user)):
    returncode, out, err = await run_script_3()
    
    if returncode != 0:
        return JSONResponse(
            content={"message": "Script en erreur", "code": returncode, "error": err, "stdout": out},
            status_code=500
        )

    return JSONResponse(
        content={"message": "Script terminé", "code": returncode, "stdout": out, "stderr": err},
        status_code=200
    )
    
@app_iv.post("/ppl_batch_4")
async def api_call(current_user: dict = Depends(get_current_user)):
    returncode, out, err = await run_script_4()
    
    if returncode != 0:
        return JSONResponse(
            content={"message": "Script en erreur", "code": returncode, "error": err, "stdout": out},
            status_code=500
        )

    return JSONResponse(
        content={"message": "Script terminé", "code": returncode, "stdout": out, "stderr": err},
        status_code=200
    )
