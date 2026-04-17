from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, Response
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import psycopg2
import psycopg2.extras
import os
import json
import uuid
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import stripe
from kysymykset import luokittele_riski, laske_compliance_pisteet, TOIMIALAT, VAATIMUKSET, VAATIMUKSET_DEPLOYER, VAATIMUKSET_RAJATTU, TOIMENPITEET

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

@app.template_filter("pvm")
def pvm_filter(arvo):
    if not arvo:
        return ""
    if hasattr(arvo, "strftime"):
        return arvo.strftime("%Y-%m-%d")
    return str(arvo)[:10]
app.config["WTF_CSRF_SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-vaihda-tuotannossa")
app.permanent_session_lifetime = timedelta(hours=8)

csrf = CSRFProtect(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://"
)

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET  = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_ID        = os.environ.get("STRIPE_PRICE_ID", "")

DATABASE_URL = os.environ.get("DATABASE_URL", "")


# ── Tietokanta ─────────────────────────────────────────────────────────────────

class DbWrapper:
    """Tekee psycopg2-yhteydestä sqlite3-yhteensopivan rajapinnan."""
    def __init__(self):
        self.conn = psycopg2.connect(DATABASE_URL)
        self.cur  = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def execute(self, sql, params=None):
        sql = sql.replace("?", "%s")
        self.cur.execute(sql, params or [])
        return self

    def executemany(self, sql, seq):
        sql = sql.replace("?", "%s")
        self.cur.executemany(sql, seq)
        return self

    def fetchone(self):
        return self.cur.fetchone()

    def fetchall(self):
        return self.cur.fetchall() or []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *_):
        if exc_type:
            self.conn.rollback()
        else:
            self.conn.commit()
        self.cur.close()
        self.conn.close()


def get_db():
    return DbWrapper()


def init_db():
    with get_db() as db:
        # Erillinen skeema jotta ei sotke muita sovelluksia samassa tietokannassa
        db.execute("CREATE SCHEMA IF NOT EXISTS aiact")
        db.execute("SET search_path TO aiact")

        db.execute("""
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
            luotu       TIMESTAMP DEFAULT NOW()
        )
        """)

        db.execute("""
        CREATE TABLE IF NOT EXISTS jarjestelmat (
            id          TEXT PRIMARY KEY,
            kayttaja_id TEXT NOT NULL,
            nimi        TEXT NOT NULL,
            kuvaus      TEXT,
            vastaukset  TEXT,
            riski_taso  TEXT,
            riski_data  TEXT,
            luotu       TIMESTAMP DEFAULT NOW(),
            FOREIGN KEY (kayttaja_id) REFERENCES kayttajat(id)
        )
        """)

        db.execute("""
        CREATE TABLE IF NOT EXISTS kayntikerrat (
            id       SERIAL PRIMARY KEY,
            polku    TEXT NOT NULL,
            ip       TEXT,
            aika     TIMESTAMP DEFAULT NOW()
        )
        """)

        # Luo testikäyttäjä jos ei ole
        TEST_EMAIL = os.environ.get("TEST_USER_EMAIL", "testi@complianceai.fi")
        TEST_PASS  = os.environ.get("TEST_USER_PASSWORD", "testi1234")
        exists = db.execute("SELECT id FROM kayttajat WHERE email=%s", [TEST_EMAIL]).fetchone()
        if not exists:
            db.execute(
                "INSERT INTO kayttajat (id, email, salasana, yritys, tilaaja) VALUES (%s,%s,%s,%s,%s)",
                [str(uuid.uuid4()), TEST_EMAIL, generate_password_hash(TEST_PASS), "Testiyritys Oy", 1]
            )
        else:
            db.execute("UPDATE kayttajat SET tilaaja=1 WHERE email=%s", [TEST_EMAIL])


def set_schema(db):
    """Aseta aiact-skeema jokaisessa yhteydessä."""
    db.execute("SET search_path TO aiact")
    return db


# ── Auth-apufunktiot ───────────────────────────────────────────────────────────

def kirjautunut():
    return session.get("kayttaja_id") is not None


@app.context_processor
def inject_kirjautunut():
    tilaaja = False
    if kirjautunut():
        try:
            with get_db() as db:
                set_schema(db)
                k = db.execute("SELECT tilaaja FROM kayttajat WHERE id=%s",
                               [session["kayttaja_id"]]).fetchone()
                tilaaja = bool(k and k["tilaaja"])
        except Exception:
            pass
    return {"kirjautunut": kirjautunut(), "tilaaja": tilaaja}


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
            set_schema(db)
            k = db.execute("SELECT tilaaja FROM kayttajat WHERE id=%s",
                           [session["kayttaja_id"]]).fetchone()
        if not k or not k["tilaaja"]:
            flash("Tämä ominaisuus vaatii aktiivisen tilauksen.", "warning")
            return redirect(url_for("tilaus"))
        return f(*args, **kwargs)
    return wrapper


ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

@app.before_request
def kirjaa_kaynnit():
    skip = ["/static/", "/admin", "/stripe/webhook", "/sitemap.xml", "/favicon"]
    if not any(request.path.startswith(s) for s in skip):
        try:
            ip = request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()
            with get_db() as db:
                set_schema(db)
                db.execute("INSERT INTO kayntikerrat (polku, ip) VALUES (%s, %s)",
                           [request.path, ip])
        except Exception:
            pass


# ── Reitit ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    paivat_jaljella = (datetime(2026, 8, 2) - datetime.now()).days
    return render_template("index.html", paivat_jaljella=paivat_jaljella)


@app.route("/rekisteri", methods=["GET", "POST"])
def rekisteri():
    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        salasana = request.form.get("salasana", "")
        yritys   = request.form.get("yritys", "").strip()
        ytunnus  = request.form.get("ytunnus", "").strip()
        koko     = request.form.get("koko", "")

        if not email or not salasana or not yritys:
            flash("Täytä kaikki pakolliset kentät.", "error")
            return render_template("rekisteri.html")

        with get_db() as db:
            set_schema(db)
            olemassa = db.execute("SELECT id FROM kayttajat WHERE email=%s", [email]).fetchone()
            if olemassa:
                flash("Sähköpostiosoite on jo käytössä.", "error")
                return render_template("rekisteri.html")

            kid = str(uuid.uuid4())
            db.execute(
                "INSERT INTO kayttajat (id,email,salasana,yritys,ytunnus,koko) VALUES (%s,%s,%s,%s,%s,%s)",
                [kid, email, generate_password_hash(salasana), yritys, ytunnus, koko]
            )

        session.permanent = True
        session["kayttaja_id"] = kid
        session["yritys"] = yritys
        flash("Tervetuloa! Aloita kartoittamalla AI-järjestelmänne.", "success")
        return redirect(url_for("dashboard"))

    return render_template("rekisteri.html")


@app.route("/kirjaudu", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def kirjaudu():
    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        salasana = request.form.get("salasana", "")

        with get_db() as db:
            set_schema(db)
            k = db.execute("SELECT * FROM kayttajat WHERE email=%s", [email]).fetchone()

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
        set_schema(db)
        kayttaja = db.execute("SELECT * FROM kayttajat WHERE id=%s", [kid]).fetchone()
        if not kayttaja:
            session.clear()
            flash("Istunto vanhentunut, kirjaudu uudelleen.", "warning")
            return redirect(url_for("kirjaudu"))
        jarjestelmat = db.execute(
            "SELECT * FROM jarjestelmat WHERE kayttaja_id=%s ORDER BY luotu DESC", [kid]
        ).fetchall()

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
    # Tarkista ilmaiskäyttäjän kartoitusraja
    kid = session["kayttaja_id"]
    with get_db() as db:
        set_schema(db)
        k = db.execute("SELECT tilaaja FROM kayttajat WHERE id=%s", [kid]).fetchone()
        if not k or not k["tilaaja"]:
            maara = db.execute("SELECT COUNT(*) as n FROM jarjestelmat WHERE kayttaja_id=%s", [kid]).fetchone()["n"]
            if maara >= 1:
                flash("Ilmainen tili on rajoitettu yhteen kartoitukseen. Päivitä Pro jatkaaksesi.", "warning")
                return redirect(url_for("tilaus"))

    if request.method == "POST":
        nimi     = request.form.get("nimi", "").strip()
        kuvaus   = request.form.get("kuvaus", "").strip()
        toimiala = request.form.get("toimiala", "muu")
        rooli    = request.form.get("rooli", "deployer")

        if not nimi:
            flash("Anna järjestelmälle nimi.", "error")
            muokkaus = session.get("kartoitus", {})
            return render_template("kartoitus_1.html", toimialat=TOIMIALAT, muokkaus=muokkaus)

        k = session.get("kartoitus", {})
        muokkaa_id = k.get("muokkaa_id")
        session["kartoitus"] = {
            "nimi": nimi,
            "kuvaus": kuvaus,
            "toimiala": toimiala,
            "rooli": rooli,
        }
        if muokkaa_id:
            session["kartoitus"]["muokkaa_id"] = muokkaa_id
        return redirect(url_for("kartoitus_2"))

    muokkaus = session.get("kartoitus", {})
    return render_template("kartoitus_1.html", toimialat=TOIMIALAT, muokkaus=muokkaus)


@app.route("/kartoitus/<jid>/muokkaa")
@vaadi_kirjautuminen
def muokkaa_jarjestelma(jid):
    with get_db() as db:
        set_schema(db)
        j = db.execute(
            "SELECT * FROM jarjestelmat WHERE id=%s AND kayttaja_id=%s",
            [jid, session["kayttaja_id"]]
        ).fetchone()
    if not j:
        flash("Järjestelmää ei löydy.", "error")
        return redirect(url_for("dashboard"))

    vastaukset = json.loads(j["vastaukset"]) if j["vastaukset"] else {}
    vastaukset["muokkaa_id"] = jid
    session["kartoitus"] = vastaukset
    return redirect(url_for("uusi_jarjestelma"))


@app.route("/kartoitus/ominaisuudet", methods=["GET", "POST"])
@vaadi_kirjautuminen
def kartoitus_2():
    if "kartoitus" not in session:
        return redirect(url_for("uusi_jarjestelma"))

    if request.method == "POST":
        k = session["kartoitus"]
        k.update({
            "autonominen":           request.form.get("autonominen") == "on",
            "biometria":             request.form.get("biometria") == "on",
            "kohdistuu_henkiloihin": request.form.get("kohdistuu_henkiloihin") == "on",
            "chatbot":               request.form.get("chatbot") == "on",
            "generoi_sisaltoa":      request.form.get("generoi_sisaltoa") == "on",
            "kielletty":             request.form.get("kielletty") == "on",
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
        for v in VAATIMUKSET + VAATIMUKSET_RAJATTU:
            k[v["id"]] = request.form.get(v["id"]) == "on"
        session["kartoitus"] = k

        riski = luokittele_riski(k)
        muokkaa_id = k.get("muokkaa_id")

        with get_db() as db:
            set_schema(db)
            if muokkaa_id:
                db.execute(
                    """UPDATE jarjestelmat
                       SET nimi=%s, kuvaus=%s, vastaukset=%s, riski_taso=%s, riski_data=%s
                       WHERE id=%s AND kayttaja_id=%s""",
                    [k["nimi"], k.get("kuvaus", ""), json.dumps(k),
                     riski["taso"], json.dumps(riski),
                     muokkaa_id, session["kayttaja_id"]]
                )
                jid = muokkaa_id
            else:
                jid = str(uuid.uuid4())
                db.execute(
                    """INSERT INTO jarjestelmat
                       (id, kayttaja_id, nimi, kuvaus, vastaukset, riski_taso, riski_data)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    [jid, session["kayttaja_id"], k["nimi"], k.get("kuvaus", ""),
                     json.dumps(k), riski["taso"], json.dumps(riski)]
                )

        session.pop("kartoitus", None)
        flash("Järjestelmä tallennettu.", "success")
        return redirect(url_for("tulos", jid=jid))

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
        set_schema(db)
        j = db.execute(
            "SELECT * FROM jarjestelmat WHERE id=%s AND kayttaja_id=%s",
            [jid, session["kayttaja_id"]]
        ).fetchone()
        k = db.execute("SELECT tilaaja FROM kayttajat WHERE id=%s",
                       [session["kayttaja_id"]]).fetchone()

    if not j:
        flash("Järjestelmää ei löydy.", "error")
        return redirect(url_for("dashboard"))

    riski = json.loads(j["riski_data"])
    vastaukset = json.loads(j["vastaukset"]) if j["vastaukset"] else {}
    paivat_jaljella = (datetime(2026, 8, 2) - datetime.now()).days

    return render_template("tulos.html",
                           jarjestelma=j,
                           riski=riski,
                           vastaukset=vastaukset,
                           paivat_jaljella=paivat_jaljella,
                           tilaaja=k["tilaaja"] if k else False,
                           toimenpiteet=TOIMENPITEET)


@app.route("/jarjestelma/<jid>/poista", methods=["POST"])
@vaadi_kirjautuminen
def poista_jarjestelma(jid):
    with get_db() as db:
        set_schema(db)
        db.execute("DELETE FROM jarjestelmat WHERE id=%s AND kayttaja_id=%s",
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
        set_schema(db)
        k = db.execute("SELECT * FROM kayttajat WHERE id=%s", [kid]).fetchone()

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
    except Exception:
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
                    set_schema(db)
                    db.execute("UPDATE kayttajat SET tilaaja=1, stripe_id=%s WHERE id=%s",
                               [cs.customer, kid])
        except Exception:
            pass
    flash("Tilaus aktivoitu! Tervetuloa.", "success")
    return redirect(url_for("dashboard"))


@app.route("/stripe/webhook", methods=["POST"])
@csrf.exempt
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
            set_schema(db)
            db.execute("UPDATE kayttajat SET tilaaja=0 WHERE stripe_id=%s", [customer_id])

    return "", 200


# ── PDF-raportti ───────────────────────────────────────────────────────────────

@app.route("/raportti/<jid>")
@vaadi_tilaus
def pdf_raportti(jid):
    with get_db() as db:
        set_schema(db)
        j = db.execute(
            "SELECT * FROM jarjestelmat WHERE id=%s AND kayttaja_id=%s",
            [jid, session["kayttaja_id"]]
        ).fetchone()
        kayttaja = db.execute("SELECT * FROM kayttajat WHERE id=%s",
                              [session["kayttaja_id"]]).fetchone()

    if not j:
        return redirect(url_for("dashboard"))

    riski = json.loads(j["riski_data"])
    seuraava_tarkistus = (datetime.now() + timedelta(days=180)).strftime("%d.%m.%Y")
    return render_template("raportti_pdf.html",
                           jarjestelma=j,
                           riski=riski,
                           kayttaja=kayttaja,
                           toimenpiteet=TOIMENPITEET,
                           seuraava_tarkistus=seuraava_tarkistus,
                           pvm=datetime.now().strftime("%d.%m.%Y"))


# ── Muut sivut ─────────────────────────────────────────────────────────────────

@app.route("/tietosuoja")
def tietosuoja():
    return render_template("tietosuoja.html")


@app.route("/robots.txt")
def robots():
    return app.send_static_file("robots.txt")


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if request.form.get("salasana") == ADMIN_PASSWORD:
            session["admin"] = True
        else:
            flash("Väärä salasana.", "error")
            return render_template("admin_kirjaudu.html")

    if not session.get("admin"):
        return render_template("admin_kirjaudu.html")

    with get_db() as db:
        set_schema(db)
        kaynnit_yht = db.execute("SELECT COUNT(*) as n FROM kayntikerrat").fetchone()["n"]
        uniikit     = db.execute("SELECT COUNT(DISTINCT ip) as n FROM kayntikerrat").fetchone()["n"]
        tanaan      = db.execute(
            "SELECT COUNT(*) as n FROM kayntikerrat WHERE aika::date = CURRENT_DATE"
        ).fetchone()["n"]
        paivat = db.execute("""
            SELECT TO_CHAR(aika::date, 'YYYY-MM-DD') as pv, COUNT(*) as n
            FROM kayntikerrat
            WHERE aika >= NOW() - INTERVAL '7 days'
            GROUP BY aika::date ORDER BY pv
        """).fetchall()
        sivut = db.execute("""
            SELECT polku, COUNT(*) as n FROM kayntikerrat
            GROUP BY polku ORDER BY n DESC LIMIT 10
        """).fetchall()
        kayttajat_yht    = db.execute("SELECT COUNT(*) as n FROM kayttajat").fetchone()["n"]
        tilaajat_yht     = db.execute("SELECT COUNT(*) as n FROM kayttajat WHERE tilaaja=1").fetchone()["n"]
        jarjestelmat_yht = db.execute("SELECT COUNT(*) as n FROM jarjestelmat").fetchone()["n"]
        uudet = db.execute("""
            SELECT TO_CHAR(luotu::date, 'YYYY-MM-DD') as pv, COUNT(*) as n FROM kayttajat
            WHERE luotu >= NOW() - INTERVAL '7 days'
            GROUP BY luotu::date ORDER BY pv
        """).fetchall()

    return render_template("admin.html",
                           kaynnit_yht=kaynnit_yht,
                           uniikit=uniikit,
                           tanaan=tanaan,
                           paivat=[dict(r) for r in paivat],
                           sivut=[dict(r) for r in sivut],
                           kayttajat_yht=kayttajat_yht,
                           tilaajat_yht=tilaajat_yht,
                           jarjestelmat_yht=jarjestelmat_yht,
                           uudet=[dict(r) for r in uudet])


@app.route("/sitemap.xml")
def sitemap():
    pages = [
        ("https://aiact.onrender.com/", "weekly", "1.0"),
        ("https://aiact.onrender.com/rekisteri", "monthly", "0.9"),
        ("https://aiact.onrender.com/kirjaudu", "monthly", "0.7"),
        ("https://aiact.onrender.com/tietosuoja", "monthly", "0.3"),
    ]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url, freq, prio in pages:
        xml += f"  <url><loc>{url}</loc><changefreq>{freq}</changefreq><priority>{prio}</priority></url>\n"
    xml += "</urlset>"
    return Response(xml, mimetype="application/xml")


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(429)
def rate_limit_exceeded(e):
    flash("Liian monta kirjautumisyritystä. Odota hetki.", "error")
    return render_template("kirjaudu.html"), 429


# ── Käynnistys ─────────────────────────────────────────────────────────────────

init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5001)
