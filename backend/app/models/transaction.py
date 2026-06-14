from sqlalchemy import Column, Integer, String, Date, Text, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.schema import CheckConstraint

from app.database import Base


class Transaction(Base):
    __tablename__ = "expenses_transaction"

    id = Column(Integer, primary_key=True, index=True)
    debit_date = Column(Date, nullable=False)
    actual_date = Column(Date, nullable=False)
    narration = Column(Text, nullable=False)
    txn_number = Column(String(100), unique=True, nullable=False)
    debit_amount = Column(Numeric(12, 2), default=0)
    credit_amount = Column(Numeric(12, 2), default=0)
    vendor_id = Column(Integer, ForeignKey("expenses_vendor.id", ondelete="SET NULL"), nullable=True)
    category = Column(String(100), default="")
    sub_category = Column(String(100), default="")
    notes = Column(Text, default="")
    exclude = Column(Boolean, default=False)

    vendor = relationship("Vendor", back_populates="transactions")

    __table_args__ = (
        CheckConstraint(
            "(exclude = 1) OR (category != '' AND sub_category != '')",
            name="category_subcategory_required_if_not_excluded",
        ),
    )
