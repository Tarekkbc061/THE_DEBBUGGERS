"""
Script de seed per a l'Espai Interactiu d'Assignatures.
Crea assignatures del GEI (UPF) i ressenyes de prova.

Executa des del directori /backend:
    python seed.py
"""
import os
import json
from datetime import datetime, timedelta
from sqlmodel import Session, create_engine, select, SQLModel

os.environ.setdefault("DATABASE_URL", "postgresql://user:password@localhost:5432/academic_db")

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=False)

# Importem tots els models perquè SQLModel els registri
from models import (
    User, Degree, Subject, Prerequisite, Activity, UserSubject,
    AcademicMemory, Review, ReviewVote, ReviewComment
)

def crear_taules():
    SQLModel.metadata.create_all(engine)

def seed_subjects(session: Session):
    """Assignatures reals del GEI (UPF)."""
    assignatures = [
        # Curs 1 - Q1
        dict(codi="23660", nom="Matemàtica I", credits=6, tipus="FB", curs=1, quadrimestre=1),
        dict(codi="23661", nom="Fonaments de Computadors", credits=6, tipus="FB", curs=1, quadrimestre=1),
        dict(codi="23662", nom="Introducció a la Programació", credits=6, tipus="FB", curs=1, quadrimestre=1),
        dict(codi="23663", nom="Anglès per a Enginyeria I", credits=4, tipus="FB", curs=1, quadrimestre=1),
        # Curs 1 - Q2
        dict(codi="23664", nom="Matemàtica II", credits=6, tipus="FB", curs=1, quadrimestre=2),
        dict(codi="23665", nom="Algorísmica i Programació", credits=6, tipus="OB", curs=1, quadrimestre=2),
        dict(codi="23666", nom="Lògica per a la Intel·ligència Artificial", credits=6, tipus="OB", curs=1, quadrimestre=2),
        # Curs 2 - Q1
        dict(codi="23670", nom="Estructures de Dades", credits=6, tipus="OB", curs=2, quadrimestre=1),
        dict(codi="23671", nom="Sistemes Operatius", credits=6, tipus="OB", curs=2, quadrimestre=1),
        dict(codi="23672", nom="Xarxes de Computadors", credits=6, tipus="OB", curs=2, quadrimestre=1),
        # Curs 2 - Q2
        dict(codi="23673", nom="Bases de Dades", credits=6, tipus="OB", curs=2, quadrimestre=2),
        dict(codi="23674", nom="Programació Orientada a Objectes", credits=6, tipus="OB", curs=2, quadrimestre=2),
        dict(codi="23675", nom="Enginyeria del Software I", credits=6, tipus="OB", curs=2, quadrimestre=2),
        # Curs 3 - Q1
        dict(codi="23680", nom="Arquitectures de Software", credits=6, tipus="OB", curs=3, quadrimestre=1),
        dict(codi="23681", nom="Intel·ligència Artificial", credits=6, tipus="OB", curs=3, quadrimestre=1),
        dict(codi="23682", nom="Compiladors", credits=6, tipus="OB", curs=3, quadrimestre=1),
        # Curs 3 - Q2
        dict(codi="23683", nom="Aprenentatge Automàtic", credits=6, tipus="OT", curs=3, quadrimestre=2),
        dict(codi="23684", nom="Seguretat Informàtica", credits=6, tipus="OT", curs=3, quadrimestre=2),
        dict(codi="23685", nom="Computació Distribuïda", credits=6, tipus="OT", curs=3, quadrimestre=2),
        # Curs 4 - Q1
        dict(codi="23690", nom="Processament del Llenguatge Natural", credits=6, tipus="OT", curs=4, quadrimestre=1),
        dict(codi="23691", nom="Visió per Computador", credits=6, tipus="OT", curs=4, quadrimestre=1),
        dict(codi="23692", nom="Gestió de Projectes", credits=6, tipus="OB", curs=4, quadrimestre=1),
        # Curs 4 - Q2
        dict(codi="23699", nom="Treball de Fi de Grau", credits=18, tipus="OB", curs=4, quadrimestre=2),
    ]

    subjects_creades = []
    for a in assignatures:
        existent = session.exec(select(Subject).where(Subject.codi == a["codi"])).first()
        if not existent:
            s = Subject(**a)
            session.add(s)
            session.flush()
            subjects_creades.append(s)
        else:
            subjects_creades.append(existent)

    session.commit()
    print(f"✅ {len(subjects_creades)} assignatures preparades")
    return subjects_creades


def seed_users(session: Session):
    """Usuaris de prova."""
    usuaris_data = [
        dict(nom="Oriol Tutusaus", email="oriol.tutusaus01@estudiant.upf.edu", role="estudiant"),
        dict(nom="Maria García", email="maria.garcia01@estudiant.upf.edu", role="estudiant"),
        dict(nom="Pau Martínez", email="pau.martinez01@estudiant.upf.edu", role="estudiant"),
        dict(nom="Laia Ferrer", email="laia.ferrer01@estudiant.upf.edu", role="estudiant"),
        dict(nom="Jordi Puig", email="jordi.puig01@estudiant.upf.edu", role="estudiant"),
    ]

    usuaris = []
    for u_data in usuaris_data:
        existent = session.exec(select(User).where(User.email == u_data["email"])).first()
        if not existent:
            u = User(**u_data)
            session.add(u)
            session.flush()
            usuaris.append(u)
        else:
            usuaris.append(existent)

    session.commit()
    print(f"✅ {len(usuaris)} usuaris preparats")
    return usuaris


def seed_reviews(session: Session, subjects, users):
    """Ressenyes de prova realistes."""
    # Dades de ressenyes per assignatures seleccionades
    ressenyes_data = [
        # Introducció a la Programació
        {
            "subject_codi": "23662",
            "user_email": "oriol.tutusaus01@estudiant.upf.edu",
            "text": "Assignatura molt ben estructurada. El professor explica amb molta claredat i els laboratoris ajuden molt a consolidar els conceptes. Perfecta per entrar al món de la programació. Però compte, els exàmens no són trivials.",
            "dificultat": 3, "carrega_treball": 3, "qualitat_professorat": 5,
            "tags": ["Laboratoris pràctics", "Bon professorat", "Exàmens difícils"],
            "dies_enrere": 10,
        },
        {
            "subject_codi": "23662",
            "user_email": "maria.garcia01@estudiant.upf.edu",
            "text": "La base de tot el grau. Si li poses ganes, s'aprèn moltíssim. El codi inicial és fàcil però al final fas projectes bastant complexos. Totalment recomanada.",
            "dificultat": 2, "carrega_treball": 4, "qualitat_professorat": 4,
            "tags": ["Molta teoria", "Molt útil per la carrera", "Projecte final"],
            "dies_enrere": 5,
        },
        # Estructures de Dades
        {
            "subject_codi": "23670",
            "user_email": "pau.martinez01@estudiant.upf.edu",
            "text": "Una de les assignatures més difícils del grau. Els arbres i els grafs porten moltes hores de feina. L'examen final és molt llarg i requereix tenir-ho tot molt clar. Però val la pena perquè és fonamental.",
            "dificultat": 5, "carrega_treball": 5, "qualitat_professorat": 4,
            "tags": ["Molta teoria", "Pràctiques difícils", "Exàmens difícils", "Molt útil per la carrera"],
            "dies_enrere": 20,
        },
        {
            "subject_codi": "23670",
            "user_email": "laia.ferrer01@estudiant.upf.edu",
            "text": "Difícil però molt ben explicada. El professorat és súper accessible i les hores de tutories ajuden molt. Les pràctiques en Python estan molt ben pensades.",
            "dificultat": 4, "carrega_treball": 4, "qualitat_professorat": 5,
            "tags": ["Laboratoris pràctics", "Bon professorat", "Pràctiques difícils"],
            "dies_enrere": 15,
        },
        # Sistemes Operatius
        {
            "subject_codi": "23671",
            "user_email": "oriol.tutusaus01@estudiant.upf.edu",
            "text": "La pràctica del kernel és un mal de cap però aprens moltíssim. El C és obligatori saber-lo bé. L'assistència no és obligatòria però les classes de laboratori aporten molt.",
            "dificultat": 5, "carrega_treball": 5, "qualitat_professorat": 3,
            "tags": ["Pràctiques difícils", "Molta teoria", "Fàcil d'aprovar"],
            "dies_enrere": 30,
        },
        # Bases de Dades
        {
            "subject_codi": "23673",
            "user_email": "jordi.puig01@estudiant.upf.edu",
            "text": "Molt pràctica i útil. SQL és fonamental i aquí l'aprens bé. El professor fa exemples reals que ajuden a entendre els conceptes. La part de normalització és la més densa.",
            "dificultat": 3, "carrega_treball": 3, "qualitat_professorat": 5,
            "tags": ["Laboratoris pràctics", "Bon professorat", "Molt útil per la carrera"],
            "dies_enrere": 8,
        },
        # Intel·ligència Artificial
        {
            "subject_codi": "23681",
            "user_email": "maria.garcia01@estudiant.upf.edu",
            "text": "Fascinant però exigent. La cerca heurística i els algoritmes de jocs estan molt ben explicats. El minimax implementat des de zero és una experiència brutal. Recomano molt.",
            "dificultat": 4, "carrega_treball": 4, "qualitat_professorat": 5,
            "tags": ["Molta teoria", "Pràctiques difícils", "Molt útil per la carrera", "Bon professorat"],
            "dies_enrere": 3,
        },
        # Aprenentatge Automàtic
        {
            "subject_codi": "23683",
            "user_email": "laia.ferrer01@estudiant.upf.edu",
            "text": "Optativa molt recomanada si et va el món de les dades. S'utilitza Python i scikit-learn. La teoria estadística és densa però els notebooks de pràctiques estan molt ben fets.",
            "dificultat": 4, "carrega_treball": 4, "qualitat_professorat": 4,
            "tags": ["Molta teoria", "Laboratoris pràctics", "Molt útil per la carrera"],
            "dies_enrere": 12,
        },
        # Seguretat Informàtica
        {
            "subject_codi": "23684",
            "user_email": "pau.martinez01@estudiant.upf.edu",
            "text": "Molt interessant si et va el tema. CTFs com a pràctiques, que és molt motivador. El professorat és expert en el sector i aporta perspectiva real. Poca teoria, molt de hands-on.",
            "dificultat": 3, "carrega_treball": 3, "qualitat_professorat": 5,
            "tags": ["Pràctiques difícils", "Bon professorat", "Fàcil d'aprovar"],
            "dies_enrere": 7,
        },
        # Compiladors
        {
            "subject_codi": "23682",
            "user_email": "jordi.puig01@estudiant.upf.edu",
            "text": "L'assignatura més difícil que he fet al grau. ANTLR, anàlisi semàntica, generació de codi... és brutal. Però si la superes sents que has après molt. Assistència pràcticament obligatòria.",
            "dificultat": 5, "carrega_treball": 5, "qualitat_professorat": 3,
            "tags": ["Molta teoria", "Pràctiques difícils", "Exàmens difícils", "Assistència obligatòria"],
            "dies_enrere": 25,
        },
    ]

    # Mapes d'accés ràpid
    subject_map = {s.codi: s for s in subjects}
    user_map = {u.email: u for u in users}

    ressenyes_creades = []
    for data in ressenyes_data:
        subject = subject_map.get(data["subject_codi"])
        user = user_map.get(data["user_email"])
        if not subject or not user:
            continue

        existent = session.exec(
            select(Review).where(
                Review.nom_assignatura == subject.nom,
                Review.grau_key == "GEI",
                Review.user_id == user.id
            )
        ).first()
        if existent:
            ressenyes_creades.append(existent)
            continue

        data_creacio = (datetime.utcnow() - timedelta(days=data["dies_enrere"])).isoformat()
        review = Review(
            nom_assignatura=subject.nom,
            grau_key="GEI",
            user_id=user.id,
            text=data["text"],
            dificultat=data["dificultat"],
            carrega_treball=data["carrega_treball"],
            qualitat_professorat=data["qualitat_professorat"],
            tags=json.dumps(data["tags"]),
            created_at=data_creacio,
        )
        session.add(review)
        session.flush()
        ressenyes_creades.append(review)

    session.commit()
    print(f"✅ {len(ressenyes_creades)} ressenyes preparades")
    return ressenyes_creades


def seed_votes(session: Session, reviews, users):
    """Vots de prova per a les ressenyes."""
    vots_data = [
        (0, 1, 1),   # ressenya 0, usuari 1, upvote
        (0, 2, 1),
        (0, 3, 1),
        (1, 0, 1),
        (1, 4, -1),
        (2, 0, 1),
        (2, 1, 1),
        (2, 3, 1),
        (2, 4, 1),
        (3, 0, 1),
        (3, 2, 1),
        (4, 1, -1),
        (4, 3, 1),
        (5, 0, 1),
        (5, 1, 1),
        (5, 2, 1),
        (6, 3, 1),
        (6, 4, 1),
        (7, 0, 1),
        (8, 1, 1),
        (8, 2, 1),
        (9, 3, -1),
    ]

    vots_creats = 0
    for review_idx, user_idx, valor in vots_data:
        if review_idx >= len(reviews) or user_idx >= len(users):
            continue
        review = reviews[review_idx]
        user = users[user_idx]

        existent = session.exec(
            select(ReviewVote).where(
                ReviewVote.review_id == review.id,
                ReviewVote.user_id == user.id
            )
        ).first()
        if not existent:
            session.add(ReviewVote(review_id=review.id, user_id=user.id, valor=valor))
            vots_creats += 1

    session.commit()
    print(f"✅ {vots_creats} vots preparats")


def seed_comments(session: Session, reviews, users):
    """Comentaris de prova."""
    comentaris_data = [
        (0, 1, "Totalment d'acord, els laboratoris fan la diferència!"),
        (0, 2, "A mi em va costar una mica més però l'examen final és just."),
        (2, 0, "Quants dies aprox. de feina et va portar la pràctica de grafs?"),
        (2, 1, "A mi unes 3 setmanes intensives. Però val la pena!"),
        (4, 1, "La pràctica del shell és brutal però aprens C com un campió."),
        (6, 0, "Quin professor tens? El de torn de tarda és molt bo."),
        (9, 0, "Ei, l'ANTLR no és tan bo com sembla... però és el que hi ha."),
    ]

    comentaris_creats = 0
    for review_idx, user_idx, text in comentaris_data:
        if review_idx >= len(reviews) or user_idx >= len(users):
            continue
        review = reviews[review_idx]
        user = users[user_idx]

        session.add(ReviewComment(
            review_id=review.id,
            user_id=user.id,
            text=text,
            created_at=(datetime.utcnow() - timedelta(days=review_idx)).isoformat()
        ))
        comentaris_creats += 1

    session.commit()
    print(f"✅ {comentaris_creats} comentaris preparats")


if __name__ == "__main__":
    print("🌱 Iniciant seed de l'Espai Interactiu d'Assignatures...")
    crear_taules()
    with Session(engine) as session:
        subjects = seed_subjects(session)
        users = seed_users(session)
        reviews = seed_reviews(session, subjects, users)
        seed_votes(session, reviews, users)
        seed_comments(session, reviews, users)
    print("🎉 Seed completat correctament!")
