from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class AuditFinding(BaseModel):
    category: str  # "Security", "Performance"
    severity: str  # "Critical", "High", "Medium", "Low"
    description: str
    remediation_sql: Optional[str] = None
    engine: str

class BaseDBEngine(ABC):
    """
    Abstracción sobre un motor de base de datos específico (Strategy/Adapter Pattern).
    Cada motor debe implementar su lógica particular para conectar y analizar los esquemas.
    """
    
    @abstractmethod
    async def connect(self) -> None:
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        pass
    
    @abstractmethod
    async def analyze_security(self) -> List[AuditFinding]:
        """Audita seguridad: permisos, usuarios, encriptación."""
        pass
        
    @abstractmethod
    async def analyze_performance(self) -> List[AuditFinding]:
        """Audita rendimiento: índices faltantes, full scans, deadlocks."""
        pass

    async def run_full_audit(self) -> List[AuditFinding]:
        """Ejecuta todos los módulos de análisis."""
        security_findings = await self.analyze_security()
        performance_findings = await self.analyze_performance()
        return security_findings + performance_findings
