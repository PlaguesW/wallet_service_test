from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..database import get_db, get_locked_wallet
from ..models import Wallet, Operation
from ..schemas import OperationRequest, OperationResponse
from ..redis_client import redis_client
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/wallets", tags=["Operations"])


@router.post("/{wallet_uuid}/operation", response_model=OperationResponse)
def perform_operation(
    wallet_uuid: str, 
    request: OperationRequest, 
    db: Session = Depends(get_db)
):
    """Perform a deposit or withdrawal operation on a wallet."""
    
    try:
        # Check if wallet exists and is locked
        wallet = get_locked_wallet(db, wallet_uuid)
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Кошелек не найден"
            )
        
        # Save the old balance for logging
        old_balance = wallet.balance
        
        # Check if the operation is valid
        if request.operation_type == "DEPOSIT":
            wallet.balance += request.amount
        elif request.operation_type == "WITHDRAW":
            if wallet.balance < request.amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Недостаточно средств на счете"
                )
            wallet.balance -= request.amount
        
        # Create the operation record
        operation = Operation(
            wallet_uuid=wallet_uuid,
            operation_type=request.operation_type,
            amount=request.amount,
            balance_after=wallet.balance
        )
        
        db.add(operation)
        db.commit()
        db.refresh(operation)
        
        # Invalidate the Redis cache for this wallet
        cache_key = f"wallet_balance:{wallet_uuid}"
        redis_client.delete(cache_key)
        
        logger.info(
            f"Operation {request.operation_type} for wallet {wallet_uuid}: "
            f"{old_balance} -> {wallet.balance}"
        )
        
        return OperationResponse(
            balance=wallet.balance,
            operation_id=operation.id
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Operation failed for wallet {wallet_uuid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )