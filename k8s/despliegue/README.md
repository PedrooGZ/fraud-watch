# Manifests de despliegue (adaptados desde Kubernetes-Apuntes)

Esta carpeta adapta estos 4 archivos del repo de referencia:

- `microdeployment.yaml` -> backend de Fraud Watch
- `microservice.yaml` -> Service `LoadBalancer` del backend
- `microfront-deployment.yaml` -> frontend de Fraud Watch
- `microfront-service.yaml` -> Service `LoadBalancer` del frontend

## Diferencias respecto a `k8s/` principal

- Aqui se sigue el estilo del repo de apuntes: manifiestos simples.
- No usa `Ingress`, `ConfigMap`, `Secret`, `PVC`, probes ni Job de migraciones.
- Se exponen backend y frontend directamente con `type: LoadBalancer`.

## Antes de aplicar

1. Reemplaza `YOUR_ACR_NAME` en `microdeployment.yaml` y `microfront-deployment.yaml`.
2. Reemplaza `DATABASE_URL` y `JWT_SECRET_KEY` en `microdeployment.yaml`.
3. Ajusta `CORS_ALLOW_ORIGINS` al dominio real del frontend.

## Aplicacion

```powershell
kubectl apply -f .\k8s\despliegue\namespace.yaml
kubectl apply -f .\k8s\despliegue\microdeployment.yaml
kubectl apply -f .\k8s\despliegue\microservice.yaml
kubectl apply -f .\k8s\despliegue\microfront-deployment.yaml
kubectl apply -f .\k8s\despliegue\microfront-service.yaml
```

## Inicializar base de datos (una vez)

```powershell
$POD = kubectl get pods -n fraud-watch -l app=backend -o jsonpath="{.items[0].metadata.name}"
kubectl exec -n fraud-watch $POD -- /bin/sh -c "alembic upgrade head && python scripts/init_db.py"
```

## Verificacion

```powershell
kubectl get pods -n fraud-watch
kubectl get svc -n fraud-watch
```

## Nota AKS

Con este enfoque tendras dos Services `LoadBalancer`. En AKS, cada Service de este tipo puede crear exposicion publica, asi que es mas simple para pruebas pero menos controlado y potencialmente mas costoso que la opcion con `Ingress`.
