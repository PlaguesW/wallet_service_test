from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Literal
import uuid


class WalletCreate(BaseModel):
    uuid: str = Field(..., description="UUID Wallet")
    
    @validator('uuid')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Unvalid UUID format')


class WalletResponse(BaseModel):
    uuid: str
    balance: int
    created_at: datetime
    updated_at: datetime = None
    
    class Config:
        from_attributes = True


class BalanceResponse(BaseModel):
    balance: int


class OperationRequest(BaseModel):
    operation_type: Literal["DEPOSIT", "WITHDRAW"] = Field(
        ..., 
        description="Operation type: DEPOSIT or WITHDRAW"
    )
    amount: int = Field(
        ..., 
        gt=0, 
        description="operation amount (must be greater than 0)"
    )


class OperationResponse(BaseModel):
    balance: int
    operation_id: int
    
    
class OperationHistory(BaseModel):
    id: int
    operation_type: str
    amount: int
    balance_after: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class HealthCheck(BaseModel):
    status: str
    database: bool
    redis: bool
    timestamp: datetime