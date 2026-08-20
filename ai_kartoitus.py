"""AI-avusteinen kartoituksen esitäyttö. Käyttäjä kuvailee vapaalla tekstillä miten
tekoälyä käytetään yrityksessä, ja Claude päättelee kuvauksesta kartoituslomakkeen
kentät (toimiala, ominaisuudet). Käyttäjä tarkistaa ja täydentää tulokset normaalin
3-vaiheisen kartoituslomakkeen kautta ennen tallennusta — AI ei tallenna mitään suoraan.
"""
import json
import anthropic

from kysymykset import TOIMIALAT

client = anthropic.Anthropic()
MODEL = "claude-sonnet-5"

_TOIMIALA_IDS = [arvo for arvo, _ in TOIMIALAT]

SYSTEM = (
    "Olet EU AI Act -compliance-työkalun avustaja. Käyttäjä kuvailee vapaalla tekstillä "
    "miten heidän yrityksessään käytetään tekoälyä yhdessä järjestelmässä/työkalussa. "
    "Tehtäväsi on poimia kuvauksesta kartoituslomakkeen kentät. Ole konservatiivinen: "
    "jos et ole varma jostain ominaisuudesta, merkitse se todennäköisemmin true kuin false "
    "— parempi yliarvioida riski kuin aliarvioida. Vastaa suomeksi."
)

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "nimi": {"type": "string", "description": "Lyhyt tunnistettava nimi järjestelmälle, esim. 'ChatGPT rekrytoinnissa'"},
        "kuvaus": {"type": "string", "description": "1-2 lauseen tiivistelmä käyttötarkoituksesta"},
        "toimiala": {"type": "string", "enum": _TOIMIALA_IDS},
        "rooli": {"type": "string", "enum": ["deployer", "provider"], "description": "deployer = ostettu/valmis työkalu, provider = itse kehitetty"},
        "autonominen": {"type": "boolean", "description": "Tekeekö järjestelmä automaattisia päätöksiä ilman ihmisen tarkistusta"},
        "kohdistuu_henkiloihin": {"type": "boolean", "description": "Vaikuttavatko päätökset suoraan luonnollisiin henkilöihin"},
        "biometria": {"type": "boolean", "description": "Käsitteleekö biometrisiä tietoja (kasvot, sormenjälki, ääni)"},
        "chatbot": {"type": "boolean", "description": "Onko kyseessä chatbot tai AI-assistentti joka keskustelee ihmisten kanssa"},
        "generoi_sisaltoa": {"type": "boolean", "description": "Generoiko tekstiä, kuvia tai muuta sisältöä"},
        "kielletty": {"type": "boolean", "description": "Viittaako kuvaus sosiaaliseen pisteytykseen tai alitajuiseen manipulointiin (Art. 5)"},
        "perustelu": {"type": "string", "description": "1-2 lauseen selitys miksi nämä valinnat tehtiin, näytetään käyttäjälle"},
    },
    "required": [
        "nimi", "kuvaus", "toimiala", "rooli", "autonominen", "kohdistuu_henkiloihin",
        "biometria", "chatbot", "generoi_sisaltoa", "kielletty", "perustelu",
    ],
    "additionalProperties": False,
}


def analysoi_kuvaus(kuvaus_teksti: str) -> dict:
    """Palauttaa dictin joka vastaa session['kartoitus']-rakennetta (nimi, kuvaus,
    toimiala, rooli + ominaisuus-boolean-kentät) sekä 'perustelu'-tekstin."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM,
        thinking={"type": "adaptive"},
        output_config={
            "effort": "medium",
            "format": {"type": "json_schema", "schema": RESPONSE_SCHEMA},
        },
        messages=[{"role": "user", "content": f"Kuvaus tekoälyn käytöstä:\n\"{kuvaus_teksti.strip()}\""}],
    )

    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)
