# PhotoWebApp (Flask + Bootstrap + MySQL + Kubernetes)

Többrétegű fényképalbum alkalmazás:
- **frontend** pod: Flask + Bootstrap UI
- **backend** pod: Flask REST API + üzleti logika
- **mysql** pod: MySQL adatbázis

## Megvalósított funkciók

- Felhasználókezelés: regisztráció, belépés, kilépés
- Fényképfeltöltés (csak bejelentkezve)
- Fényképtörlés (csak bejelentkezve, saját kép)
- Minden képhez név (max. 40 karakter) és feltöltési dátum
- Lista név vagy dátum szerinti rendezéssel
- Listaelemből részletes nézet (kép megjelenítése)

## Könyvtárstruktúra

- `frontend/` – UI szolgáltatás
- `backend/` – API szolgáltatás
- `k8s/photowebapp.yaml` – Kubernetes erőforrások

## Docker image build

A workspace gyökerében:

```bash
docker build -t photowebapp-backend:latest ./backend
docker build -t photowebapp-frontend:latest ./frontend
```

> Minikube esetén buildelj a minikube docker daemonba:
>
> ```bash
> minikube docker-env
> ```
>
> Windows PowerShell-ben:
>
> ```powershell
> minikube -p minikube docker-env | Invoke-Expression
> ```

## Kubernetes deploy

```bash
kubectl apply -f k8s/photowebapp.yaml
kubectl get pods -n photowebapp
```

Elvárt: 3 pod fut (`frontend`, `backend`, `mysql`).

## Elérés

A frontend `NodePort` szolgáltatással érhető el:
- port: `30080`

Például minikube-n:

```bash
minikube service frontend -n photowebapp --url
```

## Megjegyzés skálázhatóságról

A frontend és backend deployment replikaszáma növelhető:

```bash
kubectl scale deployment frontend --replicas=3 -n photowebapp
kubectl scale deployment backend --replicas=3 -n photowebapp
```
