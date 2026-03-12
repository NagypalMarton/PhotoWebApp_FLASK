# OpenShift deployment leírás

## Sorrend és függőségek
- A MySQL deployment és service indul el elsőként (mysql.yaml).
- A backend deployment (backend.yaml) egy initContainer-t használ, ami megvárja, hogy a MySQL service elérhető legyen (TCP 3306).
- A frontend deployment (frontend.yaml) egy initContainer-t használ, ami megvárja, hogy a backend service elérhető legyen (TCP 5001).

## Fájlok
- mysql.yaml: MySQL adatbázis és service
- backend.yaml: Backend deployment, initContainer-rel
- backend-service.yaml: Backend service
- frontend.yaml: Frontend deployment, initContainer-rel
- frontend-service.yaml: Frontend service
- photowebapp-build.yaml: ImageStream-ek és BuildConfig-ok (backend + frontend image build)

## Telepítés

### 1. ImageStream-ek és Build-ek létrehozása
```bash
oc apply -f openshift/photowebapp-build.yaml
# Backend image build elindítása
oc start-build photowebapp-backend-build --follow
# Frontend image build elindítása
oc start-build photowebapp-frontend-build --follow
```

### 2. MySQL deploy (Secret + PVC + Deployment + Service)
```bash
oc apply -f openshift/mysql.yaml
```

### 3. Backend deploy
```bash
oc apply -f openshift/backend.yaml
oc apply -f openshift/backend-service.yaml
```

### 4. Frontend deploy
```bash
oc apply -f openshift/frontend.yaml
oc apply -f openshift/frontend-service.yaml
```

## Miért "no revisions" / nincsenek podok?

Az OpenShift csak akkor hoz létre podot, ha az image **létezik** az internal registry-ben.
A `photowebapp-build.yaml`-ban lévő ImageStream-ek és BuildConfig-ok biztosítják ezt.

Az `image.openshift.io/triggers` annotation a Deployment-eken gondoskodik arról, hogy
ha az ImageStream-ben új image jelenik meg (build után), a pod automatikusan újraindul.

A sorrend garantált, a függőségek automatikusan kezelve vannak az initContainer-ek által.
