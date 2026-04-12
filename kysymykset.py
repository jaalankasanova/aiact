# EU AI Act -riskianalyysimoottori
# Perustuu EU AI Act (2024/1689) Annex III -luokitteluun

TOIMIALAT = [
    ("rekrytointi",        "Rekrytointi, HR tai henkilöstöhallinto"),
    ("asiakaspalvelu",     "Asiakaspalvelu tai viestintä"),
    ("luotto",             "Luottopäätökset, vakuutukset tai rahoitus"),
    ("koulutus",           "Koulutus tai oppilaiden arviointi"),
    ("terveys",            "Terveydenhuolto tai lääkintä"),
    ("infrastruktuuri",    "Kriittinen infrastruktuuri (energia, liikenne, vesi)"),
    ("lainvalvonta",       "Lainvalvonta tai turvallisuus"),
    ("maahanmuutto",       "Maahanmuutto tai rajavalvonta"),
    ("julkinen",           "Julkiset palvelut tai sosiaalietuudet"),
    ("markkinointi",       "Markkinointi, myynti tai suosittelu"),
    ("muu",                "Muu toiminto"),
]

# Toimialat jotka johtavat korkean riskin luokitukseen (Annex III)
KORKEA_RISKI_TOIMIALAT = {
    "rekrytointi", "luotto", "koulutus", "terveys",
    "infrastruktuuri", "lainvalvonta", "maahanmuutto", "julkinen"
}

# Vaatimukset korkean riskin järjestelmille
VAATIMUKSET = [
    {
        "id": "tekninen_dok",
        "otsikko": "Tekninen dokumentaatio",
        "kuvaus": "Järjestelmästä on laadittu tekninen dokumentaatio (Art. 11)",
        "artikkeli": "Art. 11",
        "deadline": "2.8.2026",
        "prioriteetti": "kriittinen",
    },
    {
        "id": "lokit",
        "otsikko": "Automaattiset lokitiedostot",
        "kuvaus": "Järjestelmä tallentaa lokeja vähintään 6 kuukauden ajan (Art. 12)",
        "artikkeli": "Art. 12",
        "deadline": "2.8.2026",
        "prioriteetti": "kriittinen",
    },
    {
        "id": "ihmisvalvonta",
        "otsikko": "Ihmisen valvonta",
        "kuvaus": "Koulutettu henkilö valvoo järjestelmää ja voi puuttua sen toimintaan (Art. 14)",
        "artikkeli": "Art. 14",
        "deadline": "2.8.2026",
        "prioriteetti": "kriittinen",
    },
    {
        "id": "qms",
        "otsikko": "Laadunhallintajärjestelmä (QMS)",
        "kuvaus": "Yrityksellä on dokumentoitu laadunhallintajärjestelmä AI-järjestelmille (Art. 17)",
        "artikkeli": "Art. 17",
        "deadline": "2.8.2026",
        "prioriteetti": "korkea",
    },
    {
        "id": "riskiarvio",
        "otsikko": "Riskinarviointi dokumentoituna",
        "kuvaus": "Järjestelmän riskit on arvioitu ja dokumentoitu kirjallisesti (Art. 9)",
        "artikkeli": "Art. 9",
        "deadline": "2.8.2026",
        "prioriteetti": "korkea",
    },
    {
        "id": "vaatimustenmukaisuus",
        "otsikko": "Vaatimustenmukaisuusarviointi",
        "kuvaus": "Järjestelmälle on tehty EU AI Act mukainen vaatimustenmukaisuusarviointi (Art. 43)",
        "artikkeli": "Art. 43",
        "deadline": "2.8.2026",
        "prioriteetti": "korkea",
    },
    {
        "id": "eu_rekisteri",
        "otsikko": "EU-tietokantarekisteröinti",
        "kuvaus": "Korkean riskin järjestelmä on rekisteröity EU:n AI-tietokantaan (Art. 49)",
        "artikkeli": "Art. 49",
        "deadline": "2.8.2026",
        "prioriteetti": "korkea",
    },
    {
        "id": "datalaatu",
        "otsikko": "Datan laatu dokumentoitu",
        "kuvaus": "Koulutus- ja syötedatan laatu on dokumentoitu (Art. 10)",
        "artikkeli": "Art. 10",
        "deadline": "2.8.2026",
        "prioriteetti": "normaali",
    },
]

# Vaatimukset rajatun riskin järjestelmille (chatbotit, AI-sisältö)
VAATIMUKSET_RAJATTU = [
    {
        "id": "avoimuusmerkinta",
        "otsikko": "Avoimuusmerkintä",
        "kuvaus": "Käyttäjille kerrotaan selvästi että he ovat vuorovaikutuksessa AI:n kanssa (Art. 50)",
        "artikkeli": "Art. 50",
        "deadline": "2.8.2026",
        "prioriteetti": "kriittinen",
    },
    {
        "id": "ai_sisalto_merkinta",
        "otsikko": "AI-sisällön merkitseminen",
        "kuvaus": "Tekoälyn tuottama sisältö (kuvat, tekstit, videot) merkitään koneellisesti tunnistettavasti",
        "artikkeli": "Art. 50",
        "deadline": "2.8.2026",
        "prioriteetti": "korkea",
    },
]


def luokittele_riski(vastaukset: dict) -> dict:
    """
    Analysoi yksittäisen AI-järjestelmän vastaukset ja palauttaa riskitason + puuttuvat vaatimukset.
    vastaukset = {
        "toimiala": str,
        "autonominen": bool,
        "biometria": bool,
        "kohdistuu_henkiloihin": bool,
        "chatbot": bool,
        "tekninen_dok": bool,
        "lokit": bool,
        "ihmisvalvonta": bool,
        "qms": bool,
        "riskiarvio": bool,
        "vaatimustenmukaisuus": bool,
        "eu_rekisteri": bool,
        "datalaatu": bool,
        "avoimuusmerkinta": bool,
        "ai_sisalto_merkinta": bool,
    }
    """
    toimiala = vastaukset.get("toimiala", "muu")
    biometria = vastaukset.get("biometria", False)
    chatbot = vastaukset.get("chatbot", False)

    # Kielletty AI (Art. 5) — sosiaalinen pisteytys, subliminaalinen manipulaatio
    if vastaukset.get("kielletty", False):
        return {
            "taso": "kielletty",
            "selitys": "Tämä järjestelmä saattaa kuulua EU AI Act 5. artiklan kieltämiin AI-järjestelmiin. Ota välittömästi yhteyttä lakimieheen.",
            "puuttuvat": [],
            "vaaditut": [],
        }

    # Korkea riski
    korkea = (
        toimiala in KORKEA_RISKI_TOIMIALAT
        or biometria
        or vastaukset.get("autonominen", False) and toimiala != "muu"
    )

    if korkea:
        puuttuvat = [
            v for v in VAATIMUKSET
            if not vastaukset.get(v["id"], False)
        ]
        return {
            "taso": "korkea",
            "selitys": f"Järjestelmä luokitellaan korkean riskin AI-järjestelmäksi (Annex III). Täydet compliance-vaatimukset voimassa 2.8.2026.",
            "puuttuvat": puuttuvat,
            "vaaditut": VAATIMUKSET,
        }

    # Rajattu riski (chatbotit, AI-sisältö)
    if chatbot or vastaukset.get("generoi_sisaltoa", False):
        puuttuvat = [
            v for v in VAATIMUKSET_RAJATTU
            if not vastaukset.get(v["id"], False)
        ]
        return {
            "taso": "rajattu",
            "selitys": "Järjestelmä on rajatun riskin AI. Avoimuusvaatimukset voimassa 2.8.2026.",
            "puuttuvat": puuttuvat,
            "vaaditut": VAATIMUKSET_RAJATTU,
        }

    # Minimiriski
    return {
        "taso": "minimaalinen",
        "selitys": "Järjestelmä on minimaalisen riskin AI. Erityisiä lakisääteisiä vaatimuksia ei ole, mutta hyvät käytännöt suositeltavia.",
        "puuttuvat": [],
        "vaaditut": [],
    }


def laske_compliance_pisteet(jarjestelmat: list) -> dict:
    """Laskee kokonais-compliance-pisteytyksen kaikille järjestelmille."""
    if not jarjestelmat:
        return {"pisteet": 0, "taso": "ei_arvioitu", "yhteenveto": "Ei arvioituja järjestelmiä"}

    korkeat = [j for j in jarjestelmat if j["riski"]["taso"] == "korkea"]
    kielletyt = [j for j in jarjestelmat if j["riski"]["taso"] == "kielletty"]

    if kielletyt:
        return {
            "pisteet": 0,
            "taso": "kriittinen",
            "yhteenveto": f"{len(kielletyt)} mahdollisesti kiellettyä järjestelmää — välitön toiminta vaaditaan",
        }

    if not korkeat:
        return {
            "pisteet": 95,
            "taso": "hyva",
            "yhteenveto": "Ei korkean riskin järjestelmiä. Tarkista avoimuusvaatimukset.",
        }

    total_puuttuvat = sum(len(j["riski"]["puuttuvat"]) for j in korkeat)
    total_vaaditut = sum(len(j["riski"]["vaaditut"]) for j in korkeat)
    tehty = total_vaaditut - total_puuttuvat

    pisteet = int((tehty / max(total_vaaditut, 1)) * 100)

    if pisteet >= 80:
        taso = "hyva"
    elif pisteet >= 50:
        taso = "kohtalainen"
    else:
        taso = "heikko"

    return {
        "pisteet": pisteet,
        "taso": taso,
        "yhteenveto": f"{tehty}/{total_vaaditut} vaatimusta täytetty korkean riskin järjestelmissä",
    }
