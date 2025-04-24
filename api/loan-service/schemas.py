# api/loan-service/schemas.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

# --- Schémas pour les PRÊTS NUMÉRIQUES (Loan) ---

# Données nécessaires pour CRÉER un prêt
class LoanCreate(BaseModel):
    user_id: int = Field(..., gt=0, description="ID de l'utilisateur qui emprunte")
    document_id: int = Field(..., gt=0, description="ID du document numérique emprunté")
    # Les dates et statut sont gérés par le backend

# Données d'un prêt renvoyées par l'API
class LoanOut(BaseModel):
    loan_id: int = Field(..., alias='id') # Utiliser 'id' comme alias pour 'loan_id'
    user_id: int
    document_id: int
    loan_date: datetime
    due_date: datetime
    status: str # active, returned, expired

    model_config = ConfigDict(from_attributes=True, populate_by_name=True) # Lire depuis SQLAlchemy, permettre alias


# --- Schémas pour les RÉSERVATIONS PHYSIQUES (Reservation) ---

# Données nécessaires pour CRÉER une réservation
class ReservationCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    document_id: int = Field(..., gt=0)
    # Date et statut gérés par backend

# Données d'une réservation renvoyées par l'API
class ReservationOut(BaseModel):
    reservation_id: int = Field(..., alias='id')
    user_id: int
    document_id: int
    reservation_date: datetime
    status: str # active, cancelled, honored

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# --- Schémas pour les réponses des endpoints de vérification ---
class ActiveLoanCheck(BaseModel):
    has_active_loan: bool

class ActiveReservationCheck(BaseModel):
    has_active_reservation: bool

# --- Schéma pour les réponses de comptage ---
class CountResponse(BaseModel):
    count: int

# --- Schéma pour le Top Prêts ---
# Renvoie une liste de tuples (doc_id, count)
# Pydantic peut gérer ça directement ou on peut créer un schéma
class TopLoanItem(BaseModel):
     document_id: int
     loan_count: int

# On pourrait aussi typer la réponse de /top_digital comme List[Tuple[int, int]]
# mais Pydantic préfère souvent les modèles explicites.