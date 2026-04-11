import yfinance as yf
from datetime import date, datetime, timedelta
from config.settings import TICKERS_BR, TICKERS_COMMODITIES, TICKERS_GLOBAL, ANALYSIS_PERIOD


def _get_last_business_day() -> date:
    """Retorna o ultimo dia util (D-1) antes de hoje."""
    hoje = datetime.now().date()
    d = hoje - timedelta(days=1)
    # Pular fim de semana: sabado=5, domingo=6
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def get_yesterday_data(ticker_symbol: str) -> dict:
    """Busca dados de fechamento do ultimo dia util (D-1) usando data explicita."""
    try:
        target_date = _get_last_business_day()

        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=ANALYSIS_PERIOD)
        if hist.empty:
            return {"erro": f"Dados insuficientes para {ticker_symbol}"}

        # Normalizar indice para date (sem timezone)
        if hasattr(hist.index, 'tz') and hist.index.tz is not None:
            hist.index = hist.index.tz_localize(None)
        dates = [d.date() for d in hist.index]

        # Encontrar a linha correspondente a D-1
        if target_date in dates:
            idx = dates.index(target_date)
        else:
            # Fallback: pegar o ultimo dia disponivel <= target_date
            valid = [(i, d) for i, d in enumerate(dates) if d <= target_date]
            if not valid:
                return {"erro": f"Sem dados para {ticker_symbol} em ou antes de {target_date}"}
            idx = valid[-1][0]

        d1 = hist.iloc[idx]

        # Variacao: comparar com o dia anterior disponivel
        if idx > 0:
            d_prev = hist.iloc[idx - 1]
            variacao = ((float(d1["Close"]) - float(d_prev["Close"])) / float(d_prev["Close"])) * 100
        else:
            variacao = 0.0

        return {
            "fechamento": round(float(d1["Close"]), 4),
            "variacao_pct": round(float(variacao), 2),
            "data": str(dates[idx]),
        }
    except Exception as e:
        return {"erro": f"Falha ao buscar {ticker_symbol}: {str(e)}"}


def get_all_market_data() -> dict:
    """Coleta todos os tickers configurados e retorna dict estruturado."""
    resultado = {"mercado_br": {}, "commodities": {}, "mercado_global": {}}

    for nome, ticker in TICKERS_BR.items():
        resultado["mercado_br"][nome] = get_yesterday_data(ticker)

    for nome, ticker in TICKERS_COMMODITIES.items():
        resultado["commodities"][nome] = get_yesterday_data(ticker)

    for nome, ticker in TICKERS_GLOBAL.items():
        resultado["mercado_global"][nome] = get_yesterday_data(ticker)

    return resultado
