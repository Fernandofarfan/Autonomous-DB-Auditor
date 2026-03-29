from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
from contextlib import asynccontextmanager

from app.db_engines.base import BaseDBEngine
from app.api.dependencies import get_db_engine, verify_api_key
from app.services.notifications import send_slack_alert
from app.services.pdf_generator import generate_pdf_report
from app.services.cron import start_scheduler, scheduler
from app.services.llm_advisor import enhance_remediation_with_ai
from app.core.database import init_db, SessionLocal
from app.models.audit_history import AuditRecord
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lógica de arranque
    init_db() # Crear base local de SQLAlchemy
    start_scheduler()
    yield
    # Lógica de apagado
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
        findings = await engine.run_full_audit()
        
        # Opcional: Potenciar resoluciones con LLM
        for finding in findings:
            if finding.severity in ("Critical", "High"):
                ai_solution = await enhance_remediation_with_ai(finding.description, finding.engine)
                if ai_solution:
                    finding.remediation_sql = f"-- Sugerencia AI:\n{ai_solution}\n-- Original:\n{finding.remediation_sql}"

        # Guardar en Historial DB (SQLite) modo local
        try:
            db_session = SessionLocal()
            for f in findings:
                record = AuditRecord(
                    engine=f.engine,
                    category=f.category,
                    severity=f.severity,
                    description=f.description,
                    remediation_sql=f.remediation_sql
                )
                db_session.add(record)
            db_session.commit()
        except Exception as e:
            logger.error(f"No se pudo guardar historial DB: {e}")
        finally:
            db_session.close()
        
        # Enviar Slack en background
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
