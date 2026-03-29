import aiomysql
from typing import List
from app.db_engines.base import BaseDBEngine, AuditFinding
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)

class MySQLEngine(BaseDBEngine):
    def __init__(self, **opts):
        self.settings = get_settings()
        self.host = opts.get("host", self.settings.MYSQL_HOST)
        self.port = int(opts.get("port", self.settings.MYSQL_PORT))
        self.user = opts.get("user", self.settings.MYSQL_USER)
        self.password = opts.get("password", self.settings.MYSQL_PASSWORD)
        self.db = opts.get("db", self.settings.MYSQL_DB)
        self.pool = None

    async def connect(self) -> None:
        try:
            self.pool = await aiomysql.create_pool(
                host=self.host, port=self.port,
                user=self.user, password=self.password,
                db=self.db, autocommit=True,
                minsize=1, maxsize=5
            )
        except Exception as e:
            logger.error(f"Error conectando a MySQL: {e}")
            raise

    async def disconnect(self) -> None:
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

    async def analyze_security(self) -> List[AuditFinding]:
        findings = []
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    # Riesgo crítico: Usuarios que se pueden conectar desde cualquier Host (%)
                    await cur.execute("SELECT User, Host FROM mysql.user WHERE Host = '%';")
                    for row in await cur.fetchall():
                        findings.append(AuditFinding(
                            category="Security", severity="High",
                            description=f"El usuario '{row['User']}' puede conectarse desde cualquier host (peligro de fuerza bruta externa).",
                            remediation_sql=f"UPDATE mysql.user SET Host='127.0.0.1' WHERE User='{row['User']}' AND Host='%'; FLUSH PRIVILEGES;",
                            engine="MySQL"
                        ))
                    
                    # Cuentas nativas sin contraseña (poco frecuente en builds actuales, pero posible)
                    await cur.execute("SELECT User, Host FROM mysql.user WHERE authentication_string = '';")
                    for row in await cur.fetchall():
                        findings.append(AuditFinding(
                            category="Security", severity="Critical",
                            description=f"El usuario '{row['User']}' no tiene contraseña configurada.",
                            remediation_sql=f"ALTER USER '{row['User']}'@'{row['Host']}' IDENTIFIED BY 'nueva_pass_fuerte';",
                            engine="MySQL"
                        ))
        except Exception as e:
            logger.warning(f"Error analizando seguridad MySQL (posibles privilegios faltantes): {e}")

        return findings

    async def analyze_performance(self) -> List[AuditFinding]:
        findings = []
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    # Encontrar tablas grandes fragmentadas (Engine innodb, comprobación de data_free)
                    await cur.execute("""
                        SELECT table_name, table_schema, data_free 
                        FROM information_schema.tables 
                        WHERE engine = 'InnoDB' AND data_free > 10 * 1024 * 1024 LIMIT 10;
                    """)
                    for row in await cur.fetchall():
                        findings.append(AuditFinding(
                            category="Performance", severity="Medium",
                            description=f"La tabla '{row['table_name']}' en el esquema '{row['table_schema']}' tiene más de 10MB fragmentados.",
                            remediation_sql=f"OPTIMIZE TABLE {row['table_schema']}.{row['table_name']};",
                            engine="MySQL"
                        ))
        except Exception as e:
            logger.warning(f"Error analizando rendimiento MySQL: {e}")
            
        return findings
