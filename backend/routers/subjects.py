from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from typing import List, Optional
import json
import os
import uuid
from pydantic import BaseModel

from database import obtenir_sessio
from models import Subject, UserSubject, User, AcademicMemory, UserPrivateNote
from routers.users import obtenir_usuari_actual

router = APIRouter(prefix="/subjects", tags=["subjects"])

class SubjectStatusUpdate(BaseModel):
    estat: str # superada, matriculada, planificada
    nota_final: Optional[float] = None
    tags: Optional[List[str]] = None
    semestre_planificat: Optional[int] = None

@router.get("/", response_model=List[Subject])
def llistar_assignatures(db: Session = Depends(obtenir_sessio)):
    # Retorna totes les assignatures disponibles a la base de dades
    return db.exec(select(Subject)).all()

@router.post("/", response_model=Subject)
def crear_assignatura(subject: Subject, db: Session = Depends(obtenir_sessio)):
    # Registra una nova assignatura al sistema
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject

# ── Relació Assignatures-Usuari (Estat i Tags) ──────────────────────────────

@router.get("/status", response_model=List[UserSubject])
def obtenir_estats_usuari(
    db: Session = Depends(obtenir_sessio), 
    user: User = Depends(obtenir_usuari_actual)
):
    # Retorna tots els registres de relació assignatura-usuari per a l'usuari actiu
    return db.exec(select(UserSubject).where(UserSubject.user_id == user.id)).all()

@router.post("/{subject_id}/status", response_model=UserSubject)
def actualitzar_estat_assignatura(
    subject_id: int,
    status_data: SubjectStatusUpdate,
    db: Session = Depends(obtenir_sessio),
    user: User = Depends(obtenir_usuari_actual)
):
    # Verificar que l'assignatura existeixi
    subject = db.exec(select(Subject).where(Subject.id == subject_id)).first()
    if not subject:
        # També donem suport a buscar-la per nom o codi si cal, però id és el FK.
        # Si no la trobem per id, la busquem per codi
        raise HTTPException(status_code=404, detail="Assignatura no trobada")

    # Buscar si ja existeix la relació
    user_subject = db.exec(
        select(UserSubject)
        .where(UserSubject.user_id == user.id)
        .where(UserSubject.subject_id == subject_id)
    ).first()

    tags_str = json.dumps(status_data.tags) if status_data.tags is not None else None

    if not user_subject:
        user_subject = UserSubject(
            user_id=user.id,
            subject_id=subject_id,
            estat=status_data.estat,
            nota_final=status_data.nota_final,
            tags=tags_str,
            semestre_planificat=status_data.semestre_planificat
        )
    else:
        user_subject.estat = status_data.estat
        if status_data.nota_final is not None:
            user_subject.nota_final = status_data.nota_final
        if status_data.tags is not None:
            user_subject.tags = tags_str
        if status_data.semestre_planificat is not None:
            user_subject.semestre_planificat = status_data.semestre_planificat

    db.add(user_subject)
    db.commit()
    db.refresh(user_subject)
    return user_subject

# ── Materials Acadèmics i Apunts (AcademicMemory) ───────────────────────────

class MaterialCreate(BaseModel):
    titol: str
    contingut: str
    tipus: str # apunts, examen, exercici
    curs_academic: str = "2025-26"

@router.get("/{subject_id}/materials", response_model=List[AcademicMemory])
def llistar_materials_assignatura(
    subject_id: int, 
    db: Session = Depends(obtenir_sessio)
):
    # Retorna tots els materials/apunts de l'assignatura
    return db.exec(select(AcademicMemory).where(AcademicMemory.subject_id == subject_id)).all()

@router.post("/{subject_id}/materials", response_model=AcademicMemory)
def crear_material_assignatura(
    subject_id: int,
    material_data: MaterialCreate,
    db: Session = Depends(obtenir_sessio),
    user: User = Depends(obtenir_usuari_actual)
):
    # Validar que l'assignatura existeixi
    subject = db.exec(select(Subject).where(Subject.id == subject_id)).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Assignatura no trobada")

    # Crear nou material
    material = AcademicMemory(
        user_id=user.id,
        subject_id=subject_id,
        titol=material_data.titol,
        contingut=material_data.contingut,
        tipus=material_data.tipus,
        curs_academic=material_data.curs_academic
    )
    
    db.add(material)
    db.commit()
    db.refresh(material)
    return material

# ── Apunts i Documents Privats de l'Estudiant (Drive Privat) ─────────────────

UPLOAD_DIR = "/app/uploads/private_notes"

@router.get("/{subject_id}/private-notes", response_model=List[UserPrivateNote])
def llistar_notes_privades(
    subject_id: int,
    db: Session = Depends(obtenir_sessio),
    user: User = Depends(obtenir_usuari_actual)
):
    # Retorna només els fitxers privats de l'usuari actiu per aquesta assignatura
    return db.exec(
        select(UserPrivateNote)
        .where(UserPrivateNote.user_id == user.id)
        .where(UserPrivateNote.subject_id == subject_id)
    ).all()

@router.post("/{subject_id}/private-notes", response_model=UserPrivateNote)
def carregar_nota_privada(
    subject_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(obtenir_sessio),
    user: User = Depends(obtenir_usuari_actual)
):
    # Validar que l'assignatura existeixi
    subject = db.exec(select(Subject).where(Subject.id == subject_id)).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Assignatura no trobada")

    # Crear subdirectori de l'usuari si no existeix
    user_upload_dir = os.path.join(UPLOAD_DIR, str(user.id))
    os.makedirs(user_upload_dir, exist_ok=True)

    # Generar nom de fitxer únic i desar-lo
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(user_upload_dir, unique_filename)

    # Llegir contingut i desar-lo
    try:
        contents = file.file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No s'ha pogut desar el fitxer: {str(e)}")

    # Calcular mida llegible
    size_bytes = len(contents)
    if size_bytes < 1024:
        mida_str = f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        mida_str = f"{size_bytes / 1024:.1f} KB"
    else:
        mida_str = f"{size_bytes / (1024 * 1024):.1f} MB"

    # Persistir registre a la base de dades
    private_note = UserPrivateNote(
        user_id=user.id,
        subject_id=subject_id,
        titol=file.filename,
        mida=mida_str,
        nom_arxiu_unic=unique_filename,
        extensio=file_ext.replace(".", "").upper() or "DOC"
    )

    db.add(private_note)
    db.commit()
    db.refresh(private_note)
    return private_note

@router.get("/private-notes/download/{note_id}")
def descarregar_nota_privada(
    note_id: int,
    db: Session = Depends(obtenir_sessio),
    user: User = Depends(obtenir_usuari_actual)
):
    # Buscar nota a la BD
    note = db.exec(select(UserPrivateNote).where(UserPrivateNote.id == note_id)).first()
    if not note:
        raise HTTPException(status_code=404, detail="Fitxer no trobat")

    # Verificar que l'usuari sigui el propietari del fitxer privat
    if note.user_id != user.id:
        raise HTTPException(status_code=403, detail="Accés denegat: Aquest és un fitxer privat d'un altre estudiant")

    # Comprovar existència física del fitxer
    file_path = os.path.join(UPLOAD_DIR, str(user.id), note.nom_arxiu_unic)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="El fitxer físic no existeix al servidor")

    return FileResponse(file_path, filename=note.titol)

@router.delete("/private-notes/{note_id}")
def esborrar_nota_privada(
    note_id: int,
    db: Session = Depends(obtenir_sessio),
    user: User = Depends(obtenir_usuari_actual)
):
    # Buscar nota a la BD
    note = db.exec(select(UserPrivateNote).where(UserPrivateNote.id == note_id)).first()
    if not note:
        raise HTTPException(status_code=404, detail="Fitxer no trobat")

    # Verificar propietat
    if note.user_id != user.id:
        raise HTTPException(status_code=403, detail="Accés denegat")

    # Intentar esborrar fitxer físic
    file_path = os.path.join(UPLOAD_DIR, str(user.id), note.nom_arxiu_unic)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

    # Esborrar de la BD
    db.delete(note)
    db.commit()
    return {"detail": "Fitxer esborrat amb èxit"}
