import os
from fastapi import FastAPI
from .database import engine, create_db_and_tables 
from . import models 
from . import documents 

PDF_STORAGE_PATH_DOC_SERVICE = os.path.join(os.path.dirname(__file__), 'instance', 'uploads', 'pdfs')
os.makedirs(PDF_STORAGE_PATH_DOC_SERVICE, exist_ok=True)

create_db_and_tables() 

app = FastAPI(title="Document Service API", version="0.1.0")

app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API Document Service"}

@app.on_event("startup")
def startup_event_docs():
    from .database import SessionLocal
    from .models import Document
    db: Session = SessionLocal()
    try:
        db.close()
    except Exception as e:
        print(f"Erreur lors du démarrage : {e}")
