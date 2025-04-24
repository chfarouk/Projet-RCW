# api/document_service/main.py

# --- Imports ---
import os
from fastapi import FastAPI
from .database import engine, create_db_and_tables # Import local
from . import models # Importe Base de models.py
from . import documents 
# --- Fin Imports ---

# Chemin de stockage DÉFINI ICI
PDF_STORAGE_PATH_DOC_SERVICE = os.path.join(os.path.dirname(__file__), 'instance', 'uploads', 'pdfs')
os.makedirs(PDF_STORAGE_PATH_DOC_SERVICE, exist_ok=True)

create_db_and_tables() # Crée les tables au démarrage

app = FastAPI(title="Document Service API", version="0.1.0")

# Inclure le routeur des documents
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API Document Service"}

# Ajouter données test au démarrage (optionnel)
@app.on_event("startup")
def startup_event_docs():
    from .database import SessionLocal
    from .models import Document
    db: Session = SessionLocal()
    try:
        # Logique additionnelle si nécessaire
        db.close()
    except Exception as e:
        print(f"Erreur lors du démarrage : {e}")