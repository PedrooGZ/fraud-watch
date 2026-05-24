# 🛡️ Fraud Watch: Inteligencia Operativa para la Detección de Fraude

**Proyecto:** Fraud Watch  
**Ciclo formativo:** Desarrollo de Aplicaciones Multiplataforma (DAM)  
**Alumno:** Pedro Grimaldi Zambrano

\---

## Índice

* [Introducción](#introducción)
* [Funcionalidades del proyecto y tecnologías utilizadas](#funcionalidades-del-proyecto-y-tecnologías-utilizadas)
* [Guía de instalación](#guía-de-instalación)
* [Despliegue en Azure y Kubernetes](#despliegue-en-azure-y-kubernetes)
* [Guía de uso](#guía-de-uso)
* [Enlace a la documentación](#enlace-a-la-documentación)
* [Enlace a Figma de la interfaz](#enlace-a-figma-de-la-interfaz)
* [Conclusión](#conclusión)
* [Contribuciones, agradecimientos y referencias](#contribuciones-agradecimientos-y-referencias)
* [Licencias](#licencias)
* [Contacto](#contacto)

\---

## Introducción

**Fraud Watch** es una aplicación full-stack orientada a la detección operativa de fraude mediante técnicas de Machine Learning. El proyecto permite analizar transacciones, calcular su probabilidad de fraude, priorizar casos para revisión, consultar métricas, gestionar políticas de decisión y generar informes operativos.

La finalidad principal del proyecto es centralizar en una única plataforma procesos que normalmente están separados: el scoring de riesgo, la priorización de alertas, la revisión de casos, la trazabilidad mediante auditoría, el análisis visual y la generación de informes.

Este proyecto nace como una solución académica y práctica para aplicar conocimientos de desarrollo backend, frontend, bases de datos, despliegue, Machine Learning y diseño de interfaces en un entorno cercano a un caso real de análisis de riesgo.

### Justificación

La detección de fraude es un problema relevante en sectores como banca, comercio electrónico, seguros o cumplimiento normativo. En estos contextos no basta con que un modelo prediga un posible fraude: también es necesario convertir esas predicciones en una herramienta útil para los analistas.

Por ello, Fraud Watch no se limita a ejecutar un modelo de Machine Learning, sino que incorpora funcionalidades de gestión, visualización, configuración y reporting.

### Objetivos

Los principales objetivos del proyecto son:

* Desarrollar una aplicación completa con backend, frontend y base de datos.
* Integrar un modelo de Machine Learning para scoring de transacciones.
* Permitir la predicción individual y por lotes mediante archivos CSV.
* Priorizar casos de mayor riesgo para su revisión.
* Registrar auditoría y trazabilidad de acciones relevantes.
* Visualizar métricas, evolución de alertas, distribución de riesgo y drift.
* Generar informes en formatos estructurados.
* Aplicar buenas prácticas de organización, documentación y despliegue.

### Motivación

La motivación del proyecto es construir una solución realista que combine desarrollo de software y análisis inteligente de datos. Fraud Watch permite trabajar con tecnologías actuales y demostrar competencias tanto en programación como en diseño de arquitectura, integración de servicios y presentación de información útil para el usuario final.

\---

## Funcionalidades del proyecto y tecnologías utilizadas

### Funcionalidades principales

#### Dashboard operativo

El dashboard muestra una visión general del estado del sistema, incluyendo:

* Métricas agregadas del sistema.
* Casos prioritarios para revisión.
* Lotes de análisis recientes.
* Eventos recientes de auditoría.
* Subida de archivos CSV para análisis de transacciones.
* Descarga de resultados de lotes procesados.

Endpoints principales relacionados:

* `GET /dashboard/summary`
* `GET /dashboard/priority-cases`
* `GET /batch-jobs`
* `GET /audit-events`
* `POST /batch-jobs/upload`

#### Análisis visual

La sección de análisis visual permite interpretar el comportamiento del sistema mediante gráficas y métricas:

* Evolución de alertas.
* Distribución de riesgo.
* Clasificación operativa.
* Importancia de variables.
* Estado de drift mediante PSI.
* Información del modelo activo.

Endpoints principales relacionados:

* `GET /analytics/fraud-evolution`
* `GET /analytics/risk-distribution`
* `GET /analytics/classification-summary`
* `GET /analytics/variable-importance`
* `GET /drift-runs`
* `GET /model-versions/active`

#### Informes

El sistema permite generar informes operativos en distintos formatos:

* Generación de informes en JSON.
* Generación de informes en CSV.
* Historial de informes generados.
* Descarga de informes.
* Registro de auditoría asociado a descargas.

Endpoints principales relacionados:

* `POST /reports`
* `GET /reports`
* `GET /reports/{report\\\_id}`
* `GET /reports/{report\\\_id}/download`

Actualmente el formato PDF queda planteado como mejora futura.

#### Configuración de política

La página de configuración permite consultar y modificar la política de revisión del sistema:

* Umbral de revisión.
* Capacidad diaria de alertas.
* Modo de prioridad.
* Coste de errores.
* Motivo del cambio.
* Histórico de cambios de política.
* Auditoría de modificaciones.

Endpoints principales relacionados:

* `GET /policy`
* `PUT /policy`
* `GET /policy/history`

#### Autenticación y usuarios

El proyecto incorpora autenticación básica mediante JWT:

* Registro de usuario.
* Inicio de sesión.
* Consulta del usuario autenticado.
* Roles básicos: `analyst` y `admin`.
* Protección de rutas internas en frontend.

Endpoints principales relacionados:

* `POST /auth/register`
* `POST /auth/login`
* `GET /auth/me`

#### Backend y API

El backend permite:

* Predicción individual de transacciones.
* Predicción por lotes mediante JSON.
* Subida y procesamiento de archivos CSV.
* Persistencia de predicciones.
* Gestión de lotes.
* Auditoría.
* Configuración de política.
* Histórico de cambios.
* Versionado de modelos.
* Detección de drift.
* Generación y descarga de informes.

#### Base de datos

El sistema utiliza PostgreSQL y almacena información en tablas como:

* `users`: usuarios, roles, hash de contraseña y estado.
* `model\\\_versions`: versiones del modelo y métricas.
* `policies`: política activa.
* `policy\\\_history`: histórico de cambios de política.
* `batch\\\_jobs`: ejecuciones de análisis por lotes.
* `predictions`: predicciones individuales y por lote.
* `reports`: metadatos de informes generados.
* `drift\\\_runs`: ejecuciones de drift.
* `audit\\\_events`: eventos de auditoría.

\---

### Tecnologías utilizadas

#### Backend

* Python
* FastAPI
* SQLAlchemy
* Alembic
* PostgreSQL
* Pydantic
* PyJWT
* passlib / bcrypt
* python-dotenv
* pytest

#### Machine Learning y datos

* scikit-learn
* pandas
* numpy
* joblib
* shap
* matplotlib
* OpenML

#### Frontend

* React
* Vite
* React Router DOM
* CSS propio
* Fetch API centralizada en servicios

#### Base de datos

* PostgreSQL 16
* SQLAlchemy
* Alembic

#### DevOps y despliegue

* Docker
* Docker Compose
* Nginx para servir el frontend en contenedor
* Scripts PowerShell para tareas de desarrollo

\---

## Guía de instalación

El proyecto puede ejecutarse mediante Docker Compose o en local.

### Instalación con Docker

#### Requisitos previos

* Docker Desktop o Docker Engine.
* Docker Compose plugin.
* Git.

#### Pasos de instalación

Clonar el repositorio:

```bash
git clone <URL\\\_DEL\\\_REPOSITORIO>
cd <NOMBRE\\\_DEL\\\_REPOSITORIO>
```

Construir los contenedores:

```bash
docker compose build
```

Levantar PostgreSQL:

```bash
docker compose up -d postgres
```

Ejecutar migraciones:

```bash
docker compose run --rm backend alembic upgrade head
```

Inicializar la base de datos:

```bash
docker compose run --rm backend python scripts/init\\\_db.py
```

Levantar backend y frontend:

```bash
docker compose up -d backend frontend
```

También se puede usar el arranque directo si la base de datos ya está preparada:

```bash
docker compose up --build
```

#### URLs principales

* Frontend: `http://localhost:5173`
* Backend Swagger: `http://localhost:8000/docs`
* Health Check: `http://localhost:8000/health`
* PostgreSQL: `localhost:5432`

\---

### Instalación local

#### Backend

Entrar en la carpeta del backend:

```bash
cd backend
```

Crear entorno virtual:

```bash
python -m venv .venv
```

Activar entorno virtual en Windows:

```bash
.\\\\.venv\\\\Scripts\\\\activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Levantar PostgreSQL:

```bash
.\\\\dev\\\\db\\\_up.ps1
```

Ejecutar migraciones:

```bash
.\\\\dev\\\\db\\\_migrate.ps1
```

Inicializar base de datos:

```bash
.\\\\dev\\\\db\\\_init.ps1
```

Levantar API:

```bash
.\\\\dev\\\\run\\\_api.ps1
```

#### Frontend

Entrar en la carpeta del frontend:

```bash
cd frontend
```

Instalar dependencias:

```bash
npm install
```

Ejecutar en desarrollo:

```bash
npm run dev
```

Generar build de producción:

```bash
npm run build
```

### Variables de entorno

#### Backend

Variables principales disponibles en `backend/.env.example`:

|Variable|Descripción|
|-|-|
|`APP\\\_ENV`|Entorno de ejecución de la aplicación|
|`MODEL\\\_PATH`|Ruta del artefacto del modelo|
|`MODEL\\\_METADATA\\\_PATH`|Ruta del archivo de metadatos del modelo|
|`REVIEW\\\_POLICY\\\_PATH`|Ruta del JSON de política de revisión fallback|
|`PREDICTIONS\\\_LOG\\\_PATH`|Ruta del log JSONL de predicciones|
|`DATABASE\\\_URL`|URL de conexión a PostgreSQL|
|`JWT\\\_SECRET\\\_KEY`|Clave secreta para firmar tokens JWT|
|`JWT\\\_ALGORITHM`|Algoritmo utilizado para JWT|
|`JWT\\\_ACCESS\\\_TOKEN\\\_EXPIRE\\\_MINUTES`|Tiempo de expiración del token|

#### Frontend

Variable principal disponible en `frontend/.env.example`:

|Variable|Descripción|
|-|-|
|`VITE\\\_API\\\_URL`|URL base del backend|

\---

---

## Despliegue en Azure y Kubernetes

El proyecto también ha sido desplegado en un entorno cloud utilizando servicios de Microsoft Azure y Kubernetes.

Para el despliegue se ha utilizado una arquitectura basada en contenedores, separando el backend y el frontend en imágenes independientes. El backend se ejecuta como una API FastAPI en Kubernetes, mientras que el frontend se sirve mediante Nginx a partir del build de producción generado con Vite.

El despliegue incluye:

* Backend Python/FastAPI contenedorizado con Docker.
* Frontend React compilado y servido mediante Nginx.
* Imágenes publicadas en Azure Container Registry.
* Despliegue en Azure Kubernetes Service mediante manifiestos YAML.
* Base de datos PostgreSQL Flexible Server en Azure.
* Configuración de variables sensibles mediante Kubernetes Secrets.
* Exposición del frontend mediante un servicio `LoadBalancer`.
* Comunicación interna entre frontend y backend a través del servicio de Kubernetes.

La estructura de despliegue se encuentra documentada en la carpeta:

```text
k8s/despliegue/
```

## Guía de uso

### 1\. Acceso a la aplicación

El usuario puede acceder a la aplicación desde la URL del frontend:

```text
http://localhost:5173
```

Desde la pantalla inicial puede iniciar sesión o registrarse.

### 2\. Registro e inicio de sesión

El sistema permite crear una cuenta e iniciar sesión mediante autenticación JWT.

Los roles principales son:

* `analyst`: usuario analista, con permisos de consulta.
* `admin`: usuario administrador, con permisos de configuración.

### 3\. Dashboard

Una vez dentro de la aplicación, el dashboard permite consultar:

* Métricas principales.
* Casos prioritarios.
* Lotes recientes.
* Auditoría reciente.

También permite subir un archivo CSV para analizar transacciones.

### 4\. Subida de CSV

Para analizar un lote de transacciones:

1. Acceder al dashboard.
2. Pulsar en la opción de subir CSV.
3. Seleccionar el archivo.
4. Lanzar el análisis.
5. Revisar el resumen del lote.
6. Descargar los resultados si es necesario.

El CSV debe contener las columnas esperadas por el modelo, como:

```text
Time, V1, V2, ..., V28, Amount
```

### 5\. Casos prioritarios

El sistema muestra los casos que requieren revisión según la política configurada. Estos casos se ordenan y priorizan para facilitar el trabajo del analista.

### 6\. Análisis visual

Desde la sección de análisis visual se pueden consultar:

* Evolución de alertas.
* Distribución de riesgo.
* Clasificación operativa.
* Importancia de variables.
* Estado de drift.
* Modelo activo.

Esta sección ayuda a interpretar el comportamiento global del sistema.

### 7\. Informes

Desde la página de informes el usuario puede:

1. Seleccionar periodo.
2. Seleccionar formato.
3. Seleccionar nivel de detalle.
4. Seleccionar secciones.
5. Generar informe.
6. Descargar informe desde el historial.

Formatos soportados actualmente:

* JSON
* CSV

Formato pendiente como mejora futura:

* PDF

### 8\. Configuración

La página de configuración permite consultar la política activa del sistema.

Los usuarios con rol administrador pueden modificar:

* Umbral de revisión.
* Capacidad diaria.
* Modo de prioridad.
* Coste de errores.
* Motivo del cambio.

Cada modificación queda registrada en el histórico de política y en auditoría.

\---

## Enlace a la documentación

Por rellenar: enlace a la documentación del proyecto.

Ejemplo:

```markdown
\\\[Documentación del proyecto](Por rellenar)
```

Documentación existente en el repositorio:

* `README.md`
* `backend/README.md`
* `frontend/README.md`
* `docs/arquitectura.md`

\---

## Enlace a Figma de la interfaz

(https://www.figma.com/design/6eNPFC5WV4wKs86JL9ka4D/Untitled?node-id=30-426&t=WaqZA2giqZRMKSWl-0)

\---

## Conclusión

Fraud Watch es una plataforma completa para la detección operativa de fraude que integra backend, frontend, base de datos, Machine Learning, autenticación, auditoría, análisis visual, configuración de políticas e informes.

El proyecto demuestra cómo un modelo predictivo puede integrarse en una aplicación real para aportar valor a usuarios analistas o administradores. Más allá del cálculo de una probabilidad de fraude, el sistema permite organizar el trabajo, priorizar alertas, consultar métricas, modificar políticas y mantener trazabilidad.

Como resultado, se ha construido una solución modular, ampliable y preparada para futuras mejoras roles avanzados, informes PDF, monitorización avanzada y endurecimiento de seguridad.

\---

## Contribuciones, agradecimientos y referencias

### Contribuciones

Proyecto desarrollado por:

Pedro Grimaldi Zambrano

### Agradecimientos

Jorge Juan Muñoz Morera y Escuela Profesional Vedruna

### Referencias

Para el desarrollo del proyecto se han utilizado tecnologías, librerías y documentación oficial de:

* FastAPI
* SQLAlchemy
* Alembic
* PostgreSQL
* React
* Vite
* React Router DOM
* Docker
* Docker Compose
* Nginx
* scikit-learn
* pandas
* numpy
* PyJWT
* passlib
* pytest
* OpenML


\---

## Licencias


Este proyecto se distribuye bajo la licencia MIT. Consulta el archivo [LICENSE](./LICENSE) para más información.

Copyright (c) 2026 Pedro Grimaldi Zambrano.


\---

## Contacto

**Alumno:** Pedro Grimaldi Zambrano  
**Email:** pedro.grimaldi15@gmail.com  
**Centro educativo:** Escuela Profesional Vedruna  
**Ciclo:** Desarrollo de Aplicaciones Multiplataforma (DAM)  
