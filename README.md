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

---

## OKD / OpenShift PaaS (Import from Git + automatikus build GitHub push-ra)

Ebben a módban az alkalmazás közvetlenül GitHub repóból buildelődik OpenShiftben.
Javasolt folyamat: **MySQL külön manifestből**, a **frontend/backend pedig OKD UI-ból `Import from Git`**.

### 1) Projekt létrehozás és MySQL deploy

Kizárólag UI-val:

1. OpenShift Console → **Administrator** nézet.
2. **Home → Projects → Create Project**: név legyen `photowebapp`.
3. **+Add → Import YAML** és illeszd be a [openshift/mysql.yaml](openshift/mysql.yaml) teljes tartalmát.
4. Kattints **Create**.
5. **Workloads → Pods** oldalon ellenőrizd, hogy a `mysql` pod fut.

### 2) Backend hozzáadása OKD-ben (`Import from Git`)

Developer nézet → **+Add** → **Import from Git**

- Git Repo URL: a saját GitHub repository URL-ed
- Builder/Image strategy: **Dockerfile**
- Context Dir: `backend`
- Application name: `backend`
- Service port: `5001`
- Route: **kikapcsolva** (belső service elég)

Environment variables a backendhez:

- `DATABASE_URL=mysql+pymysql://photouser:photopass@mysql:3306/photowebapp`
- `SECRET_KEY` → `photowebapp-secrets` secretből (`SECRET_KEY` kulcs)
- `UPLOAD_FOLDER=/data/uploads`

### 3) Frontend hozzáadása OKD-ben (`Import from Git`)

Ugyanúgy **Import from Git**:

- Git Repo URL: ugyanaz a repository
- Builder/Image strategy: **Dockerfile**
- Context Dir: `frontend`
- Application name: `frontend`
- Service port: `5000`
- Route: **bekapcsolva** (ez lesz a publikus URL)

Environment variables a frontendhez:

- `BACKEND_URL=http://backend:5001`
- `FLASK_SECRET_KEY` → `photowebapp-secrets` secretből (`FLASK_SECRET_KEY` kulcs)

### 4) Automatikus build GitHub push-ra (Webhook)

Az `Import from Git` létrehoz egy BuildConfig-ot (`backend`, `frontend`).
Ehhez állíts be GitHub webhookot, így minden push után új build indul.

Webhook URL-ek kinyerése UI-ból:

1. **Administrator → Builds → BuildConfigs**.
2. Nyisd meg a `backend` BuildConfigot.
3. **Configuration / Webhooks** résznél másold ki a GitHub webhook URL-t.
4. Ugyanezt ismételd meg a `frontend` BuildConfignál.

GitHub repo → **Settings** → **Webhooks** → **Add webhook**:

- Payload URL: a fenti GitHub webhook URL (backend/frontendre külön)
- Content type: `application/json`
- Event: **Just the push event**

Ellenőrzés:

1. OpenShift UI-ban: **Administrator → Builds → Builds**
2. Itt látod, hogy push után új `backend` és `frontend` build indul.
3. Build részletein belül a **Logs** fülön követhető a build folyamata.

Ha pusholsz a GitHub repóba, az OpenShift automatikusan buildel és redeployol.
