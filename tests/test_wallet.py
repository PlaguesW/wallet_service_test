import pytest
from fastapi.testclient import TestClient


def test_create_wallet(client: TestClient, wallet_uuid: str):
    """Test of wallet creation"""
    response = client.post("/api/v1/wallets/", json={"uuid": wallet_uuid})
    assert response.status_code == 201
    data = response.json()
    assert data["uuid"] == wallet_uuid
    assert data["balance"] == 0


def test_create_duplicate_wallet(client: TestClient, wallet_uuid: str):
    """Creation of a wallet with an existing UUID"""
    client.post("/api/v1/wallets/", json={"uuid": wallet_uuid})
    response = client.post("/api/v1/wallets/", json={"uuid": wallet_uuid})
    assert response.status_code == 409


def test_get_nonexistent_wallet(client: TestClient):
    """Unsuccessful attempt to get a non-existent wallet"""
    response = client.get("/api/v1/wallets/nonexistent")
    assert response.status_code == 404


def test_get_wallet_balance(client: TestClient, wallet_uuid: str):
    """Getting the balance of an existing wallet"""
    client.post("/api/v1/wallets/", json={"uuid": wallet_uuid})
    response = client.get(f"/api/v1/wallets/{wallet_uuid}")
    assert response.status_code == 200
    assert response.json()["balance"] == 0


def test_deposit_operation(client: TestClient, wallet_uuid: str):
    """Operation test of replenishment of the wallet"""
    client.post("/api/v1/wallets/", json={"uuid": wallet_uuid})
    
    response = client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation",
        json={"operation_type": "DEPOSIT", "amount": 1000}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["balance"] == 1000
    assert "operation_id" in data


def test_withdraw_operation(client: TestClient, wallet_uuid: str):
    """Operation of withdrawal from the wallet"""
    client.post("/api/v1/wallets/", json={"uuid": wallet_uuid})
    client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation",
        json={"operation_type": "DEPOSIT", "amount": 1000}
    )
    
    response = client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation",
        json={"operation_type": "WITHDRAW", "amount": 500}
    )
    assert response.status_code == 200
    assert response.json()["balance"] == 500


def test_insufficient_funds(client: TestClient, wallet_uuid: str):
    """Insufficient funds"""
    client.post("/api/v1/wallets/", json={"uuid": wallet_uuid})
    
    response = client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation",
        json={"operation_type": "WITHDRAW", "amount": 1000}
    )
    assert response.status_code == 400


def test_invalid_operation_type(client: TestClient, wallet_uuid: str):
    """Unsuccessful operation with an invalid type"""
    client.post("/api/v1/wallets/", json={"uuid": wallet_uuid})
    
    response = client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation",
        json={"operation_type": "INVALID", "amount": 1000}
    )
    assert response.status_code == 422


def test_negative_amount(client: TestClient, wallet_uuid: str):
    """Negative amount"""
    client.post("/api/v1/wallets/", json={"uuid": wallet_uuid})
    
    response = client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation",
        json={"operation_type": "DEPOSIT", "amount": -1000}
    )
    assert response.status_code == 422


def test_operation_history(client: TestClient, wallet_uuid: str):
    """History of operations"""
    client.post("/api/v1/wallets/", json={"uuid": wallet_uuid})
    client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation",
        json={"operation_type": "DEPOSIT", "amount": 1000}
    )
    client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation",
        json={"operation_type": "WITHDRAW", "amount": 300}
    )
    
    response = client.get(f"/api/v1/wallets/{wallet_uuid}/operations")
    assert response.status_code == 200
    operations = response.json()
    assert len(operations) == 2


def test_health_check(client: TestClient):
    """Check the health of the service"""
    response = client.get("/api/v1/wallets/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "redis" in data


def test_concurrent_operations(client: TestClient, wallet_uuid: str):
    """Concurrent operations on the wallet"""
    import threading
    import time
    
    client.post("/api/v1/wallets/", json={"uuid": wallet_uuid})
    client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation",
        json={"operation_type": "DEPOSIT", "amount": 10000}
    )
    
    results = []
    
    def withdraw_operation():
        response = client.post(
            f"/api/v1/wallets/{wallet_uuid}/operation",
            json={"operation_type": "WITHDRAW", "amount": 100}
        )
        results.append(response.status_code == 200)
    
    # Starting multiple threads for concurrent withdrawals(50)
    threads = []
    for _ in range(50):
        thread = threading.Thread(target=withdraw_operation)
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    # Check the final balance
    response = client.get(f"/api/v1/wallets/{wallet_uuid}")
    final_balance = response.json()["balance"]
    
    successful_operations = sum(results)
    expected_balance = 10000 - (successful_operations * 100)
    
    assert final_balance == expected_balance