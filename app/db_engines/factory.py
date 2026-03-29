from app.db_engines.base import BaseDBEngine
from app.db_engines.postgres import PostgresEngine

class DBEgineFactory:
    """
    Patrón Factory para instanciar el motor adecuado basado en un identificador o configuración.
    """
    
    @staticmethod
    def get_engine(engine_type: str, **opts) -> BaseDBEngine:
        engine_map = {
            "postgres": PostgresEngine,
            # "mysql": MySQLEngine,
            # "sqlserver": SQLServerEngine
        }
        
        engine_class = engine_map.get(engine_type.lower())
        if not engine_class:
            raise ValueError(f"Motor de base de datos '{engine_type}' no soportado aún.")
            
        return engine_class(**opts)
