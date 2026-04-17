const translations = {
  fi: {
    // Nav
    "nav.guide": "AI Act -opas",
    "nav.dashboard": "Dashboard",
    "nav.new": "+ Uusi kartoitus",
    "nav.upgrade": "Päivitä Pro",
    "nav.logout": "Kirjaudu ulos",
    "nav.login": "Kirjaudu",
    "nav.start": "Aloita ilmaiseksi",

    // Footer
    "footer.copy": "© 2026 ComplianceAI. Kaikki oikeudet pidätetään.",
    "footer.privacy": "Tietosuoja",

    // Hero
    "hero.badge": "⏳ Deadline: 2.8.2026 — enää {n} päivää",
    "hero.h1": "EU pakottaa yritykset<br>auditoimaan AI-käyttönsä",
    "hero.sub": "EU AI Act velvoittaa kaikkia yrityksiä — myös pk-yrityksiä — selvittämään mitä tekoälyjärjestelmiä ne käyttävät ja ovatko ne lain mukaisia. Sakot rikkomuksista ovat jopa <strong>15 miljoonaa euroa tai 3% liikevaihdosta</strong>.<br><br>ComplianceAI auttaa sinua kartoittamaan tilanne, tunnistamaan riskit ja tekemään tarvittavat dokumentit — 15 minuutissa, suomeksi.",
    "hero.cta1": "Tarkista yrityksesi tilanne ilmaiseksi",
    "hero.cta2": "Miten toimii?",
    "hero.note": "Ei luottokorttia. Ensimmäinen kartoitus ilmaiseksi.",

    // Mitä on
    "mita.tag": "Mikä on EU AI Act?",
    "mita.h2": "Euroopan unionin tekoälylaki — velvoittaa kaikki yritykset",
    "mita.p1": "EU AI Act (asetus 2024/1689) on maailman ensimmäinen kattava tekoälyä sääntelevä laki. Se astui voimaan elokuussa 2024 ja velvoittaa kaikkia EU-alueella toimivia yrityksiä — koosta riippumatta.",
    "mita.p2": "Laki jakaa tekoälyjärjestelmät neljään riskiluokkaan: <strong>kielletyt, korkea riski, rajattu riski</strong> ja <strong>minimiriski</strong>. Mitä korkeampi riskiluokka, sitä tiukemmat vaatimukset dokumentaatiolle, valvonnalle ja läpinäkyvyydelle.",
    "mita.p3": "Korkean riskin järjestelmille — kuten rekrytointiin, luottopäätöksiin tai terveydenhuoltoon käytettävät AI-työkalut — täydet compliance-vaatimukset tulevat voimaan <strong>2.8.2026</strong>.",
    "mita.examples": "Esimerkkejä korkean riskin järjestelmistä:",
    "mita.ex1.title": "Rekrytointi-AI",
    "mita.ex1.desc": "CV:n automaattinen pisteytys tai hylkäys.",
    "mita.ex2.title": "Luottopäätösalgoritmi",
    "mita.ex2.desc": "Automaattiset laina- tai vakuutuspäätökset",
    "mita.ex3.title": "Asiakaspalveluchatbot",
    "mita.ex3.desc": "AI joka kommunikoi asiakkaiden kanssa",
    "mita.ex4.title": "Sisäinen kirjoitusapuri",
    "mita.ex4.desc": "ChatGPT tekstien kirjoittamiseen sisäisesti",
    "mita.legend.high": "Korkea riski",
    "mita.legend.limited": "Rajattu riski",
    "mita.legend.min": "Minimiriski",

    // Urgency
    "urgency.1": "liikevaihdosta tai 15M€ — sakko vaatimustenvastaisuudesta",
    "urgency.2": "pk-yrityksistä on valmistautunut AI Act:iin",
    "urgency.3": "täysi compliance-deadline korkean riskin järjestelmille",

    // Miten toimii
    "how.h2": "Miten se toimii?",
    "how.s1.h3": "Kartoita järjestelmät",
    "how.s1.p": "Kerro mitä AI-työkaluja yrityksenne käyttää — rekrytoinnissa, asiakaspalvelussa, päätöksenteossa.",
    "how.s2.h3": "Saat riskiluokituksen",
    "how.s2.p": "Järjestelmä analysoi vastaukset EU AI Act:n mukaan ja kertoo onko riski kielletty, korkea, rajattu vai minimaalinen.",
    "how.s3.h3": "Tunnista puutteet",
    "how.s3.p": "Näet tarkalleen mitä vaatimuksia puuttuu — tekninen dokumentaatio, lokit, ihmisvalvonta, QMS.",
    "how.s4.h3": "Lataa PDF-raportti",
    "how.s4.p": "Pro-tilaajat saavat valmiin PDF-raportin viranomaisraportointia varten. Ilmaisella tilillä näet tulokset ruudulla.",

    // FAQ
    "faq.h2": "Usein kysytyt kysymykset",
    "faq.q1": "Koskeeko EU AI Act minun yritystäni?",
    "faq.a1": "Kyllä, jos yrityksesi käyttää tai tarjoaa tekoälyjärjestelmiä EU:ssa. Tämä koskee myös pk-yrityksiä jotka käyttävät esim. ChatGPT:tä rekrytoinnissa, AI-chatbottia asiakaspalvelussa tai automaattista päätöksentekoa. Laki tuli voimaan 2024 ja ensimmäiset velvoitteet astuivat voimaan helmikuussa 2025.",
    "faq.q2": "Mitä tapahtuu jos en tee mitään?",
    "faq.a2": "Vaatimustenvastaisuudesta voi seurata sakko joka on jopa 3% vuotuisesta liikevaihdosta tai 15 miljoonaa euroa — sen mukaan kumpi on suurempi. Valvontaviranomainen Suomessa on Liikenne- ja viestintävirasto Traficom.",
    "faq.q3": "Käytämme vain ChatGPT:tä — koskeeko tämä meitä?",
    "faq.a3": "Se riippuu mihin käytätte sitä. Jos ChatGPT on integroitu asiakaspalvelubottiin tai sen avulla tehdään päätöksiä jotka vaikuttavat ihmisiin (esim. rekrytointi), avoimuusvaatimukset koskevat teitä. Pelkkä sisäinen käyttö tekstien kirjoittamiseen on yleensä minimiriskiluokassa.",
    "faq.q4": "Kuinka kauan kartoitus kestää?",
    "faq.a4": "Yhden AI-järjestelmän kartoitus vie noin 10–15 minuuttia. Saat heti riskiluokituksen ja listan puuttuvista vaatimuksista. Kartoituksia voi tehdä niin monta kuin yrityksellä on AI-järjestelmiä.",
    "faq.q5": "Korvataanko tällä lakimies?",
    "faq.a5": "Ei. ComplianceAI auttaa tunnistamaan riskit ja tekemään pohjatyön, mutta ennen viranomaisdokumentointia suosittelemme tarkistuttamaan materiaalit lakimiehellä. Työkalu säästää huomattavasti aikaa ja rahaa koska pohjatyö on jo tehty.",
    "faq.q6": "Onko data turvassa?",
    "faq.a6": "Kartoitustietoja ei jaeta kolmansille osapuolille. Data tallennetaan suojatusti ja sitä käytetään vain compliance-analyysin tuottamiseen.",

    // Hinnoittelu
    "price.h2": "Hinnoittelu",
    "price.free.name": "Ilmainen",
    "price.free.li1": "1 AI-järjestelmän kartoitus",
    "price.free.li2": "Riskiluokitus",
    "price.free.li3": "Gap-analyysi",
    "price.free.li4": "PDF-raportti",
    "price.free.li5": "Rajoittamattomat kartoitukset",
    "price.free.li6": "Deadline-seuranta",
    "price.free.btn": "Aloita",
    "price.pro.badge": "Suosituin",
    "price.pro.name": "Pro",
    "price.pro.per": "/kk",
    "price.pro.li1": "Rajoittamattomat kartoitukset",
    "price.pro.li2": "Riskiluokitus kaikille järjestelmille",
    "price.pro.li3": "Gap-analyysi",
    "price.pro.li4": "PDF-raportit viranomaisille",
    "price.pro.li5": "Deadline-seuranta ja muistutukset",
    "price.pro.li6": "Dokumenttipohjat suomeksi",
    "price.pro.btn.upgrade": "Päivitä Pro — 49€/kk",
    "price.pro.btn.start": "Aloita — 49€/kk",
    "price.note": "ALV 0%. Peruuta milloin tahansa. Ei sitoutumisaikaa.",

    // CTA bottom
    "cta.h2": "AI Act deadline lähestyy.<br>Tarkista tilanne nyt.",
    "cta.btn": "Aloita ilmainen kartoitus",

    // Kirjaudu
    "login.h1": "Kirjaudu sisään",
    "login.sub": "ComplianceAI-tili",
    "login.email": "Sähköposti",
    "login.pwd": "Salasana",
    "login.btn": "Kirjaudu sisään",
    "login.forgot": "Unohditko salasanan?",
    "login.no_account": "Ei tiliä vielä?",
    "login.register": "Rekisteröidy ilmaiseksi",

    // Rekisteri
    "reg.h1": "Luo ilmainen tili",
    "reg.sub": "Ensimmäinen kartoitus ilmaiseksi — ei luottokorttia.",
    "reg.company": "Yrityksen nimi",
    "reg.email": "Sähköposti",
    "reg.pwd": "Salasana",
    "reg.ytunnus": "Y-tunnus",
    "reg.optional": "(valinnainen)",
    "reg.size": "Yrityksen koko",
    "reg.size.select": "Valitse...",
    "reg.size.1": "1–10 henkilöä",
    "reg.size.2": "11–50 henkilöä",
    "reg.size.3": "51–250 henkilöä",
    "reg.size.4": "Yli 250 henkilöä",
    "reg.btn": "Luo tili →",
    "reg.have_account": "Onko sinulla jo tili?",
    "reg.login": "Kirjaudu sisään",
  },

  en: {
    // Nav
    "nav.guide": "AI Act Guide",
    "nav.dashboard": "Dashboard",
    "nav.new": "+ New assessment",
    "nav.upgrade": "Upgrade to Pro",
    "nav.logout": "Log out",
    "nav.login": "Log in",
    "nav.start": "Start for free",

    // Footer
    "footer.copy": "© 2026 ComplianceAI. All rights reserved.",
    "footer.privacy": "Privacy policy",

    // Hero
    "hero.badge": "⏳ Deadline: 2 Aug 2026 — {n} days left",
    "hero.h1": "The EU requires companies<br>to audit their AI usage",
    "hero.sub": "The EU AI Act obligates all companies — including SMEs — to identify which AI systems they use and whether they comply with the law. Fines for non-compliance can reach <strong>€15 million or 3% of annual turnover</strong>.<br><br>ComplianceAI helps you map your situation, identify risks and prepare the required documentation — in 15 minutes.",
    "hero.cta1": "Check your company's status for free",
    "hero.cta2": "How does it work?",
    "hero.note": "No credit card. First assessment free.",

    // Mitä on
    "mita.tag": "What is the EU AI Act?",
    "mita.h2": "The EU Artificial Intelligence Act — applies to all companies",
    "mita.p1": "The EU AI Act (Regulation 2024/1689) is the world's first comprehensive law regulating artificial intelligence. It entered into force in August 2024 and applies to all companies operating in the EU — regardless of size.",
    "mita.p2": "The law divides AI systems into four risk categories: <strong>prohibited, high risk, limited risk</strong> and <strong>minimal risk</strong>. The higher the risk category, the stricter the requirements for documentation, oversight and transparency.",
    "mita.p3": "For high-risk systems — such as AI tools used in recruitment, credit decisions or healthcare — full compliance requirements take effect on <strong>2 August 2026</strong>.",
    "mita.examples": "Examples of high-risk systems:",
    "mita.ex1.title": "Recruitment AI",
    "mita.ex1.desc": "Automatic CV scoring or rejection.",
    "mita.ex2.title": "Credit decision algorithm",
    "mita.ex2.desc": "Automated loan or insurance decisions",
    "mita.ex3.title": "Customer service chatbot",
    "mita.ex3.desc": "AI that communicates directly with customers",
    "mita.ex4.title": "Internal writing assistant",
    "mita.ex4.desc": "ChatGPT used internally for writing",
    "mita.legend.high": "High risk",
    "mita.legend.limited": "Limited risk",
    "mita.legend.min": "Minimal risk",

    // Urgency
    "urgency.1": "of turnover or €15M — fine for non-compliance",
    "urgency.2": "of SMEs have prepared for the AI Act",
    "urgency.3": "full compliance deadline for high-risk systems",

    // Miten toimii
    "how.h2": "How does it work?",
    "how.s1.h3": "Map your AI systems",
    "how.s1.p": "Tell us which AI tools your company uses — in recruitment, customer service, decision-making.",
    "how.s2.h3": "Get a risk classification",
    "how.s2.p": "The system analyses your answers according to the EU AI Act and tells you whether the risk is prohibited, high, limited or minimal.",
    "how.s3.h3": "Identify gaps",
    "how.s3.p": "See exactly which requirements are missing — technical documentation, logs, human oversight, QMS.",
    "how.s4.h3": "Download PDF report",
    "how.s4.p": "Pro subscribers receive a ready-made PDF report for regulatory reporting. Free accounts see results on screen.",

    // FAQ
    "faq.h2": "Frequently asked questions",
    "faq.q1": "Does the EU AI Act apply to my company?",
    "faq.a1": "Yes, if your company uses or provides AI systems in the EU. This includes SMEs using ChatGPT for recruitment, AI chatbots for customer service, or automated decision-making. The law entered into force in 2024 and first obligations took effect in February 2025.",
    "faq.q2": "What happens if I do nothing?",
    "faq.a2": "Non-compliance can result in a fine of up to 3% of annual turnover or €15 million — whichever is greater. The supervisory authority in Finland is the Finnish Transport and Communications Agency Traficom.",
    "faq.q3": "We only use ChatGPT — does this apply to us?",
    "faq.a3": "It depends on how you use it. If ChatGPT is integrated into a customer service bot or used to make decisions affecting people (e.g. recruitment), transparency requirements apply to you. Internal use for writing assistance is generally in the minimal risk category.",
    "faq.q4": "How long does the assessment take?",
    "faq.a4": "Assessing one AI system takes about 10–15 minutes. You immediately get a risk classification and a list of missing requirements. You can do as many assessments as your company has AI systems.",
    "faq.q5": "Does this replace a lawyer?",
    "faq.a5": "No. ComplianceAI helps identify risks and do the groundwork, but we recommend having the materials reviewed by a lawyer before submitting to authorities. The tool saves significant time and money because the groundwork is already done.",
    "faq.q6": "Is the data secure?",
    "faq.a6": "Assessment data is not shared with third parties. Data is stored securely and used only for compliance analysis.",

    // Hinnoittelu
    "price.h2": "Pricing",
    "price.free.name": "Free",
    "price.free.li1": "1 AI system assessment",
    "price.free.li2": "Risk classification",
    "price.free.li3": "Gap analysis",
    "price.free.li4": "PDF report",
    "price.free.li5": "Unlimited assessments",
    "price.free.li6": "Deadline tracking",
    "price.free.btn": "Get started",
    "price.pro.badge": "Most popular",
    "price.pro.name": "Pro",
    "price.pro.per": "/mo",
    "price.pro.li1": "Unlimited assessments",
    "price.pro.li2": "Risk classification for all systems",
    "price.pro.li3": "Gap analysis",
    "price.pro.li4": "PDF reports for authorities",
    "price.pro.li5": "Deadline tracking and reminders",
    "price.pro.li6": "Document templates in English",
    "price.pro.btn.upgrade": "Upgrade to Pro — €49/mo",
    "price.pro.btn.start": "Get started — €49/mo",
    "price.note": "VAT 0%. Cancel anytime. No commitment.",

    // CTA bottom
    "cta.h2": "The AI Act deadline is approaching.<br>Check your status now.",
    "cta.btn": "Start free assessment",

    // Kirjaudu
    "login.h1": "Log in",
    "login.sub": "ComplianceAI account",
    "login.email": "Email",
    "login.pwd": "Password",
    "login.btn": "Log in",
    "login.forgot": "Forgot password?",
    "login.no_account": "No account yet?",
    "login.register": "Register for free",

    // Rekisteri
    "reg.h1": "Create free account",
    "reg.sub": "First assessment free — no credit card required.",
    "reg.company": "Company name",
    "reg.email": "Email",
    "reg.pwd": "Password",
    "reg.ytunnus": "Business ID",
    "reg.optional": "(optional)",
    "reg.size": "Company size",
    "reg.size.select": "Select...",
    "reg.size.1": "1–10 employees",
    "reg.size.2": "11–50 employees",
    "reg.size.3": "51–250 employees",
    "reg.size.4": "Over 250 employees",
    "reg.btn": "Create account →",
    "reg.have_account": "Already have an account?",
    "reg.login": "Log in",
  }
};

let currentLang = localStorage.getItem("aiact_lang") || "fi";

function applyLang(lang) {
  currentLang = lang;
  localStorage.setItem("aiact_lang", lang);
  const t = translations[lang];

  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (t[key] !== undefined) {
      if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
        el.placeholder = t[key];
      } else {
        el.textContent = t[key];
      }
    }
  });

  document.querySelectorAll("[data-i18n-html]").forEach(el => {
    const key = el.getAttribute("data-i18n-html");
    if (t[key] !== undefined) el.innerHTML = t[key];
  });

  // Kielinapit
  document.querySelectorAll(".lang-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.lang === lang);
  });

  // html lang-attribuutti
  document.documentElement.lang = lang === "fi" ? "fi" : "en";
}

document.addEventListener("DOMContentLoaded", () => applyLang(currentLang));
