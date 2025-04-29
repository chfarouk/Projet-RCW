from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index 
from database import Base 
from datetime import datetime

class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True) 
    document_id = Column(Integer, nullable=False, index=True) 

    loan_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=False) 
    status = Column(String(50), nullable=False, default='active') 

    def __repr__(self):
        return f'<Loan {self.id}: U{self.user_id} D{self.document_id}>'

class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    document_id = Column(Integer, nullable=False, index=True)

    reservation_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    status = Column(String(50), nullable=False, default='active') 

    def __repr__(self):
        return f'<Resa {self.id}: U{self.user_id} D{self.document_id}>'
