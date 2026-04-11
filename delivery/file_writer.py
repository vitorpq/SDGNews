import os
from datetime import datetime, timedelta
from config.settings import OUTPUT_DIR


def salvar_digest_md(digest: str, data_referencia: str | None = None, dados_mercado: dict | None = None) -> tuple[str, str, str]:
    """
    Salva o digest como arquivo .md e retorna (caminho, texto_telegram, texto_md).

    Args:
        digest: Texto gerado pelo LLM (conteúdo narrativo)
        data_referencia: Data de referência (D-1), formato YYYY-MM-DD
        dados_mercado: Dict com dados do yfinance para gerar dashboard

    Returns:
        (caminho_arquivo, texto_telegram_com_html, texto_md_limpo)
    """
    if not data_referencia:
        data_referencia = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    caminho = os.path.join(OUTPUT_DIR, f"digest_{data_referencia}.md")

    # Gerar dashboard com dados reais (não confia no LLM)
    dashboard_telegram = ""
    dashboard_md = ""
    if dados_mercado:
        dashboard_telegram = _gerar_dashboard_telegram(dados_mercado, data_referencia)
        dashboard_md = _gerar_dashboard_md(dados_mercado, data_referencia)

    # Versão para Telegram: HTML + dashboard
    texto_telegram = dashboard_telegram + "\n" + digest
    texto_telegram = _garantir_secoes_finais_telegram(texto_telegram)

    # Versão para arquivo .md: limpa, sem HTML
    texto_md = dashboard_md + "\n" + digest
    texto_md = _garantir_secoes_finais_md(texto_md)

    # Salvar arquivo .md local (versão limpa)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(texto_md)

    return caminho, texto_telegram, texto_md


def _gerar_dashboard_telegram(dados_mercado: dict, data_referencia: str) -> str:
    """Gera o dashboard para Telegram com HTML e semáforo de cores."""
    # Formatar data de referência
    dt = datetime.strptime(data_referencia, "%Y-%m-%d")
    dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    dia_semana = dias_semana[dt.weekday()]
    data_formatada = f"{dia_semana.capitalize()}, {dt.day} de {_mes_nome(dt.month)} de {dt.year}"

    # Cabeçalho
    html = f"🇧🇷 <b>SDG DAILY NEWS</b>\n"
    html += f"<i>{data_formatada}</i>\n\n"
    html += "📊 <b>FECHAMENTO DO DIA</b>\n\n"

    # Lista de ativos com lógica de semáforo
    ativos_dashboard = [
        ("mercado_br", "ibovespa", "IBOVESPA", "pts"),
        ("mercado_br", "usd_brl", "DÓLAR", "R$"),
        ("mercado_br", "eur_brl", "EUR/BRL", "R$"),
        ("mercado_br", "petr4", "PETR4", "R$"),
        ("mercado_br", "vale3", "VALE3", "R$"),
        ("mercado_br", "itub4", "ITUB4", "R$"),
        ("commodities", "petroleo_brent", "BRENT", "US$"),
        ("commodities", "ouro", "OURO", "US$"),
        ("mercado_global", "sp500", "S&P 500", "pts"),
    ]

    for categoria, nome_ativo, label, moeda in ativos_dashboard:
        if categoria not in dados_mercado or nome_ativo not in dados_mercado[categoria]:
            continue

        ativo = dados_mercado[categoria][nome_ativo]
        if "erro" in ativo:
            continue

        fechamento = ativo.get("fechamento", 0)
        variacao = ativo.get("variacao_pct", 0)

        # Formatar número
        if "pts" in moeda:
            numero_fmt = f"{fechamento:,.0f}".replace(",", ".")
        else:
            numero_fmt = f"{fechamento:.4f}".rstrip("0").rstrip(".")

        # Semáforo (invertido para dólar/euro)
        semaforo = _calcular_semaforo(nome_ativo, variacao)

        # Linha com espaçamento fixo em código mono
        html += f"<code>{label:<12} {numero_fmt:>12}  {variacao:>+.2f}%  {semaforo}</code>\n"

    html += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    return html


def _gerar_dashboard_md(dados_mercado: dict, data_referencia: str) -> str:
    """Gera o dashboard para arquivo .md local (versão limpa, sem HTML)."""
    # Formatar data de referência
    dt = datetime.strptime(data_referencia, "%Y-%m-%d")
    dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    dia_semana = dias_semana[dt.weekday()]
    data_formatada = f"{dia_semana.capitalize()}, {dt.day} de {_mes_nome(dt.month)} de {dt.year}"

    # Cabeçalho
    md = f"# 🇧🇷 SDG DAILY NEWS\n"
    md += f"**{data_formatada}**\n\n"
    md += "## 📊 FECHAMENTO DO DIA\n\n"

    # Lista de ativos com lógica de semáforo
    ativos_dashboard = [
        ("mercado_br", "ibovespa", "IBOVESPA", "pts"),
        ("mercado_br", "usd_brl", "DÓLAR", "R$"),
        ("mercado_br", "eur_brl", "EUR/BRL", "R$"),
        ("mercado_br", "petr4", "PETR4", "R$"),
        ("mercado_br", "vale3", "VALE3", "R$"),
        ("mercado_br", "itub4", "ITUB4", "R$"),
        ("commodities", "petroleo_brent", "BRENT", "US$"),
        ("commodities", "ouro", "OURO", "US$"),
        ("mercado_global", "sp500", "S&P 500", "pts"),
    ]

    for categoria, nome_ativo, label, moeda in ativos_dashboard:
        if categoria not in dados_mercado or nome_ativo not in dados_mercado[categoria]:
            continue

        ativo = dados_mercado[categoria][nome_ativo]
        if "erro" in ativo:
            continue

        fechamento = ativo.get("fechamento", 0)
        variacao = ativo.get("variacao_pct", 0)

        # Formatar número
        if "pts" in moeda:
            numero_fmt = f"{fechamento:,.0f}".replace(",", ".")
        else:
            numero_fmt = f"{fechamento:.4f}".rstrip("0").rstrip(".")

        # Semáforo (invertido para dólar/euro)
        semaforo = _calcular_semaforo(nome_ativo, variacao)

        # Linha com espaçamento fixo em markdown
        md += f"`{label:<12} {numero_fmt:>12}  {variacao:>+.2f}%  {semaforo}`\n"

    md += "\n---\n\n"
    return md


def _calcular_semaforo(nome_ativo: str, variacao_pct: float) -> str:
    """Retorna emoji de semáforo baseado na variação (invertido para dólar/euro)."""
    ATIVOS_INVERTIDOS = {"usd_brl", "eur_brl"}

    if variacao_pct == 0:
        return "🔵"

    positivo = variacao_pct > 0

    # Para dólar e euro, lógica é invertida: queda = bom = verde
    if nome_ativo in ATIVOS_INVERTIDOS:
        positivo = not positivo

    return "🟢" if positivo else "🔴"


def _mes_nome(mes: int) -> str:
    """Converte número do mês para nome."""
    meses = [
        "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
    ]
    return meses[mes]


def _garantir_secoes_finais_telegram(digest: str) -> str:
    """Garante seções finais no formato HTML para Telegram."""
    resultado = digest.rstrip()

    # Remover rodape existente
    if resultado.endswith("═══════════════════════════════════════"):
        linhas = resultado.rsplit("═══════════════════════════════════════", 2)
        if len(linhas) >= 2:
            resultado = linhas[0].rstrip()

    # Injetar seções em HTML
    if "NOTA SOBRE OS DADOS" not in resultado:
        resultado += "\n" + _NOTA_DADOS_HTML
    if "FONTES" not in resultado or "Tavily" not in resultado:
        resultado += _FONTES_HTML

    resultado += _RODAPE_HTML
    return resultado


def _garantir_secoes_finais_md(digest: str) -> str:
    """Garante seções finais no formato Markdown para arquivo local."""
    resultado = digest.rstrip()

    # Remover rodape existente
    if "SDG Daily News | Gerado automaticamente" in resultado:
        resultado = resultado.split("SDG Daily News | Gerado automaticamente")[0].rstrip()

    # Injetar seções em Markdown
    if "NOTA SOBRE OS DADOS" not in resultado:
        resultado += "\n" + _NOTA_DADOS_MD
    if "FONTES" not in resultado or "Tavily" not in resultado:
        resultado += _FONTES_MD

    resultado += _RODAPE_MD
    return resultado


# ============================================================================
# Seções fixas — HTML para Telegram
# ============================================================================

_NOTA_DADOS_HTML = """
<b>⚠️ NOTA SOBRE OS DADOS:</b>
<i>Yahoo Finance. Sujeito a divergências de metodologia/horário em relação às fontes oficiais (B3/BC).</i>

"""

_FONTES_HTML = """
<b>📎 FONTES</b>
Dados de mercado: <b>Yahoo Finance</b>
Notícias: <b>Tavily</b> e <b>Perigon</b> (agregadores que indexam fontes como \
Valor Econômico, Folha de São Paulo, Estadão, O Globo, Bloomberg, Infomoney, \
Reuters, Money Times, CNN, The Wall Street Journal, entre outras).

"""

_RODAPE_HTML = """
<i>SDG Daily News | @sdg_news</i>
"""

# ============================================================================
# Seções fixas — Markdown para arquivo local
# ============================================================================

_NOTA_DADOS_MD = """
## ⚠️ NOTA SOBRE OS DADOS

Os dados de cotações e variações percentuais deste digest são obtidos via Yahoo \
Finance e podem apresentar pequenas divergências em relação aos valores oficiais \
divulgados pela B3 ou pelo Banco Central. Isso acontece porque diferentes fontes \
utilizam horários de corte, metodologias de cálculo e referências distintas. Por \
exemplo, a cotação do dólar pode variar entre o dólar comercial (usado em transações \
entre empresas), o dólar turismo e o dólar spot (negociado em tempo real no mercado \
internacional). Da mesma forma, variações percentuais podem diferir conforme o preço \
de referência utilizado (fechamento anterior, abertura ou ajuste). Para decisões \
financeiras, consulte sempre as fontes oficiais.
"""

_FONTES_MD = """
## 📎 FONTES

**Dados de mercado:** Yahoo Finance

**Notícias:** Tavily e Perigon (agregadores que indexam fontes como Valor Econômico, \
Folha de São Paulo, Estadão, O Globo, Bloomberg, Infomoney, Reuters, Money Times, \
CNN, The Wall Street Journal, entre outras).
"""

_RODAPE_MD = """
---

*SDG Daily News | Gerado automaticamente*
"""
