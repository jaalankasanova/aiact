"""Finvoice 3.0 XML -generaattori ja Maventa-lähetys"""
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import os, requests


def _ovt(ytunnus: str) -> str:
    """Y-tunnus 1234567-8 → OVT-tunnus 003712345678"""
    return "0037" + ytunnus.replace("-", "")


def luo_finvoice(tilaus: dict, tarjous: dict, laskun_numero: str) -> str:
    """Palauttaa Finvoice 3.0 XML-merkkijonon."""

    # Myyjä (Rahtari-alusta) ympäristömuuttujista
    myyja_yritys  = os.environ.get("RAHTARI_YRITYS",       "Rahtari")
    myyja_ytunnus = os.environ.get("RAHTARI_YTUNNUS",       "")
    myyja_ovt     = os.environ.get("RAHTARI_OVT",           _ovt(myyja_ytunnus) if myyja_ytunnus else "")
    myyja_osoite  = os.environ.get("RAHTARI_OSOITE",        "")
    myyja_posti   = os.environ.get("RAHTARI_POSTINUMERO",   "")
    myyja_kaupunki= os.environ.get("RAHTARI_KAUPUNKI",      "")
    myyja_iban    = os.environ.get("RAHTARI_IBAN",           "")
    myyja_bic     = os.environ.get("RAHTARI_BIC",            "")

    # Ostaja (tilaaja)
    ostaja_yritys  = tilaus["yritys"]
    ostaja_ytunnus = tilaus["ytunnus"]
    ostaja_ovt     = tilaus.get("ovt_tunnus") or _ovt(ostaja_ytunnus)

    nyt       = datetime.now()
    erapaiva  = nyt + timedelta(days=14)
    pvm_fmt   = nyt.strftime("%Y%m%d")
    era_fmt   = erapaiva.strftime("%Y%m%d")

    veroton   = round(tarjous["hinta"], 2)
    alv_pros  = 25.5
    alv       = round(veroton * alv_pros / 100, 2)
    yht       = round(veroton + alv, 2)

    def e(tag, text=None, **attribs):
        el = ET.Element(tag, attribs)
        if text is not None:
            el.text = str(text)
        return el

    root = ET.Element("Finvoice", Version="3.0")

    # MessageTransmissionDetails
    mtd = ET.SubElement(root, "MessageTransmissionDetails")
    ET.SubElement(mtd, "MessageSenderId").text    = myyja_ovt
    ET.SubElement(mtd, "MessageReceiverId").text  = ostaja_ovt
    ET.SubElement(mtd, "MessageTimestamp").text   = nyt.strftime("%Y-%m-%dT%H:%M:%S")

    # SellerPartyDetails
    spd = ET.SubElement(root, "SellerPartyDetails")
    ET.SubElement(spd, "SellerPartyIdentifier").text  = myyja_ytunnus
    ET.SubElement(spd, "SellerOrganisationName").text = myyja_yritys
    addr = ET.SubElement(spd, "SellerPostalAddressDetails")
    ET.SubElement(addr, "SellerStreetName").text           = myyja_osoite
    ET.SubElement(addr, "SellerTownName").text             = myyja_kaupunki
    ET.SubElement(addr, "SellerPostCodeIdentifier").text   = myyja_posti
    ET.SubElement(addr, "CountryCode").text                = "FI"

    # SellerCommunicationDetails
    scd = ET.SubElement(root, "SellerCommunicationDetails")
    ET.SubElement(scd, "SellerEmailaddressIdentifier").text = os.environ.get("EMAIL_FROM", "")

    # BuyerPartyDetails
    bpd = ET.SubElement(root, "BuyerPartyDetails")
    ET.SubElement(bpd, "BuyerPartyIdentifier").text  = ostaja_ytunnus
    ET.SubElement(bpd, "BuyerOrganisationName").text = ostaja_yritys

    # InvoiceDetails
    ind = ET.SubElement(root, "InvoiceDetails")
    ET.SubElement(ind, "InvoiceTypeCode").text    = "INV01"
    ET.SubElement(ind, "InvoiceNumber").text      = laskun_numero
    ET.SubElement(ind, "InvoiceDate", Format="CCYYMMDD").text = pvm_fmt
    ET.SubElement(ind, "InvoiceDueDate", Format="CCYYMMDD").text = era_fmt
    ET.SubElement(ind, "InvoiceTotalVatExcludedAmount",
                  AmountCurrencyIdentifier="EUR").text = f"{veroton:.2f}"
    ET.SubElement(ind, "InvoiceTotalVatAmount",
                  AmountCurrencyIdentifier="EUR").text = f"{alv:.2f}"
    ET.SubElement(ind, "InvoiceTotalVatIncludedAmount",
                  AmountCurrencyIdentifier="EUR").text = f"{yht:.2f}"
    ET.SubElement(ind, "PaymentTermsDetails").text = "14 pv netto"

    # InvoiceRow
    row = ET.SubElement(root, "InvoiceRow")
    ET.SubElement(row, "ArticleName").text = (
        f"Kuljetuspalvelu: {tilaus['lahto_kaupunki']} → {tilaus['toimitus']}"
    )
    ET.SubElement(row, "DeliveredQuantity", QuantityUnitCode="kpl").text = "1"
    ET.SubElement(row, "UnitPriceAmount",
                  AmountCurrencyIdentifier="EUR").text = f"{veroton:.2f}"
    ET.SubElement(row, "RowVatRatePercent").text = f"{alv_pros}"
    ET.SubElement(row, "RowVatAmount",
                  AmountCurrencyIdentifier="EUR").text = f"{alv:.2f}"
    ET.SubElement(row, "RowVatExcludedAmount",
                  AmountCurrencyIdentifier="EUR").text = f"{veroton:.2f}"
    ET.SubElement(row, "RowAmount",
                  AmountCurrencyIdentifier="EUR").text = f"{yht:.2f}"

    # EpiDetails (maksutiedot)
    epi = ET.SubElement(root, "EpiDetails")
    eid = ET.SubElement(epi, "EpiIdentificationDetails")
    ET.SubElement(eid, "EpiDate", Format="CCYYMMDD").text = era_fmt
    ET.SubElement(eid, "EpiReference").text = laskun_numero
    epd = ET.SubElement(epi, "EpiPartyDetails")
    ET.SubElement(epd, "EpiBfiIdentificationCode").text  = myyja_bic
    ET.SubElement(epd, "EpiAccountID",
                  IdentificationSchemeName="IBAN").text  = myyja_iban
    epay = ET.SubElement(epi, "EpiPaymentInstructionDetails")
    ET.SubElement(epay, "EpiPaymentInstructionId").text  = laskun_numero
    ET.SubElement(epay, "EpiTransactionTypeCode").text   = "TRF"
    ET.SubElement(epay, "EpiInstructedAmountAmount",
                  AmountCurrencyIdentifier="EUR").text   = f"{yht:.2f}"
    ET.SubElement(epay, "EpiDate", Format="CCYYMMDD").text = era_fmt
    ET.SubElement(epay, "EpiRemittanceInfoIdentifier",
                  IdentificationSchemeAgencyIdentifier="SPY").text = laskun_numero

    ET.indent(root, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")


def laheta_maventa(xml_str: str, laskun_numero: str) -> dict:
    """Lähettää Finvoice-XML:n Maventaan. Palauttaa {'ok': True} tai {'ok': False, 'virhe': ...}"""
    uuid      = os.environ.get("MAVENTA_UUID", "")
    api_key   = os.environ.get("MAVENTA_API_KEY", "")
    api_url   = os.environ.get("MAVENTA_API_URL", "https://api.maventa.com/v1/invoices")

    if not uuid or not api_key:
        return {"ok": False, "virhe": "MAVENTA_UUID tai MAVENTA_API_KEY puuttuu .env:stä"}

    try:
        r = requests.post(
            api_url,
            auth=(uuid, api_key),
            headers={"Content-Type": "application/xml; charset=utf-8"},
            data=xml_str.encode("utf-8"),
            timeout=15,
        )
        if r.status_code in (200, 201):
            return {"ok": True}
        return {"ok": False, "virhe": f"HTTP {r.status_code}: {r.text[:300]}"}
    except Exception as ex:
        return {"ok": False, "virhe": str(ex)}
