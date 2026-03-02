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

## Előfeltételek

- Docker
- Kubernetes cluster + `kubectl`

Támogatott tipikus környezetek:
- **Docker Desktop Kubernetes** (Windows alatt egyszerű)
- **Minikube**

## 1) Image build

A workspace gyökerében:

```bash
docker build -t photowebapp-backend:latest ./backend
docker build -t photowebapp-frontend:latest ./frontend
```

### Minikube esetén

Minikube Docker daemonba buildelj, különben a cluster nem fogja látni a lokális image-eket.

PowerShell:

```powershell
minikube -p minikube docker-env | Invoke-Expression
docker build -t photowebapp-backend:latest ./backend
docker build -t photowebapp-frontend:latest ./frontend
```

> Ha a `minikube` parancs nem található, akkor vagy nincs telepítve, vagy nincs benne a PATH-ban.

## 2) Kubernetes deploy

```bash
kubectl apply -f k8s/photowebapp.yaml
kubectl get pods -n photowebapp
```

Elvárt: 3 pod fut (`frontend`, `backend`, `mysql`).

## 3) Elérés

A frontend `NodePort` szolgáltatással érhető el (`30080`):

- Docker Desktop Kubernetes: `http://localhost:30080`
- Minikube:

```bash
minikube service frontend -n photowebapp --url
```

## Frissítés kódmódosítás után

Példa frontend módosításra:

```bash
docker build -t photowebapp-frontend:latest ./frontend
kubectl rollout restart deployment/frontend -n photowebapp
kubectl rollout status deployment/frontend -n photowebapp
```

Backend módosításnál ugyanez `photowebapp-backend` image-re és `deployment/backend`-re.

## Hibaelhárítás

- **`minikube: command not found`**
	- Használj Docker Desktop Kubernetest, vagy telepítsd a Minikube-ot.
- **Image nem frissül deploy után**
	- Buildelj újra, majd futtasd a `kubectl rollout restart ...` parancsot.
- **Podok állapotának ellenőrzése**

```bash
kubectl get pods -n photowebapp
kubectl describe pod <pod-nev> -n photowebapp
kubectl logs <pod-nev> -n photowebapp
```

## Megjegyzések

- A jelenlegi manifest `emptyDir` volume-okat használ (`mysql` adat és feltöltött képek), így pod újraindításkor adatvesztés lehet.
- A frontend-képmegjelenítés frontend proxy route-on keresztül történik, így clusteren belül működik akkor is, ha a backend csak belső service címen érhető el.

## Skálázás

```bash
kubectl scale deployment frontend --replicas=3 -n photowebapp
kubectl scale deployment backend --replicas=3 -n photowebapp
```
