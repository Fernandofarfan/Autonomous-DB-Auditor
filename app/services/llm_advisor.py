from openai import AsyncOpenAI
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)

async def enhance_remediation_with_ai(finding_description: str, engine: str) -> str:
    """Invoca un LLM para crear o mejorar la recomendación de arreglo con contexto puro SQL."""
    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        # Si no hay llave, regresa vacío para usar la mitigación default
        return None

    try:
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"Eres un DBA Senior experto resolviendo incidencias en {engine}."},
                {"role": "user", "content": f"Genera un bloque pequeño de código SQL para arreglar este problema. Retorna SOLO el script SQL sin markdown extra: {finding_description}"}
            ],
            temperature=0.2,
            max_tokens=200
        )
        return response.choices[0].message.content.strip().replace("```sql", "").replace("```", "")
    except Exception as e:
        logger.error(f"Error generando AI Remediation: {e}")
        return None
