from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Wallet, Operation
from ..schemas import (
    WalletCreate, WalletResponse, BalanceResponse, 
    OperationHistory, HealthCheck
)
from ..redis_client import redis_client
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/wallets", tags=["Wallets"])


@router.post("/", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
def create_wallet(wallet_data: WalletCreate, db: Session = Depends(get_db)):
    """Creaatetion of a new wallet"""
    
    # Check if wallet with the same UUID already exists
    existing_wallet = db.query(Wallet).filter(
        Wallet.uuid == wallet_data.uuid
    ).first()
    
    if existing_wallet:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Кошелек с таким UUID уже существует"
        )
    
    # Create a new wallet
    new_wallet = Wallet(uuid=wallet_data.uuid, balance=0)
    db.add(new_wallet)
    db.commit()
    db.refresh(new_wallet)
    
    logger.info(f"Created wallet {wallet_data.uuid}")
    return new_wallet


@router.get("/{wallet_uuid}", response_model=BalanceResponse)
def get_wallet_balance(wallet_uuid: str, db: Session = Depends(get_db)):
    """Getting the balance of a wallet"""
    
    # Try to get balance from cache
    cache_key = f"wallet_balance:{wallet_uuid}"
    cached_balance = redis_client.get(cache_key)
    
    if cached_balance is not None:
        logger.debug(f"Cache hit for wallet {wallet_uuid}")
        return BalanceResponse(balance=cached_balance)
    
    # Get wallet from db
    wallet = db.query(Wallet).filter(Wallet.uuid == wallet_uuid).first()
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Кошелек не найден"
        )
    
    # Cache the balance
    redis_client.set(cache_key, wallet.balance)
    
    logger.debug(f"Database hit for wallet {wallet_uuid}")
    return BalanceResponse(balance=wallet.balance)


@router.get("/{wallet_uuid}/operations", response_model=List[OperationHistory])
def get_wallet_operations(
    wallet_uuid: str, 
    limit: int = 50, 
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Getting the operation history of a wallet"""
    
    # Check if the wallet exists
    wallet = db.query(Wallet).filter(Wallet.uuid == wallet_uuid).first()
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Кошелек не найден"
        )
    
    operations = db.query(Operation).filter(
        Operation.wallet_uuid == wallet_uuid
    ).order_by(Operation.created_at.desc()).offset(offset).limit(limit).all()
    
    return operations


@router.get("/health", response_model=HealthCheck)
def health_check(db: Session = Depends(get_db)):
    """Проверка здоровья сервиса"""
    
    # Check database connection
    try:
        db.execute("SELECT 1")
        db_status = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = False
    
    # Check Redis connection
    redis_status = redis_client.health_check()
    
    overall_status = "healthy" if db_status and redis_status else "unhealthy"
    
    return HealthCheck(
        status=overall_status,
        database=db_status,
        redis=redis_status,
        timestamp=datetime.utcnow()
    )