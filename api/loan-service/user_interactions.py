# api/loan-service/api/endpoints/user_interactions.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
import crud, schemas, models
from database import get_db

router = APIRouter()

@router.get("/{user_id}/loans", response_model=List[schemas.LoanOut])
def read_user_loans(
    user_id: int,
    status: Optional[str] = Query(None, enum=['active', 'returned', 'expired']),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    loans = crud.get_loans_by_user(db, user_id=user_id, status=status, skip=skip, limit=limit)
    return loans

@router.get("/{user_id}/reservations", response_model=List[schemas.ReservationOut])
def read_user_reservations(
    user_id: int,
    status: Optional[str] = Query(None, enum=['active', 'cancelled', 'honored']),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    reservations = crud.get_reservations_by_user(db, user_id=user_id, status=status, skip=skip, limit=limit)
    return reservations

# === AJOUTER LA ROUTE DE VÉRIFICATION ICI ===
@router.get("/{user_id}/loans/check", response_model=schemas.ActiveLoanCheck)
def check_active_loan(user_id: int, document_id: int = Query(...), db: Session = Depends(get_db)):
    """Vérifie si un utilisateur a un prêt numérique ACTIF pour un document."""
    loan = crud.get_active_loan_by_user_and_document(db, user_id=user_id, document_id=document_id)
    return {"has_active_loan": loan is not None}

@router.get("/{user_id}/reservations/check", response_model=schemas.ActiveReservationCheck)
def check_active_reservation(user_id: int, document_id: int = Query(...), db: Session = Depends(get_db)):
    """Vérifie si un utilisateur a une réservation physique ACTIVE pour un document."""
    resa = crud.get_active_reservation_by_user_and_document(db, user_id=user_id, document_id=document_id)
    return {"has_active_reservation": resa is not None}
# === FIN AJOUT ===