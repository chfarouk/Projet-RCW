# api/loan-service/api/endpoints/loans.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi.responses import FileResponse, RedirectResponse
import crud, models, schemas # Aller chercher dans le dossier parent (app)
from database import get_db
from datetime import datetime
import os
import requests
from models import Loan 
from werkzeug.utils import secure_filename 
# Importer les helpers pour appeler les autres services si besoin DANS les endpoints
from helpers import get_user_data, get_document_data # Exemple si helpers dans main.py

router = APIRouter()

@router.post("/digital", response_model=schemas.LoanOut, status_code=status.HTTP_201_CREATED)
def create_new_digital_loan(loan_data: schemas.LoanCreate, db: Session = Depends(get_db)):
    # --- Vérifications Métier avant de créer ---
    # 1. Vérifier User (existence, rôle, abo?)
    user_info = get_user_data(loan_data.user_id) # Appel API externe
    if not user_info or user_info.get('role') != 'membre':
        raise HTTPException(status_code=403, detail="Utilisateur membre invalide ou introuvable")
    # if user_info.get('subscription_status') != 'active': # Si abonnement actif requis
    #    raise HTTPException(status_code=403, detail="Abonnement membre inactif")

    # 2. Vérifier Document (existence, numérique?)
    doc_info = get_document_data(loan_data.document_id) # Appel API externe
    if not doc_info: raise HTTPException(status_code=404, detail="Document introuvable")
    if not doc_info.get('is_digital'): raise HTTPException(status_code=400, detail="Document non numérique")

    # 3. Vérifier prêt actif existant (logique locale)
    existing = crud.get_active_loan_by_user_and_document(db, user_id=loan_data.user_id, document_id=loan_data.document_id)
    if existing: raise HTTPException(status_code=409, detail="Document déjà emprunté")

    # 4. Créer le prêt
    try: return crud.create_loan(db=db, loan_data=loan_data)
    except Exception as e: raise HTTPException(status_code=500, detail="Erreur interne création prêt")

@router.post("/{loan_id}/return", response_model=schemas.LoanOut)
def return_loan(loan_id: int, db: Session = Depends(get_db)):
    # La validation user_id pourrait se faire ici si passé dans le body, ou se fier à la gateway
    try:
        updated_loan = crud.update_loan_status(db=db, loan_id=loan_id, new_status='returned')
        if updated_loan is None: raise HTTPException(status_code=404, detail="Prêt non trouvé")
        return updated_loan
    except ValueError as ve: raise HTTPException(status_code=400, detail=str(ve)) # Statut invalide
    except Exception as e: raise HTTPException(status_code=500, detail="Erreur interne retour prêt")


@router.get("/count", response_model=schemas.CountResponse) # Compter les prêts
def count_active_loans(status: Optional[str] = Query('active', enum=['active', 'returned', 'expired']), db: Session = Depends(get_db)):
    count = crud.count_loans(db=db, status=status)
    return {"count": count}

@router.get("/top_digital", response_model=List[schemas.TopLoanItem]) # Top prêts
def get_top_loans_endpoint(limit: int = Query(5, ge=1, le=20), db: Session = Depends(get_db)):
    top_data = crud.get_top_loaned_documents(db=db, limit=limit)
    # Convertir la liste de tuples en liste de dicts/objets Pydantic
    return [{"document_id": doc_id, "loan_count": count} for doc_id, count in top_data]

PDF_STORAGE_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'uploads', 'pdfs') # Définir le chemin

@router.get("/api/access_document/{loan_id}", tags=["File Access"]) # Utiliser GET
async def access_document(loan_id: int, db: Session = Depends(get_db)):
    """Sert le fichier PDF associé à un prêt actif."""
    print(f"[Loan Service] Demande accès pour Loan ID {loan_id}")
    try:
        loan = db.query(Loan).filter(Loan.id == loan_id).first()
        if not loan: raise HTTPException(status_code=404, detail="Prêt non trouvé")

        # Vérifier statut actif et date d'expiration
        if loan.status != 'active': raise HTTPException(status_code=403, detail="Prêt non actif.")
        if datetime.utcnow() > loan.due_date:
            loan.status = 'expired'; db.commit() # Marquer comme expiré
            raise HTTPException(status_code=403, detail="Période de prêt terminée.")

        # Récupérer les infos du document (nom du fichier)
        doc_info = get_document_data(loan.document_id)
        if not doc_info: raise HTTPException(status_code=503, detail="Service documents indisponible.")

        file_path_in_db = doc_info.get('file_path')
        if not file_path_in_db: raise HTTPException(status_code=404, detail="Fichier associé introuvable (DB).")

        safe_file_path = secure_filename(file_path_in_db)
        if '..' in safe_file_path or safe_file_path.startswith('/'): raise HTTPException(status_code=400, detail="Chemin fichier invalide.")

        full_file_path = os.path.join(PDF_STORAGE_PATH, safe_file_path)
        print(f"[Loan Service] Tentative d'envoi fichier: {full_file_path}")

        if not os.path.exists(full_file_path):
            print(f"ERREUR: Fichier {safe_file_path} non trouvé dans {PDF_STORAGE_PATH} !")
            raise HTTPException(status_code=404, detail="Fichier PDF introuvable sur le serveur.")

        # Servir le fichier avec FileResponse
        return FileResponse(path=full_file_path, media_type='application/pdf', filename=safe_file_path)

    except HTTPException as http_exc: # Re-lever les HTTPException pour que FastAPI les gère
         raise http_exc
    except Exception as e: # Autres erreurs
         print(f"[Loan Service] Erreur dans /access_document/{loan_id}: {e}")
         raise HTTPException(status_code=500, detail="Erreur interne service prêt.")