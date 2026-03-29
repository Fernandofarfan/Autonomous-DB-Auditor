import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.anyio
async def test_auth_missing_api_key():
    """Prueba que los endpoints no estén expuestos sin el secret."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/v1/audit", headers={"engine-type": "postgres"})
    assert response.status_code == 403
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.anyio
async def test_auth_invalid_api_key():
    """Prueba que rechace llaves API falsas."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/v1/audit", headers={"X-API-Key": "LLAVE_FALSA", "engine-type": "postgres"})
    assert response.status_code == 403
    assert response.json() == {"detail": "Credenciales API inválidas."}

@pytest.mark.anyio
async def test_unsupported_engine():
    """Prueba que el Factory rechace motores SQL no implementados."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/v1/audit", headers={"X-API-Key": "supersecret_dba_key", "engine-type": "oracle"})
    assert response.status_code == 400
    assert "no soportado aún" in response.json()["detail"]
