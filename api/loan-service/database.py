# api/loan-service/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os


instance_path = os.path.join(os.path.dirname(__file__), 'instance') # Chemin vers le dossier 'instance'
os.makedirs(instance_path, exist_ok=True) # Crée le dossier si besoin
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(instance_path, 'loan_service.db')}" # URL de connexion à la base de données SQLite 
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
def create_db_and_tables():
    try: Base.metadata.create_all(bind=engine); print("Tables Loan Service créées.")
    except Exception as e: print(f"Erreur création tables Loan Service: {e}")
def get_db():
    db = SessionLocal(); 
    try: yield db; 
    finally: db.close()