from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func
from typing import Optional
import json

from database import obtenir_sessio
from models import Review, ReviewVote, ReviewComment, User

router = APIRouter(prefix="/reviews", tags=["reviews"])

# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_current_user(db: Session) -> User:
    """Retorna l'usuari actiu simulat (mock d'auth)."""
    user = db.exec(select(User).where(User.email == "oriol.tutusaus01@estudiant.upf.edu")).first()
    if not user:
        user = User(nom="Oriol Tutusaus", email="oriol.tutusaus01@estudiant.upf.edu", role="estudiant")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def _enrich_review(review: Review, db: Session) -> dict:
    """Afegeix puntuació de vots, nº comentaris i nom d'autor a una ressenya."""
    vots = db.exec(select(ReviewVote).where(ReviewVote.review_id == review.id)).all()
    puntuacio_vots = sum(v.valor for v in vots)
    num_comentaris = db.exec(
        select(func.count(ReviewComment.id)).where(ReviewComment.review_id == review.id)
    ).one()
    autor = db.get(User, review.user_id)
    tags = json.loads(review.tags) if review.tags else []
    return {
        **review.model_dump(),
        "puntuacio_vots": puntuacio_vots,
        "num_comentaris": num_comentaris,
        "autor_nom": autor.nom if autor else "Anònim",
        "tags": tags,
    }

def _subject_stats(nom_assignatura: str, grau_key: str, db: Session) -> dict:
    """Calcula les estadístiques agregades de ressenyes per a una assignatura, ignorant el grau per compartir-les."""
    reviews = db.exec(
        select(Review)
        .where(Review.nom_assignatura == nom_assignatura)
    ).all()
    num = len(reviews)
    if num == 0:
        return {
            "nom_assignatura": nom_assignatura,
            "grau_key": grau_key,
            "num_ressenyes": 0,
            "avg_dificultat": 0.0,
            "avg_carrega_treball": 0.0,
            "avg_qualitat_professorat": 0.0,
            "top_tags": [],
        }
    all_tags: list[str] = []
    for r in reviews:
        if r.tags:
            all_tags.extend(json.loads(r.tags))
    tag_counts: dict[str, int] = {}
    for t in all_tags:
        tag_counts[t] = tag_counts.get(t, 0) + 1
    top_tags = sorted(tag_counts, key=lambda t: tag_counts[t], reverse=True)[:3]
    return {
        "nom_assignatura": nom_assignatura,
        "grau_key": grau_key,
        "num_ressenyes": num,
        "avg_dificultat": round(sum(r.dificultat for r in reviews) / num, 1),
        "avg_carrega_treball": round(sum(r.carrega_treball for r in reviews) / num, 1),
        "avg_qualitat_professorat": round(sum(r.qualitat_professorat for r in reviews) / num, 1),
        "top_tags": top_tags,
    }

# ── Estadístiques per assignatura (crida des del SubjectNode i Llistat) ───────

@router.get("/stats/all")
def obtenir_stats_totes(db: Session = Depends(obtenir_sessio)):
    """Retorna estadístiques agrupades de totes les assignatures que tenen ressenyes."""
    reviews = db.exec(select(Review)).all()
    grouped = {}
    for r in reviews:
        key = r.nom_assignatura
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(r)
    
    result = []
    for nom, revs in grouped.items():
        num = len(revs)
        all_tags = []
        for r in revs:
            if r.tags:
                all_tags.extend(json.loads(r.tags))
        tag_counts = {}
        for t in all_tags:
            tag_counts[t] = tag_counts.get(t, 0) + 1
        top_tags = sorted(tag_counts, key=lambda t: tag_counts[t], reverse=True)[:3]
        
        # Agafem el primer grau trobat (només per mantenir el format del diccionari)
        grau = revs[0].grau_key if revs else "GEI"
        
        result.append({
            "nom_assignatura": nom,
            "grau_key": grau,
            "num_ressenyes": num,
            "avg_dificultat": round(sum(r.dificultat for r in revs) / num, 1),
            "avg_carrega_treball": round(sum(r.carrega_treball for r in revs) / num, 1),
            "avg_qualitat_professorat": round(sum(r.qualitat_professorat for r in revs) / num, 1),
            "top_tags": top_tags,
        })
    return result

@router.get("/stats")
def obtenir_stats_assignatura(
    nom: str = Query(..., description="Nom exacte de l'assignatura"),
    grau: str = Query(..., description="Clau del grau: GEI, GEXT, GESA, GEMCD"),
    db: Session = Depends(obtenir_sessio)
):
    """Retorna les estadístiques agrupades d'una assignatura (sense la llista completa)."""
    return _subject_stats(nom, grau, db)

# ── Llistar ressenyes d'una assignatura ──────────────────────────────────────

@router.get("/subject")
def llistar_ressenyes(
    nom: str = Query(..., description="Nom exacte de l'assignatura"),
    grau: str = Query(..., description="Clau del grau: GEI, GEXT, GESA, GEMCD"),
    ordenar_per: str = Query("recents", enum=["recents", "utils", "valorades"]),
    db: Session = Depends(obtenir_sessio)
):
    """Llista totes les ressenyes d'una assignatura, ordenades per criteri (comparteix ressenyes entre graus)."""
    reviews = db.exec(
        select(Review)
        .where(Review.nom_assignatura == nom)
    ).all()

    enriched = [_enrich_review(r, db) for r in reviews]

    if ordenar_per == "recents":
        enriched.sort(key=lambda r: r["created_at"] or "", reverse=True)
    elif ordenar_per == "utils":
        enriched.sort(key=lambda r: r["puntuacio_vots"], reverse=True)
    elif ordenar_per == "valorades":
        enriched.sort(
            key=lambda r: (r["dificultat"] + r["carrega_treball"] + r["qualitat_professorat"]) / 3,
            reverse=True,
        )
    return enriched

# ── Crear una ressenya ────────────────────────────────────────────────────────

@router.post("/")
def crear_ressenya(review_data: dict, db: Session = Depends(obtenir_sessio)):
    """
    Crea una nova ressenya.
    Cos esperat: { nom_assignatura, grau_key, text, dificultat, carrega_treball,
                   qualitat_professorat, tags[] }
    """
    user = _get_current_user(db)

    existent = db.exec(
        select(Review)
        .where(Review.nom_assignatura == review_data["nom_assignatura"])
        .where(Review.grau_key == review_data["grau_key"])
        .where(Review.user_id == user.id)
    ).first()
    if existent:
        raise HTTPException(status_code=409, detail="Ja has escrit una ressenya per aquesta assignatura")

    nova = Review(
        nom_assignatura=review_data["nom_assignatura"],
        grau_key=review_data["grau_key"],
        user_id=user.id,
        text=review_data["text"],
        dificultat=review_data["dificultat"],
        carrega_treball=review_data["carrega_treball"],
        qualitat_professorat=review_data["qualitat_professorat"],
        tags=json.dumps(review_data.get("tags", [])),
    )
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return _enrich_review(nova, db)

# ── Votar una ressenya ────────────────────────────────────────────────────────

@router.post("/{review_id}/vote")
def votar_ressenya(review_id: int, vote_data: dict, db: Session = Depends(obtenir_sessio)):
    """Upvote (+1) o Downvote (-1). Click repetit elimina el vot (toggle)."""
    user = _get_current_user(db)
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Ressenya no trobada")

    valor = vote_data.get("valor")
    if valor not in (1, -1):
        raise HTTPException(status_code=422, detail="El valor ha de ser 1 o -1")

    vot_existent = db.exec(
        select(ReviewVote)
        .where(ReviewVote.review_id == review_id)
        .where(ReviewVote.user_id == user.id)
    ).first()

    if vot_existent:
        if vot_existent.valor == valor:
            db.delete(vot_existent)
        else:
            vot_existent.valor = valor
            db.add(vot_existent)
    else:
        db.add(ReviewVote(review_id=review_id, user_id=user.id, valor=valor))

    db.commit()
    return _enrich_review(review, db)

# ── Comentaris ────────────────────────────────────────────────────────────────

@router.get("/{review_id}/comments")
def llistar_comentaris(review_id: int, db: Session = Depends(obtenir_sessio)):
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Ressenya no trobada")
    comentaris = db.exec(
        select(ReviewComment).where(ReviewComment.review_id == review_id)
    ).all()
    result = []
    for c in comentaris:
        autor = db.get(User, c.user_id)
        result.append({**c.model_dump(), "autor_nom": autor.nom if autor else "Anònim"})
    result.sort(key=lambda c: c["created_at"] or "", reverse=True)
    return result


@router.post("/{review_id}/comments")
def crear_comentari(review_id: int, comment_data: dict, db: Session = Depends(obtenir_sessio)):
    user = _get_current_user(db)
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Ressenya no trobada")
    nou = ReviewComment(review_id=review_id, user_id=user.id, text=comment_data["text"])
    db.add(nou)
    db.commit()
    db.refresh(nou)
    autor = db.get(User, nou.user_id)
    return {**nou.model_dump(), "autor_nom": autor.nom if autor else "Anònim"}
