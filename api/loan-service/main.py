from fastapi import FastAPI
from database import engine, create_db_and_tables, SessionLocal, Base, get_db 
import models 
import crud 
import schemas 
from loans import router as loans_router 
from reservations import router as reservations_router 
from user_interactions import router as users_router 


create_db_and_tables()

app = FastAPI(title="Loan & Reservation Service API", version="0.1.0")


app.include_router(loans_router, prefix="/api/loans", tags=["Loans"])
app.include_router(reservations_router , prefix="/api/reservations", tags=["Reservations"])
app.include_router(users_router, prefix="/api/users", tags=["User Interactions"])

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API Loan & Reservation Service"}

