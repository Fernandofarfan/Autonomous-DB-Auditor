import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.anyio
async def test_auth_missing_api_key():
    """Prueba que los endpoints no estén expuestos sin el secret."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/v1/audit", headers={"engine-type": "postgres"})
    assert response.status_code in [401, 403]
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.anyio
async def test_auth_invalid_api_key():
    """Prueba que rechace llaves API falsas."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/v1/audit", headers={"X-API-Key": "LLAVE_FALSA", "engine-type": "postgres"})
    assert response.status_code == 403
    assert response.json() == {"detail": "Credenciales API inválidas."}

@pytest.mark.anyio
async def test_unsupported_engine():
    """Prueba que el Factory rechace motores SQL no implementados."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/v1/audit", headers={"X-API-Key": "test_key", "engine-type": "oracle"})
    assert response.status_code == 400
    assert "no soportado aún" in response.json()["detail"]
