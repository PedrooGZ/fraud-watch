# Backend - Fraud Watch

Backend API y capa de negocio de Fraud Watch.
Implementado con FastAPI, SQLAlchemy y PostgreSQL, con autenticacion JWT y persistencia operativa.

## Stack

- Python 3.11
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- scikit-learn / joblib
- PyJWT
- passlib[bcrypt]
- pytest

## Estructura

```text
backend/
|-- alembic/
|-- artifacts/
|-- data/
|-- dev/
|-- logs/
|-- scripts/
|-- src/
|   |-- api/
|   |-- core/
|   |-- db/
|   |-- repositories/
|   |-- schemas/
|   |-- services/
|   |-- models/
|   `-- evaluation/
|-- tests/
|-- .env.example
|-- alembic.ini
`-- requirements.txt
```

## Variables de entorno

Definidas en `backend/.env.example`:

- `APP_ENV`
- `DATABASE_URL`
- `MODEL_PATH`
- `MODEL_METADATA_PATH`
- `REVIEW_POLICY_PATH`
- `PREDICTIONS_LOG_PATH`
- `CORS_ALLOW_ORIGINS`
- `ROOT_PATH`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`

Para despliegue con Docker Compose en VM, usa `backend/.env.deploy.example` como plantilla.

Notas:
- `DATABASE_URL` debe apuntar a PostgreSQL Flexible Server con `sslmode=require`.
- `ROOT_PATH` se deja vacio por defecto. Solo usalo si publicas backend bajo prefijo (ejemplo: `/api`).

## Arranque local (PowerShell)

1. Levantar PostgreSQL desde raiz:

```powershell
docker compose up -d postgres
```

2. Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
.\dev\db_migrate.ps1
.\dev\db_init.ps1
.\dev\run_api.ps1
```

API local: `http://127.0.0.1:8000`  
Swagger: `http://127.0.0.1:8000/docs`

## Despliegue en VM con Docker Compose

Este backend se despliega con el compose de raiz `docker-compose.deploy.yml`.
En ese flujo se usa PostgreSQL externo (Azure Flexible Server) y no se levanta contenedor `postgres`.

Pasos minimos:

```powershell
# desde raiz del proyecto
Copy-Item backend/.env.deploy.example backend/.env.deploy
# editar backend/.env.deploy con DATABASE_URL y JWT_SECRET_KEY reales

docker compose -f docker-compose.deploy.yml --profile init up db-init
docker compose -f docker-compose.deploy.yml up -d --build
```

Equivalente Linux:

```bash
cp backend/.env.deploy.example backend/.env.deploy
# editar backend/.env.deploy con DATABASE_URL y JWT_SECRET_KEY reales

docker compose -f docker-compose.deploy.yml --profile init up db-init
docker compose -f docker-compose.deploy.yml up -d --build
```

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
  - `GET /predictions`
  - `GET /predictions/{prediction_id}`
  - `GET /audit-events`
  - `GET /model-versions`
  - `GET /model-versions/active`
  - `GET /drift-runs`

## Auth y roles

- Registro/login reales con JWT.
- Roles soportados: `analyst`, `admin`.
- Autorizacion activa actualmente:
  - `PUT /policy` requiere token valido y rol `admin`.

Nota demo academica:
- El registro permite seleccionar rol para facilitar pruebas del TFG.
- En entorno productivo, la asignacion de `admin` debe estar restringida.

## Persistencia

Tablas operativas:

- `users`
- `model_versions`
- `policies`
- `policy_history`
- `batch_jobs`
- `predictions`
- `reports`
- `drift_runs`
- `audit_events`

Compatibilidad por archivo:

- `review_policy.json` (fallback de politica)
- `logs/predictions.jsonl` (traza historica)

## Artefactos ML

- Modelo: `artifacts/fraud_model.joblib`
- Metadata: `artifacts/fraud_model_metadata.json`
- Referencia drift: `artifacts/ref_scores.npy`

## Tests

```powershell
cd backend
.\.venv\Scripts\python -m pytest -q -p no:cacheprovider -W default
```
