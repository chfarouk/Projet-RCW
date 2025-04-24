# api/loan-service/crud.py
from sqlalchemy.orm import Session
from sqlalchemy import func, desc # Pour count et order_by
import models, schemas
from datetime import datetime, timedelta
from typing import List, Optional
import os

# --- Constantes ---
DIGITAL_LOAN_DURATION_DAYS = 14

# === CRUD pour Loans ===

def get_loan(db: Session, loan_id: int) -> Optional[models.Loan]:
    return db.query(models.Loan).filter(models.Loan.id == loan_id).first()

def get_active_loan_by_user_and_document(db: Session, user_id: int, document_id: int) -> Optional[models.Loan]:
    return db.query(models.Loan).filter(
        models.Loan.user_id == user_id,
        models.Loan.document_id == document_id,
        models.Loan.status == 'active'
    ).first()

def get_loans_by_user(db: Session, user_id: int, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[models.Loan]:
    query = db.query(models.Loan).filter(models.Loan.user_id == user_id)
    if status:
        query = query.filter(models.Loan.status == status)
    return query.order_by(models.Loan.due_date).offset(skip).limit(limit).all()

def count_loans(db: Session, status: Optional[str] = None) -> int:
     query = db.query(func.count(models.Loan.id))
     if status:
         query = query.filter(models.Loan.status == status)
     return query.scalar() or 0

def create_loan(db: Session, loan_data: schemas.LoanCreate) -> models.Loan:
    loan_date = datetime.utcnow()
    due_date = loan_date + timedelta(days=DIGITAL_LOAN_DURATION_DAYS)
    db_loan = models.Loan(
        user_id=loan_data.user_id,
        document_id=loan_data.document_id,
        loan_date=loan_date,
        due_date=due_date,
        status='active' # Statut initial
    )
    db.add(db_loan)
    db.commit()
    db.refresh(db_loan)
    return db_loan

def update_loan_status(db: Session, loan_id: int, new_status: str) -> Optional[models.Loan]:
    db_loan = get_loan(db, loan_id)
    if db_loan:
        if new_status not in ['active', 'returned', 'expired']: # Validation statut
             raise ValueError(f"Statut de prêt invalide: {new_status}")
        db_loan.status = new_status
        db.commit()
        db.refresh(db_loan)
        return db_loan
    return None

def get_top_loaned_documents(db: Session, limit: int = 5) -> List[tuple]:
     # Renvoie une liste de tuples (document_id, count)
     top_docs_query = db.query(
             models.Loan.document_id, func.count(models.Loan.id).label('loan_count')
          ).filter(models.Loan.status == 'active') \
           .group_by(models.Loan.document_id) \
           .order_by(desc('loan_count')) \
           .limit(limit).all()
     return top_docs_query

# === CRUD pour Reservations ===

def get_reservation(db: Session, reservation_id: int) -> Optional[models.Reservation]:
    return db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()

def get_active_reservation_by_user_and_document(db: Session, user_id: int, document_id: int) -> Optional[models.Reservation]:
    return db.query(models.Reservation).filter(
        models.Reservation.user_id == user_id,
        models.Reservation.document_id == document_id,
        models.Reservation.status == 'active'
    ).first()

def get_reservations_by_user(db: Session, user_id: int, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[models.Reservation]:
    query = db.query(models.Reservation).filter(models.Reservation.user_id == user_id)
    if status:
        query = query.filter(models.Reservation.status == status)
    return query.order_by(models.Reservation.reservation_date.desc()).offset(skip).limit(limit).all()

def count_reservations(db: Session, status: Optional[str] = None) -> int:
     query = db.query(func.count(models.Reservation.id))
     if status:
         query = query.filter(models.Reservation.status == status)
     return query.scalar() or 0

def create_reservation(db: Session, resa_data: schemas.ReservationCreate) -> models.Reservation:
    db_resa = models.Reservation(
        user_id=resa_data.user_id,
        document_id=resa_data.document_id,
        status='active' # Statut initial
    )
    db.add(db_resa)
    db.commit()
    db.refresh(db_resa)
    return db_resa

def update_reservation_status(db: Session, reservation_id: int, new_status: str) -> Optional[models.Reservation]:
    db_resa = get_reservation(db, reservation_id)
    if db_resa:
        if new_status not in ['active', 'cancelled', 'honored']: # Statuts valides
             raise ValueError(f"Statut de réservation invalide: {new_status}")
        db_resa.status = new_status
        db.commit()
        db.refresh(db_resa)
        return db_resa
    return None

def cancel_reservations_for_document(db: Session, document_id: int) -> int:
    """Annule toutes les réservations actives pour un document donné. Renvoie le nombre annulé."""
    reservations_to_cancel = db.query(models.Reservation).filter(
        models.Reservation.document_id == document_id,
        models.Reservation.status == 'active'
    ).all()
    count = 0
    if reservations_to_cancel:
        for resa in reservations_to_cancel:
            resa.status = 'cancelled'
            count += 1
        db.commit()
    return count