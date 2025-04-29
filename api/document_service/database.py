import os
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker 

instance_path = os.path.join(os.path.dirname(__file__), 'instance') 
os.makedirs(instance_path, exist_ok=True) 
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(instance_path, 'document_service.db')}" 
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
def create_db_and_tables():
    try: Base.metadata.create_all(bind=engine); print("Tables Document Service créées.")
    except Exception as e: print(f"Erreur création tables Document Service: {e}")
def get_db():
    db = SessionLocal()
    try: yield db; 
    finally: db.close()
