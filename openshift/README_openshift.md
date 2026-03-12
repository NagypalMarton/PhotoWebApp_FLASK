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

## Telepítés
1. Először hozd létre a titkos adatokat és persistent volume-t (mysql.yaml).
2. Deploy MySQL-t.
3. Deploy backend-et (backend.yaml + backend-service.yaml).
4. Deploy frontend-et (frontend.yaml + frontend-service.yaml).

A sorrend garantált, a függőségek automatikusan kezelve vannak az initContainer-ek által.
