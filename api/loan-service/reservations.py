# api/loan-service/api/endpoints/reservations.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import crud, models, schemas
from database import get_db
from helpers import get_user_data, get_document_data # Helpers pour appels API externes

router = APIRouter()

@router.post("/physical", response_model=schemas.ReservationOut, status_code=status.HTTP_201_CREATED)
def create_new_physical_reservation(resa_data: schemas.ReservationCreate, db: Session = Depends(get_db)):
    # Vérifications métier
    user_info = get_user_data(resa_data.user_id)
    if not user_info or user_info.get('role') != 'membre': raise HTTPException(status_code=403, detail="Utilisateur membre invalide")
    # if user_info.get('subscription_status') != 'active': raise HTTPException(status_code=403, detail="Abonnement inactif")
    doc_info = get_document_data(resa_data.document_id)
    if not doc_info: raise HTTPException(status_code=404, detail="Document introuvable")
    if not doc_info.get('is_physical'): raise HTTPException(status_code=400, detail="Réservation impossible pour doc non physique")
    if doc_info.get('status') != 'emprunte': raise HTTPException(status_code=409, detail=f"Réservation impossible, doc est '{doc_info.get('status')}'")
    existing = crud.get_active_reservation_by_user_and_document(db, user_id=resa_data.user_id, document_id=resa_data.document_id)
    if existing: raise HTTPException(status_code=409, detail="Réservation déjà active")
    try: return crud.create_reservation(db=db, resa_data=resa_data)
    except Exception as e: raise HTTPException(status_code=500, detail="Erreur interne création réservation")

@router.post("/{reservation_id}/cancel", response_model=schemas.ReservationOut)
def cancel_reservation(reservation_id: int, db: Session = Depends(get_db)):
     # Valider user_id ? Normalement fait par la gateway avant l'appel
    try:
        updated_resa = crud.update_reservation_status(db=db, reservation_id=reservation_id, new_status='cancelled')
        if updated_resa is None: raise HTTPException(status_code=404, detail="Réservation non trouvée")
        return updated_resa
    except ValueError as ve: raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e: raise HTTPException(status_code=500, detail="Erreur interne annulation")

@router.get("/count", response_model=schemas.CountResponse)
def count_active_reservations(status: Optional[str] = Query('active', enum=['active', 'cancelled', 'honored']), db: Session = Depends(get_db)):
    count = crud.count_reservations(db=db, status=status)
    return {"count": count}

# Endpoint spécifique appelé par la Gateway quand un biblio change statut doc
@router.post("/documents/{document_id}/sync_reservations", status_code=status.HTTP_200_OK)
def sync_document_reservations(document_id: int, db: Session = Depends(get_db)):
    # Cette route est appelée quand le document redevient disponible
    # On annule les réservations actives pour ce document
    try:
        cancelled_count = crud.cancel_reservations_for_document(db=db, document_id=document_id)
        print(f"[Loan Service] Synchro résa pour Doc {document_id}: {cancelled_count} annulée(s).")
        return {"message": f"{cancelled_count} réservation(s) annulée(s) pour document {document_id}"}
    except Exception as e:
         print(f"[Loan Service] Erreur DB sync résa doc {document_id}: {e}")
         raise HTTPException(status_code=500, detail="Erreur interne synchronisation réservations")