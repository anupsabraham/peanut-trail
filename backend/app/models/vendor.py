from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Vendor(Base):
    __tablename__ = "expenses_vendor"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)

    transactions = relationship("Transaction", back_populates="vendor")
