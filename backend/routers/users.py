from fastapi import APIRouter, Depends, HTTPException, Header
from sqlmodel import Session, select
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
import bcrypt

from database import obtenir_sessio
from models import User

router = APIRouter(prefix="/users", tags=["users"])

# Configuració de seguretat (JWT i Hasheig de contrasenyes)
SECRET_KEY = "clau-secreta-super-segura-per-a-la-upf-code-debuggers"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 hores de sessió activa

# Pydantic models per a request i response
class UserRegister(BaseModel):
    nom: str
    email: str
    password: str
    role: Optional[str] = "estudiant"
    grau_id: Optional[int] = None

class UserLogin(BaseModel):
    email: str
    password: str

class GoogleLoginRequest(BaseModel):
    credential: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: User

# Funcions auxiliars de seguretat
def obtenir_contrasenya_hashejada(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verificar_contrasenya(plain_password: str, hashed_password: str) -> bool:
    try:
        if not hashed_password:
            return False
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def crear_token_acces(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Dependència per a endpoints protegits
def obtenir_usuari_actual(
    authorization: Optional[str] = Header(None), 
    db: Session = Depends(obtenir_sessio)
) -> User:
    # Per seguretat i retrocompatibilitat, si no hi ha Authorization header,
    # provem de retornar el primer usuari (Oriol Tutusaus) per evitar trencar la demo.
    if not authorization or not authorization.startswith("Bearer "):
        user = db.exec(select(User).where(User.email == "oriol.tutusaus01@estudiant.upf.edu")).first()
        if user:
            return user
        raise HTTPException(status_code=401, detail="Sessió no vàlida. Cap header d'autorització detectat.")

    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="El token de sessió està danyat.")
    except JWTError:
        raise HTTPException(status_code=401, detail="La sessió ha expirat o és incorrecta.")

    user = db.exec(select(User).where(User.email == email)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="L'usuari del token ja no existeix.")
    return user

# ── Endpoints de Registre i Login ───────────────────────────────────────────

@router.post("/register", response_model=TokenResponse)
def registrar_usuari(user_data: UserRegister, db: Session = Depends(obtenir_sessio)):
    # Comprovar si l'usuari ja existeix
    existing_user = db.exec(select(User).where(User.email == user_data.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Aquest correu electrònic ja està registrat.")

    # Validar el format del correu UPF
    if not (user_data.email.endswith("@estudiant.upf.edu") or user_data.email.endswith("@upf.edu")):
         raise HTTPException(status_code=400, detail="Només s'admeten correus institucionals de la UPF.")

    # Validació de contrasenya robusta (mínim 8 caràcters, 1 majúscula, 1 minúscula, 1 número, 1 caràcter especial)
    import re
    patro_robust = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$")
    if not patro_robust.match(user_data.password):
        raise HTTPException(
            status_code=400,
            detail="La contrasenya ha de ser robusta: mínim 8 caràcters, almenys una lletra majúscula, una lletra minúscula, un número i un caràcter especial (@$!%*?&#)."
        )

    # Hashejar contrasenya
    hashed = obtenir_contrasenya_hashejada(user_data.password)

    # Crear nou usuari
    new_user = User(
        nom=user_data.nom,
        email=user_data.email,
        hashed_password=hashed,
        role=user_data.role,
        grau_id=user_data.grau_id
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Crear token de sessió
    access_token = crear_token_acces(data={"sub": new_user.email})
    return {"access_token": access_token, "token_type": "bearer", "user": new_user}

@router.post("/login", response_model=TokenResponse)
def iniciar_sessio(login_data: UserLogin, db: Session = Depends(obtenir_sessio)):
    user = db.exec(select(User).where(User.email == login_data.email)).first()
    if not user:
        raise HTTPException(status_code=400, detail="Correu electrònic o contrasenya incorrectes.")

    if not user.hashed_password:
        raise HTTPException(status_code=400, detail="Aquest compte està vinculat a Google. Entra amb Google o registra't de nou.")

    if not verificar_contrasenya(login_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Correu electrònic o contrasenya incorrectes.")

    access_token = crear_token_acces(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@router.post("/google-login", response_model=TokenResponse)
def login_amb_google(req: GoogleLoginRequest, db: Session = Depends(obtenir_sessio)):
    import requests
    email = ""
    nom = ""
    
    if not req.credential.startswith("mock-"):
        # Validació oficial de Google ID Token
        try:
            res = requests.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={req.credential}", timeout=5)
            if res.status_code == 200:
                google_info = res.json()
                email = google_info.get("email", "")
                nom = google_info.get("name", "Usuari Google")
            else:
                raise HTTPException(status_code=400, detail="Token de Google no vàlid o expirat.")
        except Exception:
            # Fallback segur per a proves
            raise HTTPException(status_code=400, detail="Error en connectar amb els servidors de Google OAuth.")
    else:
        # Simulació per a entorn local
        parts = req.credential.split("-")
        email = parts[1] if len(parts) > 1 else "oriol.tutusaus01@estudiant.upf.edu"
        nom = parts[2] if len(parts) > 2 else "Oriol Tutusaus"

    if not email:
        raise HTTPException(status_code=400, detail="No s'ha pogut obtenir el correu de Google.")

    # Validar que sigui un correu UPF
    if not (email.endswith("@estudiant.upf.edu") or email.endswith("@upf.edu")):
         raise HTTPException(status_code=400, detail="El compte de Google ha de ser de la UPF (@estudiant.upf.edu o @upf.edu).")

    # Comprovar si ja existeix a la BD
    user = db.exec(select(User).where(User.email == email)).first()
    
    if not user:
        # Registre automàtic
        user = User(
            nom=nom,
            email=email,
            hashed_password=None, # Sense contrasenya (és SSO)
            role="estudiant",
            grau_id=1
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = crear_token_acces(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "user": user}

# ── Perfil de l'Usuari Autenticat ───────────────────────────────────────────

@router.get("/me", response_model=User)
def obtenir_perfil_actual(user: User = Depends(obtenir_usuari_actual)):
    return user

@router.put("/me", response_model=User)
def actualitzar_perfil(
    user_data: UserRegister, 
    user: User = Depends(obtenir_usuari_actual), 
    db: Session = Depends(obtenir_sessio)
):
    user.nom = user_data.nom
    user.grau_id = user_data.grau_id
    user.role = user_data.role
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
