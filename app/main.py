from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
from contextlib import asynccontextmanager

from app.db_engines.base import BaseDBEngine
from app.api.dependencies import get_db_engine, verify_api_key
from app.services.notifications import send_slack_alert
from app.services.pdf_generator import generate_pdf_report
from app.services.cron import start_scheduler, scheduler
from app.core.config import get_settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lógica de arranque (Ej. levantar Cron Jobs)
    start_scheduler()
    yield
    # Lógica de apagado (Ej. limpiar Scheduler o pools)
    scheduler.shutdown()

app = FastAPI(
    title=get_settings().PROJECT_NAME,
    version=get_settings().VERSION,
    description="Auditor Automatizado de Seguridad y Rendimiento de Bases de Datos",
    lifespan=lifespan
)

@app.post("/api/v1/audit", response_model=List[Dict[str, Any]], dependencies=[Depends(verify_api_key)])
async def run_db_audit(
    background_tasks: BackgroundTasks,
    engine: BaseDBEngine = Depends(get_db_engine)
):
    try:
        await engine.connect()
        # Ejecutamos tanto seguridad como performance
        findings = await engine.run_full_audit()
        
        # Opcional: Integración inmediata con notificaciones (usando BackgroundTasks de FastAPI)
        background_tasks.add_task(send_slack_alert, findings)
        
        return [f.model_dump() for f in findings]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await engine.disconnect()

@app.get("/api/v1/audit/report", dependencies=[Depends(verify_api_key)])
async def download_audit_report(engine: BaseDBEngine = Depends(get_db_engine)):
    try:
        await engine.connect()
        findings = await engine.run_full_audit()
        
        pdf_buffer = generate_pdf_report(findings)
        
        return StreamingResponse(
            pdf_buffer, 
            media_type="application/pdf", 
            headers={"Content-Disposition": f"attachment; filename=dba_report_{engine.__class__.__name__}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await engine.disconnect()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
