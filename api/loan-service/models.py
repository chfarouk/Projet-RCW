# api/loan-service/models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index # Importer depuis sqlalchemy
# from sqlalchemy.orm import declarative_base # Utiliser la Base de database.py
from database import Base # Importer la Base locale
from datetime import datetime

# Modèle Loan (pour le numérique)
class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True) # ID de l'utilisateur (service externe)
    document_id = Column(Integer, nullable=False, index=True) # ID du document (service externe)

    loan_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=False) # Doit être calculée lors de la création
    status = Column(String(50), nullable=False, default='active') # active, returned, expired

    # Pas de relations directes ici

    def __repr__(self):
        return f'<Loan {self.id}: U{self.user_id} D{self.document_id}>'


# Modèle Reservation (pour le physique)
class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    document_id = Column(Integer, nullable=False, index=True)

    reservation_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    status = Column(String(50), nullable=False, default='active') # active, cancelled, honored

    # Pas de relations directes ici

    def __repr__(self):
        return f'<Resa {self.id}: U{self.user_id} D{self.document_id}>'