"""
Configuration and Constants

Contains all URLs, patterns, and configuration values for the scraper.
"""

# URLs
BASE_URL = "https://www.ipsos.com"
BAROMETER_URL = "https://www.ipsos.com/fr-fr/barometre-politique-ipsos-bva-la-tribune-dimanche"

# Flourish patterns
FLOURISH_VIZ_PATTERN = r'visualisation/(\d+)'
FLOURISH_EMBED_TEMPLATE = "https://flo.uri.sh/visualisation/{}/embed?auto=1"

# HTTP Headers to mimic a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# French month names mapping
MONTH_MAP = {
    "janvier": 1, "février": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12
}

# Politician names for candidate data detection
POLITICIAN_INDICATORS = [
    "Bardella", "Le Pen", "Mélenchon", "Macron",
    "Philippe", "Darmanin", "Attal", "Hollande",
    "Glucksmann", "Zemmour", "Roussel", "Bertrand",
    "Retailleau", "Ruffin", "Ciotti", "Tondelier"
]
