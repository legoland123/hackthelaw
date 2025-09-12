"""
Configuration for Legal Memory Tool
"""

import os
from pathlib import Path

# Legal websites and search endpoints
LEGAL_SITES = {
    "pair_search": "https://search.pair.gov.sg/",
    "parliament_search": "https://sprs.parl.gov.sg/search/",
    "lawnet_free": "https://www.lawnet.sg/lawnet/web/lawnet/free-resources/",
    "singapore_law_watch": "https://www.singaporelawwatch.sg/",
    "singapore_statutes": "https://sso.agc.gov.sg/",
}

# Legal keywords for contract analysis
LEGAL_KEYWORDS = {
    "contract_terms": [
        "force majeure", "acts of god", "unforeseeable circumstances",
        "termination", "breach", "default", "remedy", "damages",
        "indemnity", "liability", "limitation", "exclusion",
        "warranty", "representation", "covenant", "condition",
        "performance", "delivery", "payment", "consideration"
    ],
    "dispute_resolution": [
        "arbitration", "mediation", "jurisdiction", "governing law",
        "dispute resolution", "court", "tribunal", "settlement"
    ],
    "commercial_terms": [
        "intellectual property", "confidentiality", "non-disclosure",
        "assignment", "novation", "subcontracting", "third party"
    ]
}

# Selenium configuration
SELENIUM_CONFIG = {
    "page_load_timeout": 30,
    "implicit_wait": 10,
    "max_scrolls": 50,
    "scroll_pause_time": 2,
    "headless": True,
    "window_size": (1920, 1080)
}

# Chrome options for stealth browsing
CHROME_OPTIONS = [
    "--no-sandbox",
    "--disable-dev-shm-usage", 
    "--disable-blink-features=AutomationControlled",
    "--disable-web-security",
    "--disable-features=VizDisplayCompositor",
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

# Output directories
BASE_DIR = Path(__file__).parent.parent.parent
CACHE_DIR = BASE_DIR / "cache"
LOGS_DIR = BASE_DIR / "logs"
RESULTS_DIR = BASE_DIR / "results"

# Create directories if they don't exist
for directory in [CACHE_DIR, LOGS_DIR, RESULTS_DIR]:
    directory.mkdir(exist_ok=True)

# Rate limiting (be respectful to websites)
RATE_LIMITS = {
    "site_request_delay": 3,   # seconds between requests to same site
    "max_concurrent_requests": 2
}

# Environment variables (if any)
DEBUG = os.getenv("LEGAL_MEMORY_DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LEGAL_MEMORY_LOG_LEVEL", "INFO")

# User agent rotation for avoiding detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]