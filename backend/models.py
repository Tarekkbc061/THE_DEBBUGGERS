from typing import List, Optional
from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel, create_engine

class User(SQLModel, table=True):
    # Representa un usuari de l'aplicació (estudiant o professor)
    id: Optional[int] = Field(default=None, primary_key=True)
    nom: str
    email: str = Field(unique=True, index=True)
    google_id: Optional[str] = None
    hashed_password: Optional[str] = None
    role: str = "estudiant" # estudiant, professor
    grau_id: Optional[int] = Field(default=None, foreign_key="degree.id")

class Degree(SQLModel, table=True):
    # Representa un grau o titulació universitària
    id: Optional[int] = Field(default=None, primary_key=True)
    nom: str
    total_credits: int

class Subject(SQLModel, table=True):
    # Representa una assignatura del pla d'estudis
    id: Optional[int] = Field(default=None, primary_key=True)
    codi: str = Field(unique=True)
    nom: str
    credits: int
    tipus: str # FB, OB, OT
    curs: int
    quadrimestre: int

class Prerequisite(SQLModel, table=True):
    # Defineix les dependències entre assignatures
    id: Optional[int] = Field(default=None, primary_key=True)
    subject_id: int = Field(foreign_key="subject.id")
    prerequisite_id: int = Field(foreign_key="subject.id")

class Activity(SQLModel, table=True):
    # Representa una activitat avaluable (Examen, Pràctica, etc.)
    id: Optional[int] = Field(default=None, primary_key=True)
    subject_id: int = Field(foreign_key="subject.id")
    nom: str
    percentatge: float # Percentatge sobre la nota final (0-100)
    nota_minima: float = 0.0
    data_entrega: Optional[str] = None

class UserSubject(SQLModel, table=True):
    # Relaciona un usuari amb les assignatures que cursa o ha cursat
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    subject_id: int = Field(foreign_key="subject.id")
    estat: str # superada, matriculada, planificada
    nota_final: Optional[float] = None
    semestre_planificat: Optional[int] = None
    tags: Optional[str] = None # Llista d'etiquetes separades per comes o JSON

class AcademicMemory(SQLModel, table=True):
    # US007: Recuperar apunts i materials de cursos passats
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    subject_id: int = Field(foreign_key="subject.id")
    titol: str
    contingut: str # Text o URL al material
    tipus: str # apunts, examen, exercici
    curs_academic: str # 2023-24

# ── Espai Interactiu d'Assignatures ─────────────────────────────────────────

class Review(SQLModel, table=True):
    # Ressenya d'un estudiant sobre una assignatura.
    # S'identifica per nom_assignatura + grau_key (en lloc d'un FK a Subject)
    # per desacoblar-se de la BD i connectar directament amb degrees.ts
    id: Optional[int] = Field(default=None, primary_key=True)
    nom_assignatura: str = Field(index=True)   # "Bases de Dades", "Compiladors"...
    grau_key: str = Field(index=True)          # "GEI", "GEXT", "GESA", "GEMCD"
    user_id: int = Field(foreign_key="user.id", index=True)
    text: str
    dificultat: int = Field(ge=1, le=5)           # 1 = molt fàcil, 5 = molt difícil
    carrega_treball: int = Field(ge=1, le=5)       # 1 = poca, 5 = molta
    qualitat_professorat: int = Field(ge=1, le=5)  # 1 = dolenta, 5 = excel·lent
    tags: Optional[str] = None  # JSON array: ["Molta teoria", "Pràctiques difícils"]
    created_at: Optional[str] = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ReviewVote(SQLModel, table=True):
    # Vot de utilitat d'una ressenya (upvote +1 / downvote -1)
    id: Optional[int] = Field(default=None, primary_key=True)
    review_id: int = Field(foreign_key="review.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    valor: int  # +1 upvote, -1 downvote

class ReviewComment(SQLModel, table=True):
    # Comentari a una ressenya
    id: Optional[int] = Field(default=None, primary_key=True)
    review_id: int = Field(foreign_key="review.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    text: str
    created_at: Optional[str] = Field(default_factory=lambda: datetime.utcnow().isoformat())

class UserPrivateNote(SQLModel, table=True):
    # Representa un document privat d'un estudiant dins d'una assignatura
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    subject_id: int = Field(foreign_key="subject.id", index=True)
    titol: str
    mida: str
    nom_arxiu_unic: str
    extensio: str
    data_pujada: Optional[str] = Field(default_factory=lambda: datetime.utcnow().isoformat())


