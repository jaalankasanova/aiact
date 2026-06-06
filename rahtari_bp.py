"""Rahtari — B2B kuljetusmarkkinapaikka, Flask Blueprint"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, uuid, io, json, smtplib, threading
from datetime import datetime
from functools import wraps
from email.mime.text import MIMEText
from kaupungit import MAAKUNNAT, maakunta_kaupungille
from finvoice import luo_finvoice, laheta_maventa

bp = Blueprint("rahtari", __name__,
               url_prefix="/rahtari",
               template_folder="templates/rahtari")

@bp.app_template_filter("fromjson")
def fromjson_filter(s):
    try: return json.loads(s or "[]")
    except: return []

DB = os.path.join(os.path.dirname(__file__), "rahtari.db")

SMTP_HOST  = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT  = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER  = os.environ.get("SMTP_USER", "")
SMTP_PASS  = os.environ.get("SMTP_PASS", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", SMTP_USER)
TWILIO_SID   = os.environ.get("TWILIO_SID", "")
TWILIO_TOKEN = os.environ.get("TWILIO_TOKEN", "")
TWILIO_FROM  = os.environ.get("TWILIO_FROM", "")


def get_db():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    return db

def init_rahtari_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS r_tilaukset (
        id              TEXT PRIMARY KEY,
        ytunnus         TEXT NOT NULL,
        yritys          TEXT NOT NULL,
        yhteyshenk      TEXT NOT NULL,
        email           TEXT NOT NULL,
        puhelin         TEXT,
        lahto_kaupunki  TEXT NOT NULL,
        lahto_maakunta  TEXT NOT NULL,
        lahto_osoite    TEXT,
        toimitus        TEXT NOT NULL,
        tuote           TEXT NOT NULL,
        paino           TEXT,
        mitat           TEXT,
        deadline        TEXT,
        max_budjetti    REAL,
        ovt_tunnus      TEXT,
        operaattori     TEXT,
        tila            TEXT DEFAULT 'avoin',
        hyvaksytty_tarjous TEXT,
        token           TEXT UNIQUE,
        luotu           TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS r_tarjoukset (
        id            TEXT PRIMARY KEY,
        tilaus_id     TEXT NOT NULL,
        kuljettaja_id TEXT NOT NULL,
        hinta         REAL NOT NULL,
        eta           TEXT,
        viesti        TEXT,
        tila          TEXT DEFAULT 'odottaa',
        luotu         TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS r_kuljettajat (
        id        TEXT PRIMARY KEY,
        nimi      TEXT NOT NULL,
        yritys    TEXT,
        ytunnus   TEXT,
        puhelin   TEXT NOT NULL,
        email     TEXT UNIQUE NOT NULL,
        salasana  TEXT NOT NULL,
        alueet    TEXT DEFAULT '[]',
        luotu     TEXT DEFAULT (datetime('now'))
    );
    """)
    db.commit()
    try:
        db.execute("ALTER TABLE r_tilaukset ADD COLUMN lahto_osoite TEXT")
        db.commit()
    except sqlite3.OperationalError:
        pass
    db.close()


# ── NOTIFIKAATIOT ─────────────────────────────────────────────────────────────

def laheta_email(to, subject, body):
    if not SMTP_USER or not SMTP_PASS:
        print(f"[RAHTARI EMAIL] {to}: {subject}")
        return
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"]    = EMAIL_FROM
        msg["To"]      = to
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls(); s.login(SMTP_USER, SMTP_PASS); s.send_message(msg)
    except Exception as e:
        print(f"[RAHTARI EMAIL ERROR] {e}")

def laheta_sms(to, body):
    if not TWILIO_SID or not TWILIO_TOKEN or not to:
        print(f"[RAHTARI SMS] {to}: {body}"); return
    try:
        from twilio.rest import Client
        Client(TWILIO_SID, TWILIO_TOKEN).messages.create(
            body=body, from_=TWILIO_FROM, to=to)
    except Exception as e:
        print(f"[RAHTARI SMS ERROR] {e}")

def ilmoita_kuljettajille(tilaus):
    def lahetys():
        db = get_db()
        kuljettajat = db.execute(
            "SELECT * FROM r_kuljettajat WHERE alueet != '[]'"
        ).fetchall()
        db.close()
        app_url = os.environ.get("APP_URL", "https://aiact.onrender.com")
        for k in kuljettajat:
            alueet = json.loads(k["alueet"] or "[]")
            if tilaus["lahto_maakunta"] in alueet or tilaus["lahto_kaupunki"] in alueet:
                viesti = (
                    f"Uusi kuljetustilaus alueellesi!\n\n"
                    f"Lähtö: {tilaus['lahto_kaupunki']} ({tilaus['lahto_maakunta']})\n"
                    f"Kohde: {tilaus['toimitus']}\n"
                    f"Tavara: {tilaus['tuote']}\n"
                )
                if tilaus["max_budjetti"]:
                    viesti += f"Max budjetti: {tilaus['max_budjetti']:.0f}€\n"
                if tilaus["deadline"]:
                    viesti += f"Deadline: {tilaus['deadline']}\n"
                viesti += f"\nJätä tarjous: {app_url}/rahtari/kuljettaja"
                laheta_email(k["email"], "Rahtari — uusi kuljetustilaus", viesti)
                if k["puhelin"]:
                    laheta_sms(k["puhelin"],
                               f"Rahtari: Uusi tilaus {tilaus['lahto_kaupunki']}→{tilaus['toimitus']}"
                               f"{' max '+str(int(tilaus['max_budjetti']))+'€' if tilaus['max_budjetti'] else ''}."
                               f" rahtari.fi/kuljettaja")
    threading.Thread(target=lahetys, daemon=True).start()


# ── AUTH ──────────────────────────────────────────────────────────────────────

def kuljettaja_vaaditaan(f):
    @wraps(f)
    def d(*a, **kw):
        if not session.get("r_kuljettaja_id"):
            return redirect(url_for("rahtari.kuljettaja_kirjaudu"))
        return f(*a, **kw)
    return d


# ── REITIT ────────────────────────────────────────────────────────────────────

@bp.route("/")
def index():
    return render_template("rahtari/index.html")

@bp.route("/tilaa", methods=["GET","POST"])
def tilaa():
    if request.method == "POST":
        kaupunki = request.form["lahto_kaupunki"].strip()
        maakunta = maakunta_kaupungille(kaupunki) or ""
        token = uuid.uuid4().hex
        tid   = str(uuid.uuid4())
        db = get_db()
        db.execute("""
            INSERT INTO r_tilaukset
            (id,ytunnus,yritys,yhteyshenk,email,puhelin,
             lahto_kaupunki,lahto_maakunta,lahto_osoite,toimitus,tuote,
             paino,mitat,deadline,max_budjetti,ovt_tunnus,operaattori,token)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (tid,
              request.form["ytunnus"].strip(),
              request.form["yritys"].strip(),
              request.form["yhteyshenk"].strip(),
              request.form["email"].strip().lower(),
              request.form.get("puhelin","").strip() or None,
              kaupunki, maakunta,
              request.form.get("lahto_osoite","").strip() or None,
              request.form["toimitus"].strip(),
              request.form["tuote"].strip(),
              request.form.get("paino","").strip() or None,
              request.form.get("mitat","").strip() or None,
              request.form.get("deadline","").strip() or None,
              float(request.form["max_budjetti"]) if request.form.get("max_budjetti") else None,
              request.form.get("ovt_tunnus","").strip() or None,
              request.form.get("operaattori","").strip() or None,
              token))
        db.commit()
        tilaus = db.execute("SELECT * FROM r_tilaukset WHERE id=?", (tid,)).fetchone()
        db.close()
        ilmoita_kuljettajille(tilaus)
        # Sähköposti tilaajalle seurantaLinkin kanssa
        app_url = os.environ.get("APP_URL", "https://aiact.onrender.com")
        seuranta_url = f"{app_url}/rahtari/seuranta/{token}"
        laheta_email(
            tilaus["email"],
            "Rahtari — tilauksesi on vastaanotettu",
            f"Hei {tilaus['yhteyshenk']},\n\n"
            f"Kuljetustilauksesi on vastaanotettu.\n\n"
            f"Lähtö: {tilaus['lahto_osoite'] + ', ' if tilaus['lahto_osoite'] else ''}"
            f"{tilaus['lahto_kaupunki']} ({tilaus['lahto_maakunta']})\n"
            f"Toimitus: {tilaus['toimitus']}\n"
            f"Tavara: {tilaus['tuote']}\n\n"
            f"Seuraa tarjouksia ja hyväksy paras tästä linkistä:\n{seuranta_url}\n\n"
            f"Tallenna tämä linkki — se on ainoa tapa päästä seurantasivulle.\n\n"
            f"RAHTARI"
        )
        return redirect(url_for("rahtari.seuranta", token=token))
    return render_template("rahtari/tilaa.html", maakunnat=MAAKUNNAT)

@bp.route("/seuranta/<token>")
def seuranta(token):
    db = get_db()
    tilaus = db.execute("SELECT * FROM r_tilaukset WHERE token=?", (token,)).fetchone()
    if not tilaus:
        db.close(); flash("Tilausta ei löydy.", "error")
        return redirect(url_for("rahtari.index"))
    tarjoukset = db.execute("""
        SELECT t.*, k.nimi as kuljettaja_nimi, k.yritys as kuljettaja_yritys,
               k.puhelin as kuljettaja_puhelin
        FROM r_tarjoukset t JOIN r_kuljettajat k ON k.id=t.kuljettaja_id
        WHERE t.tilaus_id=? ORDER BY t.hinta ASC
    """, (tilaus["id"],)).fetchall()
    db.close()
    return render_template("rahtari/seuranta.html",
                           tilaus=tilaus, tarjoukset=tarjoukset, token=token)

@bp.route("/hyvaksy/<token>/<tarjous_id>", methods=["POST"])
def hyvaksy(token, tarjous_id):
    db = get_db()
    tilaus = db.execute("SELECT * FROM r_tilaukset WHERE token=?", (token,)).fetchone()
    if not tilaus or tilaus["tila"] != "avoin":
        db.close(); flash("Ei voida hyväksyä.", "error")
        return redirect(url_for("rahtari.seuranta", token=token))
    db.execute("UPDATE r_tilaukset SET tila='hyvaksytty', hyvaksytty_tarjous=? WHERE token=?",
               (tarjous_id, token))
    db.execute("UPDATE r_tarjoukset SET tila='hyvaksytty' WHERE id=?", (tarjous_id,))
    db.execute("UPDATE r_tarjoukset SET tila='hylatty' WHERE tilaus_id=? AND id!=?",
               (tilaus["id"], tarjous_id))
    tarjous = db.execute(
        "SELECT tar.*, k.email, k.puhelin, k.nimi FROM r_tarjoukset tar "
        "JOIN r_kuljettajat k ON k.id=tar.kuljettaja_id WHERE tar.id=?",
        (tarjous_id,)).fetchone()
    db.commit(); db.close()
    if tarjous:
        def ilmoitus():
            viesti = (f"Tarjouksesi hyväksyttiin!\n\n"
                      f"Tilaus: {tilaus['lahto_kaupunki']} → {tilaus['toimitus']}\n"
                      f"Hinta: {tarjous['hinta']:.2f}€\n"
                      f"Tilaaja: {tilaus['yritys']}, {tilaus['yhteyshenk']}, "
                      f"{tilaus['puhelin'] or tilaus['email']}")
            laheta_email(tarjous["email"], "Rahtari — tarjouksesi hyväksyttiin!", viesti)
            if tarjous["puhelin"]:
                laheta_sms(tarjous["puhelin"],
                           f"Rahtari: Tarjouksesi {tarjous['hinta']:.0f}€ hyväksyttiin! "
                           f"{tilaus['lahto_kaupunki']}→{tilaus['toimitus']}. "
                           f"Yhteys: {tilaus['yhteyshenk']} {tilaus['puhelin'] or ''}")
        threading.Thread(target=ilmoitus, daemon=True).start()
    # Lähetä verkkolasku jos tilaajalla on OVT-tunnus
    if tilaus.get("ovt_tunnus") and tarjous:
        def verkkolasku():
            try:
                laskun_nro = tilaus["id"][:8].upper()
                xml = luo_finvoice(dict(tilaus), dict(tarjous), laskun_nro)
                tulos = laheta_maventa(xml, laskun_nro)
                if not tulos["ok"]:
                    print(f"[VERKKOLASKU VIRHE] {tulos['virhe']}")
            except Exception as ex:
                print(f"[VERKKOLASKU VIRHE] {ex}")
        threading.Thread(target=verkkolasku, daemon=True).start()

    flash("Tarjous hyväksytty! Kuljettajalle lähetetty ilmoitus.", "ok")
    return redirect(url_for("rahtari.seuranta", token=token))

@bp.route("/toimitettu/<token>", methods=["POST"])
def toimitettu(token):
    db = get_db()
    db.execute("UPDATE r_tilaukset SET tila='toimitettu' WHERE token=? AND tila='hyvaksytty'", (token,))
    db.commit(); db.close()
    return redirect(url_for("rahtari.seuranta", token=token))

@bp.route("/lasku/<token>")
def lasku(token):
    db = get_db()
    tilaus = db.execute("SELECT * FROM r_tilaukset WHERE token=?", (token,)).fetchone()
    tarjous = None
    if tilaus and tilaus["hyvaksytty_tarjous"]:
        tarjous = db.execute("""
            SELECT t.*, k.nimi, k.yritys as k_yritys, k.ytunnus as k_ytunnus, k.puhelin
            FROM r_tarjoukset t JOIN r_kuljettajat k ON k.id=t.kuljettaja_id WHERE t.id=?
        """, (tilaus["hyvaksytty_tarjous"],)).fetchone()
    db.close()
    if not tilaus or not tarjous:
        flash("Lasku ei saatavilla.", "error")
        return redirect(url_for("rahtari.index"))
    try:
        from fpdf import FPDF
        pdf = FPDF(); pdf.add_page(); pdf.set_margins(20,20,20)
        pdf.set_fill_color(255,224,0); pdf.rect(0,0,210,28,"F")
        pdf.set_font("Helvetica","B",20); pdf.set_text_color(0,0,0)
        pdf.set_xy(20,8); pdf.cell(0,12,"RAHTARI — LASKU",ln=True)
        pdf.set_font("Helvetica",size=9); pdf.set_xy(20,32)
        pdf.cell(0,5,f"Laskunumero: {tilaus['id'][:8].upper()}  |  "
                    f"Pvm: {datetime.now().strftime('%d.%m.%Y')}  |  Maksuehto: 14 pv netto",ln=True)
        pdf.ln(6)
        pdf.set_font("Helvetica","B",9)
        pdf.cell(85,5,"LASKUTTAJA",ln=False); pdf.cell(0,5,"VASTAANOTTAJA",ln=True)
        pdf.set_font("Helvetica",size=9)
        pdf.cell(85,5,tarjous["k_yritys"] or tarjous["nimi"],ln=False)
        pdf.cell(0,5,tilaus["yritys"],ln=True)
        pdf.cell(85,5,f"Y: {tarjous['k_ytunnus']}" if tarjous["k_ytunnus"] else "",ln=False)
        pdf.cell(0,5,f"Y-tunnus: {tilaus['ytunnus']}",ln=True)
        pdf.cell(85,5,tarjous["puhelin"] or "",ln=False)
        pdf.cell(0,5,tilaus["yhteyshenk"],ln=True)
        if tilaus["ovt_tunnus"]:
            pdf.cell(85,5,"",ln=False)
            pdf.cell(0,5,f"OVT: {tilaus['ovt_tunnus']}  Op: {tilaus['operaattori'] or ''}",ln=True)
        pdf.ln(8)
        pdf.set_fill_color(255,224,0); pdf.set_font("Helvetica","B",9)
        pdf.cell(0,7,"KULJETUKSEN TIEDOT",ln=True,fill=True)
        pdf.set_font("Helvetica",size=9)
        for label, val in [
            ("Noutopaikka", f"{tilaus['lahto_kaupunki']} ({tilaus['lahto_maakunta']})"),
            ("Toimituspaikka", tilaus["toimitus"]),
            ("Tavara", tilaus["tuote"]),
            *([("Paino", tilaus["paino"])] if tilaus["paino"] else []),
            *([("Aikataulu", tilaus["deadline"])] if tilaus["deadline"] else []),
        ]:
            pdf.cell(45,6,label,ln=False); pdf.cell(0,6,val,ln=True)
        pdf.ln(6); alv = tarjous["hinta"]*0.255; yht = tarjous["hinta"]+alv
        pdf.set_fill_color(255,224,0); pdf.set_font("Helvetica","B",11)
        pdf.cell(0,9,f"  Veroton: {tarjous['hinta']:.2f} EUR   "
                    f"ALV 25,5%: {alv:.2f} EUR   YHT: {yht:.2f} EUR",ln=True,fill=True)
        buf = io.BytesIO(pdf.output()); buf.seek(0)
        return send_file(buf, mimetype="application/pdf",
                         download_name=f"rahtari_{tilaus['id'][:8]}.pdf")
    except ImportError:
        flash("fpdf2 ei ole asennettu.", "error")
        return redirect(url_for("rahtari.seuranta", token=token))

# ── KULJETTAJA ────────────────────────────────────────────────────────────────

@bp.route("/kuljettaja/rekisteroidy", methods=["GET","POST"])
def kuljettaja_rekisteroidy():
    if request.method == "POST":
        alueet = request.form.getlist("alueet")
        db = get_db()
        try:
            db.execute("""INSERT INTO r_kuljettajat
                (id,nimi,yritys,ytunnus,puhelin,email,salasana,alueet)
                VALUES (?,?,?,?,?,?,?,?)""",
                (str(uuid.uuid4()),
                 request.form["nimi"].strip(),
                 request.form.get("yritys","").strip() or None,
                 request.form.get("ytunnus","").strip() or None,
                 request.form["puhelin"].strip(),
                 request.form["email"].strip().lower(),
                 generate_password_hash(request.form["salasana"]),
                 json.dumps(alueet)))
            db.commit()
            flash("Rekisteröityminen onnistui.", "ok")
            return redirect(url_for("rahtari.kuljettaja_kirjaudu"))
        except sqlite3.IntegrityError:
            flash("Sähköposti on jo käytössä.", "error")
        finally:
            db.close()
    return render_template("rahtari/kuljettaja_rekisteroidy.html", maakunnat=MAAKUNNAT)

@bp.route("/kuljettaja/kirjaudu", methods=["GET","POST"])
def kuljettaja_kirjaudu():
    if request.method == "POST":
        db = get_db()
        k = db.execute("SELECT * FROM r_kuljettajat WHERE email=?",
                       (request.form["email"].strip().lower(),)).fetchone()
        db.close()
        if k and check_password_hash(k["salasana"], request.form["salasana"]):
            session["r_kuljettaja_id"]   = k["id"]
            session["r_kuljettaja_nimi"] = k["nimi"]
            return redirect(url_for("rahtari.kuljettaja_dashboard"))
        flash("Väärä sähköposti tai salasana.", "error")
    return render_template("rahtari/kuljettaja_kirjaudu.html")

@bp.route("/kuljettaja/ulos")
def kuljettaja_ulos():
    session.pop("r_kuljettaja_id", None)
    session.pop("r_kuljettaja_nimi", None)
    return redirect(url_for("rahtari.index"))

@bp.route("/kuljettaja")
@kuljettaja_vaaditaan
def kuljettaja_dashboard():
    db = get_db()
    k = db.execute("SELECT * FROM r_kuljettajat WHERE id=?",
                   (session["r_kuljettaja_id"],)).fetchone()
    alueet = json.loads(k["alueet"] or "[]")
    avoimet = []
    if alueet:
        kaikki = db.execute("""
            SELECT t.*,
                   (SELECT COUNT(*) FROM r_tarjoukset WHERE tilaus_id=t.id) as tarjouksia,
                   (SELECT COUNT(*) FROM r_tarjoukset WHERE tilaus_id=t.id AND kuljettaja_id=?) as oma
            FROM r_tilaukset t WHERE t.tila='avoin' ORDER BY t.luotu DESC
        """, (session["r_kuljettaja_id"],)).fetchall()
        for t in kaikki:
            if t["lahto_maakunta"] in alueet or t["lahto_kaupunki"] in alueet:
                avoimet.append(t)
    omat = db.execute("""
        SELECT tar.*, t.lahto_kaupunki, t.toimitus, t.tila as tilauksen_tila, t.yritys
        FROM r_tarjoukset tar JOIN r_tilaukset t ON t.id=tar.tilaus_id
        WHERE tar.kuljettaja_id=? ORDER BY tar.luotu DESC
    """, (session["r_kuljettaja_id"],)).fetchall()
    db.close()
    return render_template("rahtari/kuljettaja_dashboard.html",
                           avoimet=avoimet, omat=omat,
                           nimi=k["nimi"], alueet=alueet)

@bp.route("/kuljettaja/profiili", methods=["GET","POST"])
@kuljettaja_vaaditaan
def kuljettaja_profiili():
    db = get_db()
    k = db.execute("SELECT * FROM r_kuljettajat WHERE id=?",
                   (session["r_kuljettaja_id"],)).fetchone()
    if request.method == "POST":
        alueet = request.form.getlist("alueet")
        db.execute("UPDATE r_kuljettajat SET alueet=?,puhelin=?,yritys=? WHERE id=?",
                   (json.dumps(alueet),
                    request.form["puhelin"].strip(),
                    request.form.get("yritys","").strip() or None,
                    session["r_kuljettaja_id"]))
        db.commit()
        flash("Profiili päivitetty.", "ok")
        return redirect(url_for("rahtari.kuljettaja_profiili"))
    valitut = json.loads(k["alueet"] or "[]")
    db.close()
    return render_template("rahtari/kuljettaja_profiili.html",
                           k=k, maakunnat=MAAKUNNAT, valitut=valitut)

# ── ADMIN ─────────────────────────────────────────────────────────────────────

ADMIN_USER = os.environ.get("RAHTARI_ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("RAHTARI_ADMIN_PASS", "rahtari2026")

def admin_vaaditaan(f):
    @wraps(f)
    def d(*a, **kw):
        if not session.get("r_admin"):
            return redirect(url_for("rahtari.admin_kirjaudu"))
        return f(*a, **kw)
    return d

@bp.route("/admin/kirjaudu", methods=["GET","POST"])
def admin_kirjaudu():
    if request.method == "POST":
        if (request.form.get("tunnus") == ADMIN_USER and
                request.form.get("salasana") == ADMIN_PASS):
            session["r_admin"] = True
            return redirect(url_for("rahtari.admin_dashboard"))
        flash("Väärät tunnukset.", "error")
    return render_template("rahtari/admin_kirjaudu.html")

@bp.route("/admin/ulos")
def admin_ulos():
    session.pop("r_admin", None)
    return redirect(url_for("rahtari.admin_kirjaudu"))

@bp.route("/admin")
@admin_vaaditaan
def admin_dashboard():
    db = get_db()
    stats = {
        "tilaukset":   db.execute("SELECT COUNT(*) FROM r_tilaukset").fetchone()[0],
        "avoimet":     db.execute("SELECT COUNT(*) FROM r_tilaukset WHERE tila='avoin'").fetchone()[0],
        "hyvaksytyt":  db.execute("SELECT COUNT(*) FROM r_tilaukset WHERE tila='hyvaksytty'").fetchone()[0],
        "toimitetut":  db.execute("SELECT COUNT(*) FROM r_tilaukset WHERE tila='toimitettu'").fetchone()[0],
        "kuljettajat": db.execute("SELECT COUNT(*) FROM r_kuljettajat").fetchone()[0],
        "tarjoukset":  db.execute("SELECT COUNT(*) FROM r_tarjoukset").fetchone()[0],
    }
    tilaukset = db.execute("""
        SELECT t.*,
               (SELECT COUNT(*) FROM r_tarjoukset WHERE tilaus_id=t.id) as tarjouksia
        FROM r_tilaukset t ORDER BY t.luotu DESC LIMIT 20
    """).fetchall()
    db.close()
    return render_template("rahtari/admin_dashboard.html", stats=stats, tilaukset=tilaukset)

@bp.route("/admin/tilaukset")
@admin_vaaditaan
def admin_tilaukset():
    tila = request.args.get("tila", "")
    db = get_db()
    q = "SELECT t.*, (SELECT COUNT(*) FROM r_tarjoukset WHERE tilaus_id=t.id) as tarjouksia FROM r_tilaukset t"
    q += " WHERE t.tila=?" if tila else ""
    q += " ORDER BY t.luotu DESC"
    tilaukset = db.execute(q, (tila,) if tila else ()).fetchall()
    db.close()
    return render_template("rahtari/admin_tilaukset.html", tilaukset=tilaukset, tila=tila)

@bp.route("/admin/tilaus/<tilaus_id>")
@admin_vaaditaan
def admin_tilaus(tilaus_id):
    db = get_db()
    tilaus = db.execute("SELECT * FROM r_tilaukset WHERE id=?", (tilaus_id,)).fetchone()
    tarjoukset = db.execute("""
        SELECT t.*, k.nimi as knimi, k.yritys as kyritys, k.puhelin as kpuh, k.email as kemail
        FROM r_tarjoukset t JOIN r_kuljettajat k ON k.id=t.kuljettaja_id
        WHERE t.tilaus_id=? ORDER BY t.hinta ASC
    """, (tilaus_id,)).fetchall()
    db.close()
    return render_template("rahtari/admin_tilaus.html", tilaus=tilaus, tarjoukset=tarjoukset)

@bp.route("/admin/kuljettajat")
@admin_vaaditaan
def admin_kuljettajat():
    db = get_db()
    kuljettajat = db.execute("""
        SELECT k.*, (SELECT COUNT(*) FROM r_tarjoukset WHERE kuljettaja_id=k.id) as tarjouksia
        FROM r_kuljettajat k ORDER BY k.luotu DESC
    """).fetchall()
    db.close()
    return render_template("rahtari/admin_kuljettajat.html", kuljettajat=kuljettajat)

@bp.route("/admin/poista_kuljettaja/<kid>", methods=["POST"])
@admin_vaaditaan
def admin_poista_kuljettaja(kid):
    db = get_db()
    db.execute("DELETE FROM r_kuljettajat WHERE id=?", (kid,))
    db.commit(); db.close()
    flash("Kuljettaja poistettu.", "ok")
    return redirect(url_for("rahtari.admin_kuljettajat"))


@bp.route("/kuljettaja/tarjous/<tilaus_id>", methods=["POST"])
@kuljettaja_vaaditaan
def tee_tarjous(tilaus_id):
    db = get_db()
    if db.execute("SELECT id FROM r_tarjoukset WHERE tilaus_id=? AND kuljettaja_id=?",
                  (tilaus_id, session["r_kuljettaja_id"])).fetchone():
        db.close(); flash("Olet jo jättänyt tarjouksen.", "error")
        return redirect(url_for("rahtari.kuljettaja_dashboard"))
    t = db.execute("SELECT tila FROM r_tilaukset WHERE id=?", (tilaus_id,)).fetchone()
    if not t or t["tila"] != "avoin":
        db.close(); flash("Tilaus ei ole enää avoin.", "error")
        return redirect(url_for("rahtari.kuljettaja_dashboard"))
    db.execute("""INSERT INTO r_tarjoukset (id,tilaus_id,kuljettaja_id,hinta,eta,viesti)
                  VALUES (?,?,?,?,?,?)""",
               (str(uuid.uuid4()), tilaus_id, session["r_kuljettaja_id"],
                float(request.form["hinta"]),
                request.form.get("eta") or None,
                request.form.get("viesti") or None))
    db.commit(); db.close()
    flash("Tarjous lähetetty.", "ok")
    return redirect(url_for("rahtari.kuljettaja_dashboard"))
