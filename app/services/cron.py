import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.db_engines.factory import DBEgineFactory
from app.services.notifications import send_slack_alert

logger = logging.getLogger(__name__)

# Instanciamos el planificador asíncrono
scheduler = AsyncIOScheduler()

async def scheduled_db_audit_task():
    """
    Tarea central (Cron Job) programada para ejecutarse automáticamente.
    En un entorno real, iteraría sobre una lista de motores/cadenas configuradas en la BD.
    Por defecto lo ejecutamos para Postgres para probar su validez funcional en background.
    """
    logger.info("⏰ Ejecutando cron job: Auditoría programada de base de datos...")
    
    try:
        # Aquí instanciaremos el motor por defecto para la auditoría batch
        engine = DBEgineFactory.get_engine("postgres")
        await engine.connect()
        
        # Ejecutamos módulos
        findings = await engine.run_full_audit()
        
        if findings:
            # Notificamos si hay hallazgos (envía solo High o Critical)
            await send_slack_alert(findings)
            logger.info(f"Cron Job finalizado exitosamente. {len(findings)} hallazgos encontrados.")
        else:
            logger.info("Cron Job finalizado. No se encontraron anomalías.")
            
    except Exception as e:
        logger.error(f"Error en tarea programada (cron job): {e}")
    finally:
        await engine.disconnect()

def start_scheduler():
    """
    Configura y arranca el scheduler general asociándole los intervalos/horarios.
    """
    # Ejemplo de producción real: Ejecutarse todos los viernes a las 3 AM (madrugada)
    # scheduler.add_job(
    #     scheduled_db_audit_task, 
    #     'cron', 
    #     day_of_week='fri', hour=3, minute=0
    # )
    
    # Ejemplo Local: Ejecutar cada 24 horas (u horas establecidas)
    scheduler.add_job(scheduled_db_audit_task, 'interval', hours=24)
    
    scheduler.start()
    logger.info("Módulo Cron activado para auditorías en background.")
