import httpx
from pydantic import BaseModel
from typing import List, Dict, Any
from app.core.config import get_settings
from app.db_engines.base import AuditFinding
import logging

logger = logging.getLogger(__name__)

async def send_slack_alert(findings: List[AuditFinding]):
    settings = get_settings()
    if not settings.SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL no configurada. Alerta omitida.")
        return

    # Agrupar hallazgos críticos
    critical_findings = [f for f in findings if f.severity in ("Critical", "High")]
    if not critical_findings:
        return
        
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🛡️ DBA-Sentinel: Alerta Crítica de Base de Datos"
            }
        }
    ]

    for finding in critical_findings:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*[{finding.category}] {finding.engine} - {finding.severity}* \n{finding.description}\n> Remediation: `{finding.remediation_sql}`"
                }
            }
        )

    payload = {"blocks": blocks}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(settings.SLACK_WEBHOOK_URL, json=payload)
            response.raise_for_status()
            logger.info("Alerta de DBA-Sentinel enviada exitosamente a Slack.")
    except Exception as e:
        logger.error(f"Error despachando alerta a Slack: {e}")
