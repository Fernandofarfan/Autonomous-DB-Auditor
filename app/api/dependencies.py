from app.db_engines.factory import DBEgineFactory
from app.db_engines.base import BaseDBEngine
from app.core.config import get_settings
from fastapi import Header, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from typing import Optional

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != get_settings().API_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Credenciales API inválidas.")

async def get_db_engine(engine_type: str = Header(..., description="postgres, mysql, sqlserver")) -> BaseDBEngine:
    try:
        engine = DBEgineFactory.get_engine(engine_type)
        return engine
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
