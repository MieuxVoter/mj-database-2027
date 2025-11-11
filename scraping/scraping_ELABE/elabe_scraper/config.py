"""
Configuration Module

Constants and configuration for ELABE barometer scraping.
"""

# Base URLs
BASE_URL = "https://elabe.fr"
BAROMETER_URL_TEMPLATE_WITH_DASH = "https://elabe.fr/barometre-politique-{month_name}-{year}/"
BAROMETER_URL_TEMPLATE_NO_DASH = "https://elabe.fr/barometre-politique-{month_name}{year}/"

# Month name mapping (French short form used in URLs)
MONTH_URL_MAP = {
    1: "janvier",
    2: "fevrier",
    3: "mars",
    4: "avril",
    5: "mai",
    6: "juin",
    7: "juillet",
    8: "aout",
    9: "septembre",
    10: "oct",
    11: "nov",
    12: "dec"
}

# Month name mapping (French full name for parsing)
MONTH_NAME_MAP = {
    "janvier": 1,
    "février": 2,
    "fevrier": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "aout": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
    "decembre": 12,
}

# PDF patterns
PDF_LINK_PATTERN = r'Télécharger le rapport.*?href="(https://elabe\.fr/wp-content/uploads/[^"]+\.pdf)"'
PDF_FILENAME_PATTERN = r'/(\d{8})_les_echos_observatoire-politique\.pdf'

# HTTP Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}
