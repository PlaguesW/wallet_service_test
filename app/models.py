from sqlalchemy import Column, String, Integer, DateTime, func, Index
from .database import Base


class Wallet(Base):
    __tablename__ = "wallets"
    
    uuid = Column(String(36), primary_key=True, index=True)
    balance = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('ix_wallets_uuid', 'uuid'),
    )


class Operation(Base):
    __tablename__ = "operations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_uuid = Column(String(36), nullable=False, index=True)
    operation_type = Column(String(20), nullable=False)
    amount = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('ix_operations_wallet_uuid', 'wallet_uuid'),
        Index('ix_operations_created_at', 'created_at'),
    )