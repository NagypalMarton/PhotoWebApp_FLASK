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
│   ├── backend.yaml        # OpenShift: PVC, Deployment, Service
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app.py              # Flask UI
│   ├── frontend.yaml       # OpenShift: Deployment, Service, Route
│   ├── Dockerfile
│   ├── requirements.txt
│   └── templates/          # Jinja2 sablonok
├── mysql/
│   ├── mysql.yaml          # OpenShift: Secret, PVC, Deployment, Service
│   └── Dockerfile          # OpenShift-kompatibilis MySQL image (UBI9 + mysql-server)
├── openshift/
│   └── photowebapp-build.yaml  # ImageStream-ek + BuildConfig-ok
└── k8s/
    └── photowebapp.yaml    # Lokális Kubernetes manifest (fejlesztéshez)
```

## Fejlesztői megjegyzések

A telepítés kizárólag az OpenShift webes konzolán keresztül történik, `oc` CLI nélkül.

### 1) Projekt létrehozás

1. OpenShift Console → **Administrator** nézet
2. **Home → Projects → Create Project**: név legyen `photowebapp`

### 2) Build infrastruktúra – ImageStream-ek és BuildConfig-ok

1. **+Add → Import YAML**
2. Illeszd be az [`openshift/photowebapp-build.yaml`](openshift/photowebapp-build.yaml) teljes tartalmát
3. Kattints **Create**
4. **Builds → BuildConfigs** – a `photowebapp-backend-build` és `photowebapp-frontend-build` BuildConfig-ok automatikusan elindulnak (ConfigChange trigger)
5. Várd meg, amíg mindkét build sikeresen befejezik (**Builds → Builds** → zöld pipa)

### 3) MySQL deploy

1. **+Add → Import YAML**
2. Illeszd be az [`mysql/mysql.yaml`](mysql/mysql.yaml) teljes tartalmát
3. Kattints **Create**
4. **Workloads → Pods** – ellenőrizd, hogy a `mysql` pod **Running** állapotú

### 4) Backend deploy

1. **+Add → Import YAML**
2. Illeszd be a [`backend/backend.yaml`](backend/backend.yaml) teljes tartalmát
3. Kattints **Create**
4. A Deployment az ImageStream trigger segítségével automatikusan frissül, amint a `photowebapp-backend:latest` kép elérhető

### 5) Frontend deploy

1. **+Add → Import YAML**
2. Illeszd be a [`frontend/frontend.yaml`](frontend/frontend.yaml) teljes tartalmát
3. Kattints **Create**
4. A Deployment az ImageStream trigger segítségével automatikusan frissül, amint a `photowebapp-frontend:latest` kép elérhető
5. **Networking → Routes** – a `frontend` route-on érhető el az alkalmazás (HTTPS)

### 6) Automatikus build GitHub push-ra (Webhook)

A `photowebapp-build.yaml`-ban lévő BuildConfig-ok GitHub webhook triggert tartalmaznak. A webhook beállításával minden `git push` után új build és automatikus redeployment indul.

**Webhook URL-ek kinyerése az OpenShift UI-ból:**

1. **Administrator → Builds → BuildConfigs**
2. Nyisd meg a `photowebapp-backend-build` BuildConfigot
3. **Configuration** fül → **Webhooks** szakasz → **GitHub** sor → **Copy URL with Secret**
4. Ismételd meg a `photowebapp-frontend-build` BuildConfiggal

**Webhook hozzáadása GitHub-on:**

1. GitHub repo → **Settings → Webhooks → Add webhook**
2. **Payload URL**: a másolt OpenShift webhook URL
3. **Content type**: `application/json`
4. **Trigger**: Just the push event
5. Mentés után: a zöld pipa jelzi a sikeres kapcsolatot

Ezután minden `git push` hatására az OpenShift automatikusan buildeli és redeployolja az érintett podokat.

## Megjegyzések

- A feltöltött képek PersistentVolumeClaim (`uploads-pvc`, 5Gi) volume-on tárolódnak a backendben – pod újraindítás esetén megmaradnak.
- A MySQL adatai PVC-n tárolódnak, így pod újraindítás esetén megmaradnak.
- A jelszavak a `mysql/mysql.yaml`-ban lévő `Secret`-ben találhatók – éles környezetben ezeket külső titkos kezelőből (pl. Vault) kellene betölteni.
- A `mysql/Dockerfile` most már egy Red Hat UBI9 alapú, OpenShift-kompatibilis MySQL image-et készít. Használható saját buildhez, ha nem a hivatalos MySQL image-t szeretnéd használni.

Hasznos linkek:
- [OpenShift Documentation - creating-images ](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html/images/creating-images)
- [OpenShift Documentation - building_applications](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html/building_applications/index)