from typing import List, Dict, Any
from app.db_engines.base import BaseDBEngine, AuditFinding
from app.core.config import get_settings
import asyncpg
import logging

logger = logging.getLogger(__name__)

class PostgresEngine(BaseDBEngine):
    def __init__(self, **opts):
        self.settings = get_settings()
        self.dsn = opts.get("dsn", f"postgresql://{self.settings.PG_USER}:{self.settings.PG_PASSWORD}@{self.settings.PG_HOST}:{self.settings.PG_PORT}/{self.settings.PG_DB}")
        self.pool: asyncpg.Pool = None

    async def connect(self) -> None:
        try:
            self.pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=10)
        except Exception as e:
            logger.error(f"Error creando pool Postgres: {e}")
            raise

    async def disconnect(self) -> None:
        if self.pool:
            await self.pool.close()

    async def analyze_security(self) -> List[AuditFinding]:
        findings = []
        async with self.pool.acquire() as conn:
            # 1. Buscar usuarios con privilegios de superusuario
            query_super = "SELECT rolname FROM pg_roles WHERE rolsuper = true AND rolname != 'postgres';"
            for row in await conn.fetch(query_super):
                findings.append(AuditFinding(
                    category="Security", severity="Critical",
                    description=f"El rol '{row['rolname']}' tiene privilegios de SUPERUSER innecesarios.",
                    remediation_sql=f"ALTER ROLE {row['rolname']} NOSUPERUSER;", engine="PostgreSQL"
                ))
            
            # 2. Conexiones sin encriptar (SSL = false)
            query_ssl = """
                SELECT usename, client_addr 
                FROM pg_stat_ssl 
                JOIN pg_stat_activity ON pg_stat_ssl.pid = pg_stat_activity.pid 
                WHERE ssl = false AND backend_type = 'client backend';
            """
            for row in await conn.fetch(query_ssl):
                findings.append(AuditFinding(
                    category="Security", severity="Medium",
                    description=f"El usuario '{row['usename']}' ({row['client_addr']}) conectó sin SSL.",
                    remediation_sql="-- Configurar hostssl en pg_hba.conf para forzar cifrado para esta IP/Usuario.", engine="PostgreSQL"
                ))

            # 3. Validar contraseñas antiguas (MD5 en lugar de SCRAM)
            try:
                query_pwd = "SELECT usename FROM pg_shadow WHERE passwd LIKE 'md5%';"
                for row in await conn.fetch(query_pwd):
                    findings.append(AuditFinding(
                        category="Security", severity="High",
                        description=f"El usuario '{row['usename']}' utiliza encriptación débil (MD5).",
                        remediation_sql=f"ALTER ROLE {row['usename']} ENCRYPTED PASSWORD 'nueva_pass_fuerte';", engine="PostgreSQL"
                    ))
            except Exception as e:
                logger.warning(f"No se pudo consultar pg_shadow (falta de privilegios): {e}")

        return findings

    async def analyze_performance(self) -> List[AuditFinding]:
        findings = []
        async with self.pool.acquire() as conn:
            # 1. Secuential Scans (Candidatas a falta de índices)
            query_seq = """
                SELECT relname AS table_name, seq_scan 
                FROM pg_stat_user_tables 
                WHERE seq_scan > 1000 AND (idx_scan IS NULL OR seq_scan > idx_scan) LIMIT 10;
            """
            for row in await conn.fetch(query_seq):
                findings.append(AuditFinding(
                    category="Performance", severity="High",
                    description=f"La tabla '{row['table_name']}' sufre de {row['seq_scan']} Secuential Scans. Propenso a falta de índices.",
                    remediation_sql=f"CREATE INDEX CONCURRENTLY idx_{row['table_name']}_opt ON {row['table_name']} (/*_columna_*/);", engine="PostgreSQL"
                ))

            # 2. Índices sin uso comprobado en las métricas
            query_idx = """
                SELECT relname, indexrelname, idx_scan 
                FROM pg_stat_user_indexes 
                WHERE idx_scan = 0 AND idx_scan IS NOT NULL LIMIT 10;
            """
            for row in await conn.fetch(query_idx):
                findings.append(AuditFinding(
                    category="Performance", severity="Medium",
                    description=f"El índice '{row['indexrelname']}' en la tabla '{row['relname']}' no está siendo utilizado (idx_scan = 0).",
                    remediation_sql=f"DROP INDEX CONCURRENTLY {row['indexrelname']};", engine="PostgreSQL"
                ))

            # 3. Tablas hinchadas (Bloat / Dead Tuples) (Podría causar problemas de rendimiento)
            query_bloat = "SELECT relname, n_dead_tup FROM pg_stat_user_tables WHERE n_dead_tup > 10000;"
            for row in await conn.fetch(query_bloat):
                findings.append(AuditFinding(
                    category="Performance", severity="Low",
                    description=f"La tabla '{row['relname']}' tiene una alta cantidad de tuplas muertas: {row['n_dead_tup']}.",
                    remediation_sql=f"VACUUM ANALYZE {row['relname']};", engine="PostgreSQL"
                ))
            
        return findings
