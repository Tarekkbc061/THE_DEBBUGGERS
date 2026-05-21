from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from database import inicialitzar_db, obtenir_sessio
from sqlmodel import Session
from routers import subjects, activities, ai, users, reviews

app = FastAPI(title="Academic Planner API")

# Configuració de CORS per permetre connexions des del frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def a_l_arrencada():
    # S'executa en iniciar el servidor i prepara la base de dades
    inicialitzar_db()

app.include_router(subjects.router)
app.include_router(activities.router)
app.include_router(ai.router)
app.include_router(users.router)
app.include_router(reviews.router)

@app.get("/")
def llegir_arrel():
    # Retorna un missatge de benvinguda a l'arrel de l'API
    return {"missatge": "Benvingut a l'API de l'Assistent Acadèmic"}

@app.get("/health")
def estat_salut():
    # Verifica que el servei estigui actiu i funcionant
    return {"estat": "ok"}
