from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class LoanCreate(BaseModel):
    user_id: int = Field(..., gt=0, description="ID de l'utilisateur qui emprunte")
    document_id: int = Field(..., gt=0, description="ID du document numérique emprunté")

class LoanOut(BaseModel):
    loan_id: int = Field(..., alias='id') 
    user_id: int
    document_id: int
    loan_date: datetime
    due_date: datetime
    status: str 

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ReservationCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    document_id: int = Field(..., gt=0)

class ReservationOut(BaseModel):
    reservation_id: int = Field(..., alias='id')
    user_id: int
    document_id: int
    reservation_date: datetime
    status: str 

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class ActiveLoanCheck(BaseModel):
    has_active_loan: bool

class ActiveReservationCheck(BaseModel):
    has_active_reservation: bool

class CountResponse(BaseModel):
    count: int

class TopLoanItem(BaseModel):
     document_id: int
     loan_count: int
