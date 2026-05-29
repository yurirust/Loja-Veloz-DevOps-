import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Mockar banco antes de importar a app
with patch("sqlalchemy.create_engine"), \
     patch("sqlalchemy.orm.Session"), \
     patch("main.Base.metadata.create_all"):
    from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "pedidos"

def test_criar_pedido_payload_invalido():
    response = client.post("/pedidos", json={})
    assert response.status_code == 422  # Validation error

def test_criar_pedido_quantidade_negativa():
    response = client.post("/pedidos", json={
        "cliente_id": "cli-001",
        "produto_id": "prod-001",
        "quantidade": -1,
        "valor_total": 100.0,
    })
    assert response.status_code == 422

def test_buscar_pedido_nao_encontrado():
    with patch("main.SessionLocal") as mock_session:
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_session.return_value.__enter__ = lambda s: mock_db
        response = client.get("/pedidos/id-inexistente")
        assert response.status_code == 404
