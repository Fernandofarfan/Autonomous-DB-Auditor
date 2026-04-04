# Arquitectura DBA-Sentinel

Esta documentación sigue el principio de "Enlazar, no incrustar". Su objetivo es describir los patrones arquitectónicos base del proyecto *DBA-Sentinel*.

## Patrones de Diseño Utilizados

1. **Patrón Strategy (Estrategia):**
   *   El núcleo del sistema de auditoría no depende de librerías ni dialectos específicos de bases de datos.
   *   El archivo `/app/db_engines/base.py` define una clase abstracta pura `BaseDBEngine` con métodos virtuales para analizar seguridad (`analyze_security()`) y rendimiento (`analyze_performance()`). 
   *   Esto permite aislar la lógica ("Open/Closed Principle") al momento de crear escáneres específicos para un motor como PostgreSQL.

2. **Patrón Factory (Fábrica):**
   *   Almacenado en `/app/db_engines/factory.py`, intercepta las peticiones (HTTP Headers) y decide en runtime qué objeto inicializar (ej. `PostgresEngine`, `MySQLEngine`). 

3. **Inyección de Dependencias (FastAPI):**
   *   Al utilizar `Depends()` nativo de FastAPI, validamos la entrada del usuario antes de que una petición alcance el controlador.
   *   `get_db_engine` lanza un error HTTP 400 si el motor no está soportado.

4. **12-Factor App (Variables de Entorno):**
   *   Todo secreto, URL, puerto de conexión, o llave API, debe radicar fuera del control de versiones. Empleamos `pydantic-settings` (`SettingsConfigDict`) para este fin.

## Adición de un Nuevo Motor

La plataforma actualmente soporta **PostgreSQL** y **MySQL**. Para extender el alcance de la herramienta a **SQL Server** (u otro motor de bases de datos):

1. Crear una clase `SQLServerEngine` que herede de `BaseDBEngine` (ej. en `app/db_engines/sqlserver.py`).
2. Utilizar librerías asíncronas compatibles (ej. `aioodbc`).
3. Implementar métodos de seguridad y rendimiento haciendo `queries` asíncronas pertinentes para el motor.
4. Extender el diccionario del mapeo expuesto por la fábrica (`factory.py`) apuntando al nuevo motor.