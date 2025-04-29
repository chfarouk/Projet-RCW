from sqlalchemy import Column, Integer, String, Boolean, Text 
from .database import Base 

class Document(Base):
    __tablename__ = "documents" 

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True) 
    author = Column(String(150), nullable=True, index=True) 
    summary = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default='disponible') 
    is_physical = Column(Boolean, default=True, nullable=False)
    is_digital = Column(Boolean, default=False, nullable=False)
    file_path = Column(String(300), nullable=True) 
    cover_image_filename = Column(String(100), nullable=True) 

    def __repr__(self):
        fmts = ("P" if self.is_physical else "") + ("D" if self.is_digital else "")
        img = "I" if self.cover_image_filename else ""
        return f'<Doc {self.id} {self.title[:20]} ({fmts}{img})>'

