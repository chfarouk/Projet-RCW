# api/loan-service/main.py
from fastapi import FastAPI
from database import engine, create_db_and_tables, SessionLocal, Base, get_db # CORRECT
import models # CORRECT
import crud # CORRECT
import schemas # CORRECT
from loans import router as loans_router #
from reservations import router as reservations_router 
from user_interactions import router as users_router 



create_db_and_tables()

app = FastAPI(title="Loan & Reservation Service API", version="0.1.0")

# Inclure les routeurs
app.include_router(loans_router, prefix="/api/loans", tags=["Loans"])
app.include_router(reservations_router , prefix="/api/reservations", tags=["Reservations"])
# Inclure aussi les routes spécifiques par utilisateur
# (Alternativement, on pourrait créer un routeur user_interactions.py)
app.include_router(users_router, prefix="/api/users", tags=["User Interactions"])

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API Loan & Reservation Service"}

