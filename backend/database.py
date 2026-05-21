import os
from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/academic_db")

engine = create_engine(DATABASE_URL, echo=True)

def inicialitzar_db():
    # Crea totes les taules definides als models si no existeixen
    from models import User, Degree, Subject, Prerequisite, Activity, UserSubject, AcademicMemory, Review, ReviewVote, ReviewComment, UserPrivateNote
    from sqlmodel import select
    import bcrypt

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # 1. Crear l'usuari admin/admin (Rol Professor de proves)
        admin_exists = session.exec(select(User).where(User.email == "admin")).first()
        if not admin_exists:
            # Hashejar contrasenya "admin" amb bcrypt estàndard
            salt = bcrypt.gensalt()
            hashed_admin = bcrypt.hashpw("admin".encode('utf-8'), salt).decode('utf-8')
            
            new_admin = User(
                nom="Administrador de Proves",
                email="admin",
                hashed_password=hashed_admin,
                role="professor",
                grau_id=None
            )
            session.add(new_admin)
            session.commit()
            print("Usuari de proves admin/admin creat amb èxit a la BD!")

        # 2. Crear l'usuari Oriol Tutusaus (Rol Estudiant) per a proves
        oriol_exists = session.exec(select(User).where(User.email == "oriol.tutusaus01@estudiant.upf.edu")).first()
        if not oriol_exists:
            # Hashejar contrasenya "oriol" amb bcrypt estàndard
            salt = bcrypt.gensalt()
            hashed_oriol = bcrypt.hashpw("oriol".encode('utf-8'), salt).decode('utf-8')
            
            new_oriol = User(
                nom="Oriol Tutusaus",
                email="oriol.tutusaus01@estudiant.upf.edu",
                hashed_password=hashed_oriol,
                role="estudiant",
                grau_id=None
            )
            session.add(new_oriol)
            session.commit()
            print("Usuari de proves oriol.tutusaus01@estudiant.upf.edu creat amb èxit!")

def obtenir_sessio():
    # Proporciona una sessió de base de dades per a cada petició
    with Session(engine) as session:
        yield session
