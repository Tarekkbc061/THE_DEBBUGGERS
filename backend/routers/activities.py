from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from database import obtenir_sessio
from models import Activity

router = APIRouter(prefix="/activities", tags=["activities"])

@router.get("/{subject_id}", response_model=List[Activity])
def llistar_activitats_assignatura(subject_id: int, db: Session = Depends(obtenir_sessio)):
    # Obté totes les activitats d'avaluació vinculades a una assignatura específica
    return db.exec(select(Activity).where(Activity.subject_id == subject_id)).all()

@router.post("/", response_model=Activity)
def crear_activitat(activity: Activity, db: Session = Depends(obtenir_sessio)):
    # Crea una nova activitat d'avaluació (examen, pràctica, etc.)
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity
