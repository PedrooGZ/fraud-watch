# Fraud Watch

Fraud Watch es un proyecto de deteccion de fraude con Machine Learning orientado a operacion analitica.
El sistema esta dividido en frontend (React + Vite) y backend (FastAPI + PostgreSQL), con autenticacion JWT y persistencia operativa completa.

## Funcionalidades principales

- Autenticacion real:
  - Registro: `POST /auth/register`
  - Login: `POST /auth/login`
  - Sesion actual: `GET /auth/me`
- Roles de usuario:
  - `analyst`
  - `admin`
- Autorizacion basica por rol:
  - Solo `admin` puede modificar politica via `PUT /policy`.
- Prediccion de fraude:
  - Single: `POST /predict`
  - Batch JSON: `POST /predict_batch`
  - Upload CSV real: `POST /batch-jobs/upload`
- Persistencia operativa:
  - `batch_jobs`, `predictions`, `policy_history`, `audit_events`, `reports`, `drift_runs`, etc.
- Dashboard y analitica:
  - Resumen operativo y casos prioritarios
  - Endpoints de analytics para evolucion, distribucion, clasificacion e importancia de variables
- Informes reales:
  - Generacion JSON/CSV (`POST /reports`)
  - Listado, detalle y descarga (`GET /reports`, `GET /reports/{id}`, `GET /reports/{id}/download`)

## Stack tecnologico

- Frontend: React, Vite, React Router, CSS
- Backend: FastAPI, Pydantic, SQLAlchemy, Alembic
- Base de datos: PostgreSQL
- ML: scikit-learn, joblib, numpy, pandas
- Auth: JWT (PyJWT), passlib+bcrypt
- Testing: pytest
- Contenedores: Docker, Docker Compose

## Arquitectura resumida

```text
Usuario
  -> Frontend (React/Vite)
  -> Backend API (FastAPI)
  -> Modelo ML + Politica de revision
  -> PostgreSQL (estado operativo e historico)
  -> Respuesta al frontend
```

## Autenticacion y roles

- El backend emite tokens JWT en login/registro.
- El frontend guarda token y usuario en `localStorage` y envia `Authorization: Bearer <token>` en llamadas API.
- Rutas internas del frontend estan protegidas (`/dashboard`, `/analysis`, `/reports`, `/config`).
- La politica de revision solo puede modificarse con usuario `admin`.

Nota para TFG/demo:
- Actualmente el formulario de registro permite elegir rol (`analyst` o `admin`) para facilitar demostraciones academicas.
- En un entorno productivo, la asignacion de administradores debe hacerse mediante un proceso controlado (no desde auto-registro publico).

## Endpoints principales

- Salud: `GET /health`
- Auth:
  - `POST /auth/register`
  - `POST /auth/login`
  - `GET /auth/me`
- Politica:
  - `GET /policy`
  - `PUT /policy` (solo admin)
  - `GET /policy/history`
- Prediccion:
  - `POST /predict`
  - `POST /predict_batch`
- Batch jobs:
  - `POST /batch-jobs/upload`
  - `GET /batch-jobs`
  - `GET /batch-jobs/{batch_job_id}`
  - `GET /batch-jobs/{batch_job_id}/predictions`
  - `GET /batch-jobs/{batch_job_id}/download`
- Predicciones:
  - `GET /predictions`
  - `GET /predictions/{prediction_id}`
- Dashboard:
  - `GET /dashboard/summary`
  - `GET /dashboard/priority-cases`
- Analytics:
  - `GET /analytics/fraud-evolution`
  - `GET /analytics/risk-distribution`
  - `GET /analytics/classification-summary`
  - `GET /analytics/variable-importance`
- Informes:
  - `POST /reports`
  - `GET /reports`
  - `GET /reports/{report_id}`
  - `GET /reports/{report_id}/download`
- Otros:
  - `GET /audit-events`
  - `GET /model-versions`
  - `GET /model-versions/active`
  - `GET /drift-runs`

## Estructura del proyecto

```text
tfg-fraude-ml next/
|-- backend/
|   |-- alembic/
|   |-- artifacts/
|   |-- data/
|   |-- dev/
|   |-- logs/
|   |-- scripts/
|   |-- src/
|   |   |-- api/
|   |   |-- core/
|   |   |-- db/
|   |   |-- repositories/
|   |   |-- schemas/
|   |   |-- services/
|   |   |-- models/
|   |   `-- evaluation/
|   `-- tests/
|-- frontend/
|   |-- src/
|   |-- Dockerfile
|   `-- README.md
|-- docs/
|   `-- arquitectura.md
|-- docker-compose.yml
`-- README.md
```

## Instalacion local (sin Docker para app completa)

### 1) Base de datos

Desde la raiz:

```powershell
docker compose up -d postgres
```

### 2) Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
.\dev\db_migrate.ps1
.\dev\db_init.ps1
.\dev\run_api.ps1
```

API: `http://127.0.0.1:8000`  
Swagger: `http://127.0.0.1:8000/docs`

### 3) Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

## Ejecucion con Docker

```powershell
docker compose up --build
```

Flujo recomendado de inicializacion DB (primera vez o tras reset):

```powershell
docker compose up -d postgres
docker compose run --rm backend alembic upgrade head
docker compose run --rm backend python scripts/init_db.py
docker compose up -d backend frontend
```

URLs:
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432`

## Variables de entorno

### Backend (`backend/.env.example`)

- `DATABASE_URL`
- `MODEL_PATH`
- `MODEL_METADATA_PATH`
- `REVIEW_POLICY_PATH`
- `PREDICTIONS_LOG_PATH`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`

### Frontend (`frontend/.env.example`)

- `VITE_API_URL` (ejemplo local: `http://127.0.0.1:8000`)

## Artefactos ML y configuracion

- Modelo: `backend/artifacts/fraud_model.joblib`
- Metadata: `backend/artifacts/fraud_model_metadata.json`
- Politica fallback: `backend/review_policy.json`
- Compatibilidad de logs: `backend/logs/predictions.jsonl`

## Tests

Backend:

```powershell
cd backend
.\.venv\Scripts\python -m pytest -q -p no:cacheprovider -W default
```

Estado validado reciente: `54 passed`.

## Estado actual

- Backend productivo para demo academica:
  - Persistencia real con PostgreSQL
  - Auth JWT funcional
  - Roles basicos y autorizacion en operacion sensible de politica
  - Endpoints de dashboard, analytics, informes y batch CSV
- Frontend integrado con API real en login/register, dashboard, analisis, configuracion e informes.
- Se mantienen fallbacks visuales a mocks ante caidas de API para mejorar resiliencia en demo.

## Limitaciones conocidas y mejoras futuras

- Asignacion de rol `admin` desde registro pensada para demo; en produccion debe restringirse.
- No hay refresh tokens ni recuperacion de password.
- No hay RBAC granular por recurso; autorizacion inicial aplicada solo a `PUT /policy`.
- Falta hardening de seguridad para despliegue productivo (secretos, rotacion, etc.).
- La documentacion de algunas pantallas puede seguir evolucionando con nuevas fases del TFG.
