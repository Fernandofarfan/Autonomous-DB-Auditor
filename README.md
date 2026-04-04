# DBA-Sentinel 🛡️

**DBA-Sentinel** es un Auditor Automatizado de Seguridad y Rendimiento de Bases de Datos, diseñado por y para Database Administrators (DBAs). Se conecta a múltiples motores de bases de datos, analiza métricas y vulnerabilidades de manera no intrusiva, y emite recomendaciones procesables (código SQL de remediación) junto con alertas en tiempo real.

## 🚀 Características Principales

*   **Arquitectura Multi-Motor:** Utiliza los patrones de diseño *Strategy* y *Factory* para abstraer la conexión y ejecución. Actualmente soporta **PostgreSQL** y **MySQL**, con estructura preparada para **SQL Server**.
*   **Módulo de Seguridad:** Detección de usuarios con exceso de privilegios, revisión de roles superuser innecesarios, y futuras integraciones para cifrado SSL/TLS.
*   **Módulo de Rendimiento (Performance):** Análisis proactivo de la base de datos buscando:
    *   Consultas propensas a *Full Table Scans* (Falta de índices).
    *   Estadísticas de uso directo desde el motor (ej. `pg_stat_user_tables`).
*   **Motor de Remediación:** Generación dinámica de SQL de mitigación (ej. scripts de `CREATE INDEX` o `REVOKE`).
*   **Dashboard Interactivo:** Interfaz gráfica desarrollada en Streamlit para visualizar hallazgos y conectarse a la API desde el navegador.
*   **Notificaciones Inteligentes:** Integración nativa asíncrona mediante Webhooks de Slack para notificar automáticamente hallazgos críticos.

## 📂 Arquitectura

La aplicación está construida utilizando **FastAPI** y enfoques asíncronos para garantizar un alto rendimiento.

```text
DBA-Sentinel/
├── app/
│   ├── api/          # Controladores y dependencias de FastAPI (Inyección del Engine)
│   ├── core/         # Configuraciones Globales (Pydantic Settings)
│   ├── db_engines/   # Patrones Strategy (BaseDBEngine) y Factory
│   └── services/     # Lógica de negocio externa (Slack, Reportes)
└── docs/             # Documentación extendida
```

> **Nota:** Para más detalles arquitectónicos, revisar la carpeta `/docs/` (En construcción).

## 🛠️ Requisitos Previos

*   Docker y Docker Compose.
*   (Alternativa) Python 3.10 o superior con un entorno virtual (`venv` o equivalente).

## ⚙️ Instalación y Configuración

1. **Clonar el repositorio y preparar el entorno:**
   ```bash
   git clone <repo-url> DBA-Sentinel
   cd DBA-Sentinel
   ```

2. **Variables de Entorno:**
   Crea un archivo `.env` en la raíz del proyecto (sin comillas para evitar problemas de parseo en Docker):
   ```env
   PROJECT_NAME=DBA-Sentinel
   VERSION=1.0.0
   API_SECRET_KEY=supersecret_dba_key
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T000/B000/XXX
   
   # PostgreSQL Test Configuration
   PG_USER=postgres
   PG_PASSWORD=tu_password
   PG_HOST=dba-postgres
   PG_PORT=5432
   PG_DB=postgres

   # MySQL Test Configuration
   MYSQL_USER=root
   MYSQL_PASSWORD=tu_password
   MYSQL_HOST=dba-mysql
   MYSQL_PORT=3306
   MYSQL_DB=mysql
   ```

## 🐳 Ejecución con Docker (Recomendada)

¡Todo está listo para producción! Puedes levantar el auditor como un microservicio en su propio contenedor usando Docker Compose. Esto incluye el despliegue automático de las tareas programadas (Cron jobs).

```bash
docker-compose down -v
docker-compose up --build -d
```
Una vez en ejecución, los servicios estarán disponibles en:
*   **Dashboard (Streamlit):** [http://localhost:8501](http://localhost:8501)
*   **API (FastAPI) & Swagger:** [http://localhost:8000/docs](http://localhost:8000/docs)
*   **PostgreSQL:** `localhost:5432`
*   **MySQL:** `localhost:3307`

## 🏃‍♂️ Ejecución Local (Desarrollo)

Si prefieres levantarlo directo sin Docker:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📡 Uso del API

Puedes consultar la documentación interactiva Swagger navegando a: `http://localhost:8000/docs`.

**Importante:** Ahora todos los endpoints están protegidos por el Header `X-API-Key`.

### Endpoint de Auditoría

*   **Ruta:** `POST /api/v1/audit`
*   **Headers OBLIGATORIOS:**
    *   `X-API-Key`: `supersecret_dba_key` (o la que se configure en el `.env`).
    *   `engine-type`: `postgres` (o el motor deseado en el futuro, ej: `mysql`).

### Endpoint de Reportes PDF
*   **Ruta:** `GET /api/v1/audit/report`
*   **Headers OBLIGATORIOS:** (Los mismos descritos arriba).
*   **Respuesta:** Descarga directa de bytes (`application/pdf`).

**Respuesta de Ejemplo:**
```json
[
  {
    "category": "Performance",
    "severity": "High",
    "description": "La tabla 'usuarios' sufre de excesivos Secuential Scans (15420). Podría faltar un índice en columnas usadas frecuentemente en WHERE o JOINs.",
    "remediation_sql": "-- Sugerencia: CREATE INDEX idx_usuarios_opt ON usuarios (/*_tu_columna_filtrada_*/);",
    "engine": "PostgreSQL"
  }
]
```
