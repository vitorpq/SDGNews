import os
from dotenv import load_dotenv

load_dotenv()

# --- OpenRouter ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "google/gemini-2.5-flash"

# --- API Keys ---
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
PERIGON_API_KEY = os.getenv("PERIGON_API_KEY")

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Tickers Brasil ---
TICKERS_BR = {
    "ibovespa": "^BVSP",
    "usd_brl": "USDBRL=X",
    "eur_brl": "EURBRL=X",
    "petr4": "PETR4.SA",
    "vale3": "VALE3.SA",
    "itub4": "ITUB4.SA",
    "bbdc4": "BBDC4.SA",
    "mglu3": "MGLU3.SA",
}

TICKERS_COMMODITIES = {
    "petroleo_wti": "CL=F",
    "petroleo_brent": "BZ=F",
    "ouro": "GC=F",
    "soja": "ZS=F",
    "milho": "ZC=F",
}

TICKERS_GLOBAL = {
    "sp500": "^GSPC",
    "nasdaq": "^IXIC",
    "dxy": "DX-Y.NYB",
    "treasury_10y": "^TNX",
}

# --- Periodos ---
ANALYSIS_PERIOD = "5d"  # busca 5 dias para garantir D-1 util

# --- Paths ---
SQLITE_DB_PATH = "./data/sqlite/digests.db"
OUTPUT_DIR = "./data/outputs"
