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
