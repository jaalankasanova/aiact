MAAKUNNAT = {
    "Uusimaa": [
        "Helsinki","Espoo","Vantaa","Porvoo","Hyvinkää","Järvenpää","Kerava",
        "Lohja","Tuusula","Nurmijärvi","Kirkkonummi","Sipoo","Mäntsälä",
        "Loviisa","Raasepori","Hanko","Inkoo","Karkkila","Vihti","Askola"
    ],
    "Varsinais-Suomi": [
        "Turku","Salo","Naantali","Uusikaupunki","Raisio","Kaarina","Lieto",
        "Paimio","Somero","Parainen","Loimaa","Mynämäki","Nousiainen","Pöytyä"
    ],
    "Satakunta": [
        "Pori","Rauma","Harjavalta","Huittinen","Kankaanpää","Ulvila",
        "Kokemäki","Nakkila","Säkylä","Eurajoki","Eura","Merikarvia"
    ],
    "Kanta-Häme": [
        "Hämeenlinna","Forssa","Riihimäki","Tammela","Loppi","Janakkala",
        "Hattula","Humppila","Jokioinen","Ypäjä","Hausjärvi","Kärkölä"
    ],
    "Pirkanmaa": [
        "Tampere","Nokia","Ylöjärvi","Kangasala","Lempäälä","Valkeakoski",
        "Mänttä-Vilppula","Orivesi","Virrat","Parkano","Ikaalinen","Pälkäne",
        "Hämeenkyrö","Ruovesi","Juupajoki","Punkalaidun","Akaa"
    ],
    "Päijät-Häme": [
        "Lahti","Heinola","Hollola","Orimattila","Asikkala","Padasjoki",
        "Sysmä","Artjärvi","Hartola","Iitti"
    ],
    "Kymenlaakso": [
        "Kouvola","Kotka","Hamina","Pyhtää","Miehikkälä","Virolahti"
    ],
    "Etelä-Karjala": [
        "Lappeenranta","Imatra","Lemi","Luumäki","Ruokolahti","Savitaipale",
        "Taipalsaari","Parikkala","Rautjärvi","Suomenniemi"
    ],
    "Etelä-Savo": [
        "Mikkeli","Savonlinna","Pieksämäki","Juva","Hirvensalmi",
        "Kangasniemi","Mäntyharju","Pertunmaa","Puumala","Rantasalmi",
        "Joroinen","Heinävesi","Enonkoski","Sulkava"
    ],
    "Pohjois-Savo": [
        "Kuopio","Iisalmi","Varkaus","Siilinjärvi","Suonenjoki","Leppävirta",
        "Kiuruvesi","Pielavesi","Rautalampi","Keitele","Nilsiä","Riistavesi",
        "Kaavi","Tuusniemi","Sonkajärvi","Lapinlahti","Vesanto"
    ],
    "Pohjois-Karjala": [
        "Joensuu","Lieksa","Nurmes","Outokumpu","Kitee","Kontiolahti",
        "Liperi","Polvijärvi","Juuka","Rääkkylä","Tohmajärvi","Valtimo",
        "Ilomantsi","Heinävesi"
    ],
    "Keski-Suomi": [
        "Jyväskylä","Jämsä","Äänekoski","Saarijärvi","Keuruu","Laukaa",
        "Muurame","Viitasaari","Pihtipudas","Kivijärvi","Konnevesi",
        "Toivakka","Uurainen","Petäjävesi","Multia"
    ],
    "Etelä-Pohjanmaa": [
        "Seinäjoki","Kauhajoki","Kurikka","Lapua","Kauhava","Alajärvi",
        "Alavus","Isokyrö","Ilmajoki","Jalasjärvi","Teuva","Ähtäri",
        "Soini","Vimpeli","Evijärvi","Lappajärvi","Töysä"
    ],
    "Pohjanmaa": [
        "Vaasa","Mustasaari","Pietarsaari","Uusikaarlepyy","Kaskinen",
        "Kristiinankaupunki","Närpiö","Korsnäs","Maalahti","Isokyrö",
        "Vöyri","Laihia","Oravainen"
    ],
    "Keski-Pohjanmaa": [
        "Kokkola","Kannus","Toholampi","Veteli","Halsua","Lestijärvi",
        "Perho","Reisjärvi","Sievi","Kaustinen"
    ],
    "Pohjois-Pohjanmaa": [
        "Oulu","Raahe","Oulainen","Kalajoki","Ylivieska","Haapajärvi",
        "Kuusamo","Pudasjärvi","Ii","Kempele","Liminka","Tyrnävä",
        "Muhos","Utajärvi","Vaala","Siikajoki","Pyhäjoki","Merijärvi",
        "Alavieska","Haapavesi","Pyhäjärvi","Kärsämäki","Nivala","Taivalkoski",
        "Kuivaniemi","Hailuoto"
    ],
    "Kainuu": [
        "Kajaani","Kuhmo","Sotkamo","Suomussalmi","Paltamo","Ristijärvi",
        "Hyrynsalmi","Puolanka","Vaala"
    ],
    "Lappi": [
        "Rovaniemi","Kemi","Tornio","Kemijärvi","Sodankylä","Inari",
        "Muonio","Enontekiö","Utsjoki","Kittilä","Kolari","Pello",
        "Ylitornio","Ranua","Posio","Salla","Savukoski","Pelkosenniemi",
        "Simon","Tervola","Keminmaa"
    ],
    "Ahvenanmaa": [
        "Maarianhamina","Jomala","Lemland","Saltvik","Finström","Sund",
        "Geta","Hammarland","Eckerö","Mariehamn"
    ],
}

# Kaikki kaupungit listana
KAIKKI_KAUPUNGIT = sorted(
    {k for kaupungit in MAAKUNNAT.values() for k in kaupungit}
)

def maakunta_kaupungille(kaupunki):
    for mk, kaupungit in MAAKUNNAT.items():
        if kaupunki in kaupungit:
            return mk
    return None
