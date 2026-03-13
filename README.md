# Fényképalbum alkalmazás – Dokumentáció

## Választott környezet

Az alkalmazás **OpenShift PaaS** platformon fut (OKD). Az OpenShift automatikusan buildeli az image-eket a GitHub repóból, és kezeli a podok életciklusát.

## Architektúra – Rétegek és kapcsolatok

Az alkalmazás három egymástól független, konténerizált rétegből áll:

```
Böngésző
    │  HTTP :80
    ▼
┌─────────────────────────────┐
│  Frontend (Flask + Gunicorn) │  :5000
│  Jinja2 sablonok, Bootstrap  │
└─────────────┬───────────────┘
              │  HTTP REST :5001
              ▼
┌─────────────────────────────┐
│  Backend  (Flask + Gunicorn) │  :5001
│  REST API, üzleti logika     │
│  Fájl tárolás (/data/uploads)│
└─────────────┬───────────────┘
              │  TCP :3306 (SQLAlchemy / PyMySQL)
              ▼
┌─────────────────────────────┐
│  MySQL 8.0                   │  :3306
│  Felhasználók, kép metaadatok│
└─────────────────────────────┘
```

### Frontend réteg

- **Technológia:** Python 3.12, Flask 3.1, Gunicorn, Jinja2, Bootstrap 5.3
- **Feladat:** Szerver-oldali HTML renderelés, HTTP sablonvezérelt UI
- **Képmegjelenítés:** Proxy route-on keresztül (`/photo/<id>/image`) kéri le a képfájlt a backendtől, így a böngészőnek nem kell közvetlenül a backend service-t elérnie
- **Session kezelés:** A bejelentkezési token szerver oldali Flask session-ban tárolódik

### Backend réteg

- **Technológia:** Python 3.12, Flask 3.1, Gunicorn, Flask-SQLAlchemy, PyMySQL, Werkzeug, itsdangerous
- **Feladat:** REST API biztosítása a frontend számára, autentikáció, fájl feltöltés kezelése
- **Autentikáció:** Token-alapú (`itsdangerous.URLSafeTimedSerializer`), 24 órás lejárattal, `Authorization: Bearer <token>` fejléccel
- **Fájl tárolás:** `/data/uploads` könyvtár (OpenShift-kompatibilis: `chgrp -R 0 / chmod -R g+rwx`)

### Adatbázis réteg

- **Technológia:** MySQL 8.0
- **Táblák:**
  - `users`: `id`, `username` (max 80 kar., egyedi), `password_hash`
  - `photos`: `id`, `name` (max 40 kar.), `filename`, `uploaded_at`, `owner_id` (FK → users)
- **OpenShift:** PersistentVolumeClaim (5Gi) biztosítja az adatok megőrzését

## REST API végpontok

| Metódus | Végpont | Auth | Leírás |
|---|---|---|---|
| GET | `/api/health` | – | Állapot ellenőrzés |
| POST | `/api/register` | – | Regisztráció |
| POST | `/api/login` | – | Bejelentkezés, tokent ad vissza |
| GET | `/api/photos?sort=date\|name` | – | Fotók listázása |
| POST | `/api/photos` | ✅ | Fotó feltöltése |
| GET | `/api/photos/<id>` | – | Fotó metaadatai |
| DELETE | `/api/photos/<id>` | ✅ | Fotó törlése (csak saját) |
| GET | `/api/photos/<id>/image` | – | Képfájl visszaadása |

## Megvalósított funkciók

- Felhasználókezelés: regisztráció, belépés, kilépés
- Fényképfeltöltés (csak bejelentkezett felhasználónak)
- Fényképtörlés (csak bejelentkezett felhasználónak, csak saját kép)
- Minden képhez: név (max. 40 karakter) és feltöltési dátum (`ÉÉÉÉ-HH-NN ÓÓ:PP`)
- Lista névvagy dátum szerinti rendezéssel
- Listaelemre kattintva a kép részletes megjelenítése

## Skálázhatóság

Mindhárom réteg önállóan skálázható az OpenShift-ben:

```bash
oc scale deployment frontend --replicas=3
oc scale deployment backend  --replicas=3
```

A MySQL egy példányban fut PVC-vel, a frontend és backend állapotmentes – tetszőleges számú példányban futtatható.

## Könyvtárstruktúra

```
PhotoWebApp_FLASK/
├── backend/
│   ├── app.py              # Flask REST API
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app.py              # Flask UI
│   ├── Dockerfile
│   ├── requirements.txt
│   └── templates/          # Jinja2 sablonok
├── openshift/
│   ├── mysql.yaml          # MySQL: Secret, PVC, Deployment, Service
│   ├── backend.yaml        # Backend Deployment (initContainer: vár MySQL-re)
│   ├── backend-service.yaml
│   ├── frontend.yaml       # Frontend Deployment (initContainer: vár backend-re)
│   ├── frontend-service.yaml
│   └── photowebapp-build.yaml  # ImageStream-ek + BuildConfig-ok
└── k8s/
    └── photowebapp.yaml    # Lokális Kubernetes manifest (fejlesztéshez)
```

## Fejlesztői megjegyzések

A telepítés kizárólag az OpenShift webes konzolán keresztül történik, `oc` CLI nélkül.

### 1) Projekt létrehozás

1. OpenShift Console → **Administrator** nézet
2. **Home → Projects → Create Project**: név legyen `photowebapp`

### 2) MySQL deploy

1. **+Add → Import YAML**
2. Illeszd be az [`openshift/mysql.yaml`](openshift/mysql.yaml) teljes tartalmát
3. Kattints **Create**
4. **Workloads → Pods** – ellenőrizd, hogy a `mysql` pod **Running** állapotú

### 3) Backend hozzáadása – Import from Git

**Developer nézet → +Add → Import from Git**

| Beállítás | Érték |
|---|---|
| Git Repo URL | `https://github.com/NagypalMarton/PhotoWebApp_FLASK` |
| Image strategy | **Dockerfile** |
| Context Dir | `backend` |
| Application name | `backend` |
| Service port | `5001` |
| Route | **kikapcsolva** (belső service elég) |

Environment variables:

| Név | Érték |
|---|---|
| `DATABASE_URL` | `mysql+pymysql://photouser:photopass@mysql:3306/photowebapp` |
| `SECRET_KEY` | `photowebapp-secrets` secret → `SECRET_KEY` kulcs |
| `UPLOAD_FOLDER` | `/data/uploads` |

### 4) Frontend hozzáadása – Import from Git

**Developer nézet → +Add → Import from Git**

| Beállítás | Érték |
|---|---|
| Git Repo URL | `https://github.com/NagypalMarton/PhotoWebApp_FLASK` |
| Image strategy | **Dockerfile** |
| Context Dir | `frontend` |
| Application name | `frontend` |
| Service port | `5000` |
| Route | **bekapcsolva** (ez lesz a publikus URL) |

Environment variables:

| Név | Érték |
|---|---|
| `BACKEND_URL` | `http://backend:5001` |
| `FLASK_SECRET_KEY` | `photowebapp-secrets` secret → `FLASK_SECRET_KEY` kulcs |

### 5) Automatikus build GitHub push-ra (Webhook)

Az **Import from Git** automatikusan létrehoz egy BuildConfig-ot mindkét szolgáltatáshoz. A GitHub webhook beállításával minden `git push` után új build és automatikus redeployment indul.

**Webhook URL-ek kinyerése az OpenShift UI-ból:**

1. **Administrator → Builds → BuildConfigs**
2. Nyisd meg a `backend` BuildConfigot
3. **Configuration** fül → **Webhooks** szakasz → **GitHub** sor → **Copy URL with Secret**
4. Ismételd meg a `frontend` BuildConfiggal

**Webhook hozzáadása GitHub-on:**

1. GitHub repo → **Settings → Webhooks → Add webhook**
2. **Payload URL**: a másolt OpenShift webhook URL
3. **Content type**: `application/json`
4. **Trigger**: Just the push event
5. Mentés után: a zöld pipa jelzi a sikeres kapcsolatot

Ezután minden `git push` hatására az OpenShift automatikusan buildeli és redeployolja az érintett podokat.

## Megjegyzések

- A feltöltött képek `emptyDir` volume-on tárolódnak a backendben – pod újraindításkor elvesznek. Persistent tároláshoz `PersistentVolumeClaim` szükséges a backend `uploads` volume-jához is.
- A MySQL adatai PVC-n tárolódnak, így pod újraindítás esetén megmaradnak.
- A jelszavak a `mysql.yaml`-ban lévő `Secret`-ben találhatók – éles környezetben ezeket külső titkos kezelőből (pl. Vault) kellene betölteni.
