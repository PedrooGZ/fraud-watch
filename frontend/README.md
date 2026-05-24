# Frontend - Fraud Watch

Frontend de Fraud Watch para operacion analitica de fraude.
Implementado con React + Vite, autenticacion real y consumo de API backend.

## Stack

- React
- Vite
- JavaScript
- React Router
- CSS propio

## Rutas

- `/` -> Splash
- `/login` -> Login
- `/register` -> Registro
- `/dashboard` -> Dashboard
- `/analysis` -> Analisis visual
- `/reports` -> Informes
- `/config` -> Configuracion

## Auth en frontend

- Estado de sesion en `AuthContext`.
- Token y usuario persistidos en `localStorage`.
- `Authorization: Bearer <token>` en llamadas API cuando hay token.
- Rutas internas protegidas (`dashboard`, `analysis`, `reports`, `config`).

## Integracion API

Cliente central: `src/services/api.js`

Comportamiento de `BASE_URL`:
- Usa `import.meta.env.VITE_API_URL` si esta definida.
- Si no esta definida, usa `/api` por defecto.

Incluye, entre otros:

- `register`, `login`, `getMe`
- `getDashboardSummary`, `getDashboardPriorityCases`
- `getPolicy`, `updatePolicy`, `getPolicyHistory`
- `createReport`, `downloadReport`
- `uploadBatchCsv`, `downloadBatchResults`
- endpoints de analytics y drift

## Roles en UI

- `analyst`: visualiza configuracion/historico.
- `admin`: puede editar y guardar politica.

## Fallbacks

La UI mantiene fallbacks a mocks en algunos bloques si la API falla, para no dejar pantallas en blanco durante demo.

## Instalacion y ejecucion

```powershell
cd frontend
npm install
npm run dev
```

Build:

```powershell
npm run build
```

## Variables de entorno

`frontend/.env.example`:

- `VITE_API_URL=http://127.0.0.1:8000`

En despliegue con Docker Compose/Kubernetes se recomienda `VITE_API_URL=/api`.

## Despliegue en VM con Docker Compose

El frontend se construye con `VITE_API_URL=/api` y se sirve en Nginx.
Nginx enruta `/api` al servicio backend (`http://backend:8000`) dentro de la red Docker.

Comandos (desde raiz):

```powershell
docker compose -f docker-compose.deploy.yml up -d --build frontend
```

URL esperada en despliegue:
- Frontend: `http://<IP-o-dominio-de-tu-VM>`

Si hay errores de API en navegador:
- Verifica que `backend` este `healthy` en `docker compose ps`.
- Verifica que `CORS_ALLOW_ORIGINS` del backend incluya el dominio final del frontend.

## Estructura principal

```text
frontend/
|-- src/
|   |-- assets/
|   |-- components/
|   |-- context/
|   |-- data/
|   |-- hooks/
|   |-- pages/
|   |-- services/
|   |-- styles/
|   |-- utils/
|   |-- App.jsx
|   `-- main.jsx
|-- Dockerfile
|-- nginx.conf
`-- package.json
```
