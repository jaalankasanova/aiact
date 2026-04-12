from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import sqlite3
import os
import json
import uuid
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import stripe
from kysymykset import luokittele_riski, laske_compliance_pisteet, TOIMIALAT, VAATIMUKSET, VAATIMUKSET_RAJATTU

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# .env lataus
env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, "templates"),
            static_folder=os.path.join(BASE_DIR, "static"))

app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-vaihda-tuotannossa")
app.permanent_session_lifetime = timedelta(hours=8)

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET  = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_ID        = os.environ.get("STRIPE_PRICE_ID", "")

DB_PATH = os.path.join(BASE_DIR, "aiact.db")


# ── Tietokanta ─────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS kayttajat (
            id          TEXT PRIMARY KEY,
            email       TEXT UNIQUE NOT NULL,
            salasana    TEXT NOT NULL,
            yritys      TEXT NOT NULL,
            ytunnus     TEXT,
            koko        TEXT,
            toimiala    TEXT,
            stripe_id   TEXT,
            tilaaja     INTEGER DEFAULT 0,
            tilaus_paattyy TEXT,
            luotu       TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS jarjestelmat (
            id          TEXT PRIMARY KEY,
            kayttaja_id TEXT NOT NULL,
            nimi        TEXT NOT NULL,
            kuvaus      TEXT,
            vastaukset  TEXT,
            riski_taso  TEXT,
            riski_data  TEXT,
            luotu       TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (kayttaja_id) REFERENCES kayttajat(id)
        );
        """)


# ── Auth-apufunktiot ───────────────────────────────────────────────────────────

def kirjautunut():
    return session.get("kayttaja_id") is not None


@app.context_processor
def inject_kirjautunut():
    return {"kirjautunut": kirjautunut()}


def vaadi_kirjautuminen(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not kirjautunut():
            return redirect(url_for("kirjaudu"))
        return f(*args, **kwargs)
    return wrapper


def vaadi_tilaus(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not kirjautunut():
            return redirect(url_for("kirjaudu"))
        with get_db() as db:
            k = db.execute("SELECT tilaaja FROM kayttajat WHERE id=?",
                           [session["kayttaja_id"]]).fetchone()
        if not k or not k["tilaaja"]:
            flash("Tämä ominaisuus vaatii aktiivisen tilauksen.", "warning")
            return redirect(url_for("tilaus"))
        return f(*args, **kwargs)
    return wrapper


# ── Reitit ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    paivat_jaljella = (datetime(2026, 8, 2) - datetime.now()).days
    return render_template("index.html", paivat_jaljella=paivat_jaljella)


@app.route("/rekisteri", methods=["GET", "POST"])
def rekisteri():
    if request.method == "POST":
        email   = request.form.get("email", "").strip().lower()
        salasana = request.form.get("salasana", "")
        yritys  = request.form.get("yritys", "").strip()
        ytunnus = request.form.get("ytunnus", "").strip()
        koko    = request.form.get("koko", "")

        if not email or not salasana or not yritys:
            flash("Täytä kaikki pakolliset kentät.", "error")
            return render_template("rekisteri.html")

        with get_db() as db:
            olemassa = db.execute("SELECT id FROM kayttajat WHERE email=?", [email]).fetchone()
            if olemassa:
                flash("Sähköpostiosoite on jo käytössä.", "error")
                return render_template("rekisteri.html")

            kid = str(uuid.uuid4())
            db.execute(
                "INSERT INTO kayttajat (id,email,salasana,yritys,ytunnus,koko) VALUES (?,?,?,?,?,?)",
                [kid, email, generate_password_hash(salasana), yritys, ytunnus, koko]
            )

        session.permanent = True
        session["kayttaja_id"] = kid
        session["yritys"] = yritys
        flash("Tervetuloa! Aloita kartoittamalla AI-järjestelmänne.", "success")
        return redirect(url_for("dashboard"))

    return render_template("rekisteri.html")


@app.route("/kirjaudu", methods=["GET", "POST"])
def kirjaudu():
    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        salasana = request.form.get("salasana", "")

        with get_db() as db:
            k = db.execute("SELECT * FROM kayttajat WHERE email=?", [email]).fetchone()

        if not k or not check_password_hash(k["salasana"], salasana):
            flash("Väärä sähköposti tai salasana.", "error")
            return render_template("kirjaudu.html")

        session.permanent = True
        session["kayttaja_id"] = k["id"]
        session["yritys"] = k["yritys"]
        return redirect(url_for("dashboard"))

    return render_template("kirjaudu.html")


@app.route("/kirjaudu-ulos")
def kirjaudu_ulos():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
@vaadi_kirjautuminen
def dashboard():
    kid = session["kayttaja_id"]
    with get_db() as db:
        kayttaja = db.execute("SELECT * FROM kayttajat WHERE id=?", [kid]).fetchone()
        jarjestelmat = db.execute(
            "SELECT * FROM jarjestelmat WHERE kayttaja_id=? ORDER BY luotu DESC", [kid]
        ).fetchall()

    # Rakenna jarjestelmat-lista riskidatoineen
    js_lista = []
    for j in jarjestelmat:
        riski_data = json.loads(j["riski_data"]) if j["riski_data"] else {}
        js_lista.append({"db": j, "riski": riski_data})

    yhteenveto = laske_compliance_pisteet(js_lista)
    paivat_jaljella = (datetime(2026, 8, 2) - datetime.now()).days

    return render_template("dashboard.html",
                           kayttaja=kayttaja,
                           jarjestelmat=js_lista,
                           yhteenveto=yhteenveto,
                           paivat_jaljella=paivat_jaljella,
                           tilaaja=kayttaja["tilaaja"])


# ── Kartoituslomake ────────────────────────────────────────────────────────────

@app.route("/kartoitus/uusi", methods=["GET", "POST"])
@vaadi_kirjautuminen
def uusi_jarjestelma():
    if request.method == "POST":
        nimi    = request.form.get("nimi", "").strip()
        kuvaus  = request.form.get("kuvaus", "").strip()
        toimiala = request.form.get("toimiala", "muu")

        if not nimi:
            flash("Anna järjestelmälle nimi.", "error")
            return render_template("kartoitus_1.html", toimialat=TOIMIALAT)

        # Tallenna väliaikaisesti sessioon
        session["kartoitus"] = {
            "nimi": nimi,
            "kuvaus": kuvaus,
            "toimiala": toimiala,
        }
        return redirect(url_for("kartoitus_2"))

    return render_template("kartoitus_1.html", toimialat=TOIMIALAT)


@app.route("/kartoitus/ominaisuudet", methods=["GET", "POST"])
@vaadi_kirjautuminen
def kartoitus_2():
    if "kartoitus" not in session:
        return redirect(url_for("uusi_jarjestelma"))

    if request.method == "POST":
        k = session["kartoitus"]
        k.update({
            "autonominen":       request.form.get("autonominen") == "on",
            "biometria":         request.form.get("biometria") == "on",
            "kohdistuu_henkiloihin": request.form.get("kohdistuu_henkiloihin") == "on",
            "chatbot":           request.form.get("chatbot") == "on",
            "generoi_sisaltoa":  request.form.get("generoi_sisaltoa") == "on",
            "kielletty":         request.form.get("kielletty") == "on",
        })
        session["kartoitus"] = k
        return redirect(url_for("kartoitus_3"))

    return render_template("kartoitus_2.html", kartoitus=session["kartoitus"])


@app.route("/kartoitus/nykytila", methods=["GET", "POST"])
@vaadi_kirjautuminen
def kartoitus_3():
    if "kartoitus" not in session:
        return redirect(url_for("uusi_jarjestelma"))

    if request.method == "POST":
        k = session["kartoitus"]
        # Compliance-nykytila
        for v in VAATIMUKSET + VAATIMUKSET_RAJATTU:
            k[v["id"]] = request.form.get(v["id"]) == "on"
        session["kartoitus"] = k

        # Laske riski
        riski = luokittele_riski(k)

        # Tallenna tietokantaan
        jid = str(uuid.uuid4())
        with get_db() as db:
            db.execute(
                """INSERT INTO jarjestelmat
                   (id, kayttaja_id, nimi, kuvaus, vastaukset, riski_taso, riski_data)
                   VALUES (?,?,?,?,?,?,?)""",
                [jid, session["kayttaja_id"], k["nimi"], k.get("kuvaus", ""),
                 json.dumps(k), riski["taso"], json.dumps(riski)]
            )

        session.pop("kartoitus", None)
        flash("Järjestelmä kartoitettu onnistuneesti.", "success")
        return redirect(url_for("tulos", jid=jid))

    # Näytä vain relevantit vaatimukset esikatselmuksen perusteella
    k = session["kartoitus"]
    riski_esikatselu = luokittele_riski(k)
    return render_template("kartoitus_3.html",
                           kartoitus=k,
                           riski_esikatselu=riski_esikatselu,
                           vaatimukset=VAATIMUKSET,
                           vaatimukset_rajattu=VAATIMUKSET_RAJATTU)


@app.route("/tulos/<jid>")
@vaadi_kirjautuminen
def tulos(jid):
    with get_db() as db:
        j = db.execute(
            "SELECT * FROM jarjestelmat WHERE id=? AND kayttaja_id=?",
            [jid, session["kayttaja_id"]]
        ).fetchone()

    if not j:
        flash("Järjestelmää ei löydy.", "error")
        return redirect(url_for("dashboard"))

    riski = json.loads(j["riski_data"])
    vastaukset = json.loads(j["vastaukset"]) if j["vastaukset"] else {}
    paivat_jaljella = (datetime(2026, 8, 2) - datetime.now()).days

    with get_db() as db:
        k = db.execute("SELECT tilaaja FROM kayttajat WHERE id=?", [session["kayttaja_id"]]).fetchone()
    return render_template("tulos.html",
                           jarjestelma=j,
                           riski=riski,
                           vastaukset=vastaukset,
                           paivat_jaljella=paivat_jaljella,
                           tilaaja=k["tilaaja"] if k else False)


@app.route("/jarjestelma/<jid>/poista", methods=["POST"])
@vaadi_kirjautuminen
def poista_jarjestelma(jid):
    with get_db() as db:
        db.execute("DELETE FROM jarjestelmat WHERE id=? AND kayttaja_id=?",
                   [jid, session["kayttaja_id"]])
    flash("Järjestelmä poistettu.", "success")
    return redirect(url_for("dashboard"))


# ── Stripe-tilaus ──────────────────────────────────────────────────────────────

@app.route("/tilaus")
@vaadi_kirjautuminen
def tilaus():
    return render_template("tilaus.html",
                           stripe_pk=STRIPE_PUBLISHABLE_KEY,
                           hinta="49")


@app.route("/tilaus/checkout", methods=["POST"])
@vaadi_kirjautuminen
def checkout():
    if not STRIPE_PRICE_ID:
        flash("Maksujärjestelmä ei ole vielä käytössä.", "warning")
        return redirect(url_for("tilaus"))

    kid = session["kayttaja_id"]
    with get_db() as db:
        k = db.execute("SELECT * FROM kayttajat WHERE id=?", [kid]).fetchone()

    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=k["email"],
            payment_method_types=["card"],
            line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
            mode="subscription",
            success_url=request.host_url + "tilaus/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.host_url + "tilaus",
            metadata={"kayttaja_id": kid},
        )
        return redirect(checkout_session.url)
    except Exception as e:
        flash("Maksun käynnistäminen epäonnistui.", "error")
        return redirect(url_for("tilaus"))


@app.route("/tilaus/success")
@vaadi_kirjautuminen
def tilaus_success():
    sid = request.args.get("session_id")
    if sid and STRIPE_PRICE_ID:
        try:
            cs = stripe.checkout.Session.retrieve(sid)
            if cs.payment_status == "paid":
                kid = session["kayttaja_id"]
                with get_db() as db:
                    db.execute("UPDATE kayttajat SET tilaaja=1, stripe_id=? WHERE id=?",
                               [cs.customer, kid])
        except Exception:
            pass
    flash("Tilaus aktivoitu! Tervetuloa.", "success")
    return redirect(url_for("dashboard"))


@app.route("/stripe/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.get_data()
    sig = request.headers.get("Stripe-Signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except Exception:
        return "", 400

    if event["type"] == "customer.subscription.deleted":
        customer_id = event["data"]["object"]["customer"]
        with get_db() as db:
            db.execute("UPDATE kayttajat SET tilaaja=0 WHERE stripe_id=?", [customer_id])

    return "", 200


# ── PDF-raportti ───────────────────────────────────────────────────────────────

@app.route("/raportti/<jid>.pdf")
@vaadi_tilaus
def pdf_raportti(jid):
    try:
        from weasyprint import HTML
    except ImportError:
        flash("PDF-vienti ei ole käytettävissä tässä ympäristössä.", "warning")
        return redirect(url_for("tulos", jid=jid))

    with get_db() as db:
        j = db.execute(
            "SELECT * FROM jarjestelmat WHERE id=? AND kayttaja_id=?",
            [jid, session["kayttaja_id"]]
        ).fetchone()
        kayttaja = db.execute("SELECT * FROM kayttajat WHERE id=?",
                              [session["kayttaja_id"]]).fetchone()

    if not j:
        return redirect(url_for("dashboard"))

    riski = json.loads(j["riski_data"])
    html = render_template("raportti_pdf.html",
                           jarjestelma=j,
                           riski=riski,
                           kayttaja=kayttaja,
                           pvm=datetime.now().strftime("%d.%m.%Y"))

    from flask import Response
    pdf = HTML(string=html).write_pdf()
    return Response(pdf, mimetype="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=aiact-raportti-{j['nimi']}.pdf"})


@app.route("/tietosuoja")
def tietosuoja():
    return render_template("tietosuoja.html")


# ── Käynnistys ─────────────────────────────────────────────────────────────────

init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5001)
