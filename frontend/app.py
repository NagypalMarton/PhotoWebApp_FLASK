import os

import requests
from flask import Flask, Response, flash, redirect, render_template, request, session, url_for


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "frontend-dev-secret")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5001")


def api_headers():
    token = session.get("token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def backend(path: str) -> str:
    return f"{BACKEND_URL}{path}"


@app.route("/")
def index():
    sort = request.args.get("sort", "date")
    try:
        response = requests.get(backend(f"/api/photos?sort={sort}"), timeout=10)
        photos = response.json().get("photos", []) if response.ok else []
    except requests.RequestException:
        photos = []
        flash("A backend jelenleg nem elérhető.", "danger")

    return render_template(
        "index.html",
        photos=photos,
        sort=sort,
        logged_in=bool(session.get("token")),
        username=session.get("username"),
    )


@app.route("/photo/<int:photo_id>")
def photo_view(photo_id: int):
    try:
        response = requests.get(backend(f"/api/photos/{photo_id}"), timeout=10)
        if not response.ok:
            flash("A kép nem található.", "warning")
            return redirect(url_for("index"))
        photo = response.json()
    except requests.RequestException:
        flash("A backend jelenleg nem elérhető.", "danger")
        return redirect(url_for("index"))

    image_url = url_for("photo_image_proxy", photo_id=photo_id)
    return render_template("photo.html", photo=photo, image_url=image_url)


@app.route("/photo/<int:photo_id>/image")
def photo_image_proxy(photo_id: int):
    try:
        response = requests.get(backend(f"/api/photos/{photo_id}/image"), timeout=20)
    except requests.RequestException:
        flash("A backend jelenleg nem elérhető.", "danger")
        return redirect(url_for("photo_view", photo_id=photo_id))

    if not response.ok:
        if response.status_code == 404:
            flash("A kép nem található.", "warning")
        else:
            flash("A kép betöltése sikertelen.", "danger")
        return redirect(url_for("photo_view", photo_id=photo_id))

    return Response(
        response.content,
        status=response.status_code,
        content_type=response.headers.get("Content-Type", "application/octet-stream"),
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        try:
            response = requests.post(
                backend("/api/register"),
                json={"username": username, "password": password},
                timeout=10,
            )
            if response.status_code == 201:
                flash("Sikeres regisztráció. Most jelentkezz be.", "success")
                return redirect(url_for("login"))
            flash(response.json().get("error", "Regisztráció sikertelen."), "danger")
        except requests.RequestException:
            flash("A backend jelenleg nem elérhető.", "danger")

    return render_template("auth.html", mode="register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        try:
            response = requests.post(
                backend("/api/login"),
                json={"username": username, "password": password},
                timeout=10,
            )
            if response.ok:
                body = response.json()
                session["token"] = body["token"]
                session["username"] = body["username"]
                flash("Sikeres bejelentkezés.", "success")
                return redirect(url_for("index"))
            flash(response.json().get("error", "Bejelentkezés sikertelen."), "danger")
        except requests.RequestException:
            flash("A backend jelenleg nem elérhető.", "danger")

    return render_template("auth.html", mode="login")


@app.route("/logout")
def logout():
    session.clear()
    flash("Sikeres kijelentkezés.", "info")
    return redirect(url_for("index"))


@app.route("/upload", methods=["POST"])
def upload():
    if "token" not in session:
        flash("A feltöltéshez bejelentkezés szükséges.", "warning")
        return redirect(url_for("login"))

    name = request.form.get("name", "").strip()
    photo = request.files.get("photo")

    if not name or len(name) > 40:
        flash("A kép neve kötelező és max 40 karakter lehet.", "danger")
        return redirect(url_for("index"))

    if not photo:
        flash("Válassz ki egy képet feltöltésre.", "danger")
        return redirect(url_for("index"))

    try:
        response = requests.post(
            backend("/api/photos"),
            headers=api_headers(),
            data={"name": name},
            files={"photo": (photo.filename, photo.stream, photo.mimetype)},
            timeout=20,
        )
        if response.status_code == 201:
            flash("Sikeres feltöltés.", "success")
        else:
            flash(response.json().get("error", "Feltöltés sikertelen."), "danger")
    except requests.RequestException:
        flash("A backend jelenleg nem elérhető.", "danger")

    return redirect(url_for("index"))


@app.route("/delete/<int:photo_id>", methods=["POST"])
def delete(photo_id: int):
    if "token" not in session:
        flash("A törléshez bejelentkezés szükséges.", "warning")
        return redirect(url_for("login"))

    try:
        response = requests.delete(
            backend(f"/api/photos/{photo_id}"), headers=api_headers(), timeout=10
        )
        if response.ok:
            flash("Kép törölve.", "success")
        else:
            flash(response.json().get("error", "Törlés sikertelen."), "danger")
    except requests.RequestException:
        flash("A backend jelenleg nem elérhető.", "danger")

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
