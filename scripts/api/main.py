from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from scripts.utils.db_connect import get_pg_conn
import json
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

#Configuration
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 525600

app_iv = FastAPI()

#Hash mot de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

#Fake base utilisateur
fake_users_db = {
    "admin": {
        "username": "admin",
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
    conn = get_pg_conn()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT city FROM city ORDER BY city ASC;")

    rows = cursor.fetchall()
    
    json_data = json.dumps(rows, indent=2)
    	
    cursor.close()
    conn.close()
    return rows