# CLAUDE.md — Mercado Brasil Daily: Sistema Multiagentes de Digest Financeiro

## Visão Geral do Projeto

**Nome do sistema:** Mercado Brasil Daily  
**Objetivo:** Pipeline multiagente sequencial que coleta, verifica, analisa e entrega um digest diário do mercado financeiro brasileiro em texto corrido, acessível para investidores iniciantes.  
**Stack técnica:** Python 3.11+, Agno Framework, Ollama (qwen3:8b + qwen3:14b), yfinance, DuckDuckGo Search, ChromaDB, SQLite  
**Entrega:** Arquivo `.md` salvo localmente em `data/outputs/` (Telegram, e-mail e WhatsApp serão adicionados futuramente)  
**Execução:** Workflow sequencial (não paralelo) — restrição de hardware (CPU-only, 16GB RAM, Intel N95)

---

## Arquitetura do Sistema

### Diagrama de Fluxo

```
┌─────────────────────────────────────────────────────────────────┐
│                     Mercado Brasil Daily                        │
│                    Agno Workflow (sequencial)                   │
└─────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────┐
│   Agente 1          │  Coleta dados de mercado (yfinance) +
│   ColetorDeMercado  │  notícias financeiras (DuckDuckGo Search)
│                     │  Foco: Brasil — IBOVESPA, B3, USD/BRL,
│                     │  juros SELIC, commodities relevantes ao BR
└────────┬────────────┘
         │ dados_brutos (dict)
         ▼
┌─────────────────────┐
│   Agente 2          │  Coleta contexto geopolítico + macro global
│   ColetorGeopolitico│  com impacto direto no Brasil:
│                     │  Fed, China, Argentina, commodities globais
└────────┬────────────┘
         │ contexto_global (dict)
         ▼
┌─────────────────────┐
│   Agente 3          │  Verifica e faz curadoria das notícias:
│   CuradorDeNoticias │  checagem de fatos, filtragem de ruído,
│                     │  identificação da notícia de MAIOR IMPACTO
│                     │  de volatilidade do dia anterior
└────────┬────────────┘
         │ noticias_curadas (dict)
         ▼
┌─────────────────────┐
│   Agente 4          │  Redige o digest final em texto corrido:
│   RedatorFinanceiro │  análise do impacto da notícia principal,
│                     │  explicação para iniciantes, dica do mentor
└────────┬────────────┘
         │ digest_final (str)
         ▼
┌─────────────────────┐
│   Entregador        │  Salva digest em arquivo .md em
│   (não é agente)    │  data/outputs/digest_YYYY-MM-DD.md
└─────────────────────┘
```

---

## Estrutura de Arquivos

```
mercado_brasil_daily/
│
├── CLAUDE.md                      # Este arquivo — referência arquitetural
├── main.py                        # Ponto de entrada — executa o workflow
├── workflow.py                    # Define o Agno Workflow e orquestra os agentes
│
├── agents/
│   ├── __init__.py
│   ├── coletor_mercado.py         # Agente 1: coleta dados yfinance + notícias BR
│   ├── coletor_geopolitico.py     # Agente 2: coleta contexto geopolítico global
│   ├── curador_noticias.py        # Agente 3: verifica, filtra e rankeia notícias
│   └── redator_financeiro.py      # Agente 4: redige o digest final em texto corrido
│
├── tools/
│   ├── __init__.py
│   ├── market_data.py             # Funções yfinance: cotações, variação % do dia anterior
│   ├── news_search.py             # Funções DuckDuckGo: busca notícias BR + global
│   └── fact_check.py              # Funções auxiliares para checagem de fatos
│
├── rag/
│   ├── __init__.py
│   ├── chroma_client.py           # Inicialização do ChromaDB
│   ├── embeddings.py              # Embeddings via Ollama (nomic-embed-text, ~270MB)
│   └── knowledge_base.py          # Glossário financeiro + dicas do mentor (RAG)
│
├── delivery/
│   ├── __init__.py
│   └── file_writer.py             # Salva o digest como arquivo .md em data/outputs/
│                                  # (Telegram, e-mail e WhatsApp: implementação futura)
│
├── data/
│   ├── chroma_db/                 # Banco vetorial ChromaDB persistido
│   ├── sqlite/
│   │   └── digests.db             # Histórico de digests gerados (SQLite)
│   └── outputs/                   # Arquivos .md dos digests salvos localmente
│
├── config/
│   ├── settings.py                # Configurações centrais (tickers, modelos, etc.)
│   └── prompts.py                 # Todos os prompts dos agentes centralizados aqui
│
└── requirements.txt
```

---

## Configurações Centrais (`config/settings.py`)

```python
# Modelos Ollama — dois modelos com papéis distintos
# IMPORTANTE: nunca carregar os dois simultaneamente (restrição de RAM)
OLLAMA_BASE_URL = "http://localhost:11434"

OLLAMA_MODEL_LEVE  = "qwen3:8b"   # Agentes 1 e 2: coleta + estruturação JSON
OLLAMA_MODEL_FORTE = "qwen3:14b"  # Agentes 3 e 4: raciocínio + redação em português

# Embeddings — modelo leve, fica residente sem impacto (~270MB)
OLLAMA_EMBED_MODEL = "nomic-embed-text"

# Tickers monitorados — foco Brasil
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
    "minerio_ferro": "TIO=F",   # proxy
}

TICKERS_GLOBAL = {
    "sp500": "^GSPC",
    "nasdaq": "^IXIC",
    "dxy": "DX-Y.NYB",          # índice do dólar
    "treasury_10y": "^TNX",
}

# Período de análise: dia anterior (D-1)
ANALYSIS_PERIOD = "2d"          # yfinance: busca 2 dias para pegar D-1

# ChromaDB
CHROMA_PERSIST_DIR = "./data/chroma_db"
CHROMA_COLLECTION_MENTOR = "dicas_mentor"
CHROMA_COLLECTION_GLOSSARIO = "glossario_financeiro"

# SQLite
SQLITE_DB_PATH = "./data/sqlite/digests.db"

# Saída — apenas arquivo local por enquanto
OUTPUT_DIR = "./data/outputs"          # digests salvos como digest_YYYY-MM-DD.md

# Entrega via Telegram, e-mail e WhatsApp: implementação futura
```

---

## Agente 1 — ColetorDeMercado (`agents/coletor_mercado.py`)

### Responsabilidade
Coleta os dados quantitativos do mercado financeiro do **dia anterior (D-1)** e notícias brasileiras recentes. Não faz análise — apenas coleta e estrutura dados brutos.

### Ferramentas usadas
- `tools/market_data.py` → funções `get_price_data()`, `calculate_variation()`, `get_selic_rate()`
- `tools/news_search.py` → função `search_news_brazil()`

### Inputs
Nenhum (é o primeiro agente do pipeline).

### Output esperado (`dados_brutos: dict`)
```python
{
    "data_referencia": "2025-03-15",   # D-1
    "mercado_br": {
        "ibovespa": {"fechamento": 128500.0, "variacao_pct": -1.23, "variacao_pts": -1600},
        "usd_brl": {"cotacao": 5.87, "variacao_pct": 0.45},
        "selic_atual": 13.75,
        # ... outros tickers
    },
    "commodities": {
        "petroleo_brent": {"preco_usd": 82.5, "variacao_pct": -0.8},
        "ouro": {"preco_usd": 2050.0, "variacao_pct": 0.3},
        "soja": {"preco_usd": 1250.0, "variacao_pct": -0.5},
        # ...
    },
    "mercado_global": {
        "sp500": {"variacao_pct": -0.9},
        "nasdaq": {"variacao_pct": -1.2},
        "dxy": {"valor": 104.5, "variacao_pct": 0.3},
    },
    "noticias_brutas_br": [
        {"titulo": "...", "fonte": "...", "url": "...", "data": "..."},
        # máximo 15 notícias
    ]
}
```

### Instruções de implementação
- Usar `yfinance.download(ticker, period="2d")` para pegar D-1 e calcular variação
- Busca de notícias: DuckDuckGo com queries focadas em BR (ex: `"Bovespa ontem" "mercado financeiro Brasil"`)
- Em caso de falha no yfinance, registrar erro e continuar com dados parciais
- Não chamar LLM neste agente — apenas coleta de dados estruturados

---

## Agente 2 — ColetorGeopolitico (`agents/coletor_geopolitico.py`)

### Responsabilidade
Coleta contexto geopolítico e macroeconômico global com **impacto direto no Brasil**, focando em eventos do dia anterior.

### Ferramentas usadas
- `tools/news_search.py` → função `search_news_global_brazil_impact()`

### Queries de busca (implementar em `news_search.py`)
```python
QUERIES_GEOPOLITICAS = [
    "Federal Reserve juros Estados Unidos ontem",
    "China economia PIB commodities ontem",
    "Argentina crise econômica câmbio ontem",
    "OPEP petróleo produção ontem",
    "guerra Ucrânia commodities ontem",
    "tensão geopolítica mercados emergentes ontem",
    "Banco Central Brasil SELIC decisão ontem",
    "inflação IPCA Brasil ontem",
    "balança comercial Brasil ontem",
]
```

### Output esperado (`contexto_global: dict`)
```python
{
    "eventos_geopoliticos": [
        {"titulo": "...", "fonte": "...", "resumo_bruto": "...", "relevancia_br": "alta/media/baixa"},
        # máximo 10 eventos
    ],
    "dados_macro_br": {
        "ipca_ultimo": "...",
        "selic_decisao_recente": "...",
        "balanca_comercial": "...",
    }
}
```

### Instruções de implementação
- Usar LLM (Qwen3 via Agno) **apenas** para classificar `relevancia_br` de cada evento encontrado
- Prompt simples: classificar se o evento tem impacto alto, médio ou baixo no Brasil
- Manter o prompt enxuto para não sobrecarregar a RAM

---

## Agente 3 — CuradorDeNoticias (`agents/curador_noticias.py`)

### Responsabilidade
**Este é o agente mais crítico do pipeline.** Recebe todos os dados brutos, faz curadoria, checagem de fatos e identifica **a notícia de maior impacto de volatilidade do dia anterior**, explicando o porquê.

### Inputs
- `dados_brutos` (output do Agente 1)
- `contexto_global` (output do Agente 2)

### Tarefas do agente
1. **Filtragem de ruído:** Remove notícias duplicadas, irrelevantes ou de baixa credibilidade
2. **Checagem de fatos básica:** Cruza dados quantitativos (variações de preço reais do yfinance) com as notícias encontradas — descarta notícias que contradizem os dados de mercado
3. **Rankeamento por impacto:** Ordena notícias por impacto de volatilidade usando os dados reais de variação percentual coletados no Agente 1
4. **Seleção da notícia principal:** Identifica a notícia de MAIOR impacto de volatilidade do dia
5. **Extração de explicação causal:** Gera uma hipótese causal: por que aquela notícia causou aquela volatilidade

### Critérios de rankeamento (implementar no prompt)
```
- Variação > 2% no IBOVESPA → impacto ALTO
- Variação > 1% no USD/BRL → impacto ALTO
- Variação > 3% em commodities relevantes ao BR → impacto ALTO
- Evento geopolítico com relevância_br = "alta" → peso extra
- Decisão do Banco Central ou Fed → sempre impacto ALTO
```

### Output esperado (`noticias_curadas: dict`)
```python
{
    "noticias_curadas": [
        {
            "titulo": "...",
            "fonte": "...",
            "resumo_verificado": "...",
            "ativo_impactado": "IBOVESPA / USD/BRL / PETR4 / etc.",
            "variacao_registrada": "-2.3%",
            "score_impacto": 9.2,   # 0-10
        },
        # top 5 notícias
    ],
    "noticia_principal": {
        "titulo": "...",
        "fonte": "...",
        "resumo_verificado": "...",
        "ativo_mais_impactado": "...",
        "variacao": "...",
        "hipotese_causal": "...",  # explicação do porquê causou volatilidade
    },
    "noticia_descartadas_count": 8,
    "motivo_descarte_geral": "duplicatas e baixa credibilidade"
}
```

### RAG neste agente
- Consultar ChromaDB (`glossario_financeiro`) para enriquecer o `hipotese_causal` com definições precisas
- Ex: se a notícia envolve "carry trade", buscar definição no glossário e incorporar na explicação

---

## Agente 4 — RedatorFinanceiro (`agents/redator_financeiro.py`)

### Responsabilidade
Redige o **digest final em texto corrido**, em linguagem acessível para investidores iniciantes, incluindo a dica do mentor do dia.

### Inputs
- `dados_brutos` (output do Agente 1)
- `noticias_curadas` (output do Agente 3)

### Estrutura do texto final produzido

```
═══════════════════════════════════════
📊 MERCADO BRASIL DAILY — [DATA]
═══════════════════════════════════════

BOM DIA! Aqui está o resumo do que moveu os mercados ontem.

─── PANORAMA GERAL ───────────────────
[Parágrafo único descrevendo o comportamento geral do mercado brasileiro
ontem — IBOVESPA, câmbio, juros — em 3 a 4 frases. Linguagem simples.]

─── O QUE MAIS MOVEU O MERCADO ───────
[Parágrafo explicando a notícia de maior impacto de volatilidade.
Citar o ativo afetado e a variação registrada. Explicar a relação causal
de forma didática para iniciantes. 4 a 6 frases.]

─── CONTEXTO GLOBAL ──────────────────
[Parágrafo sobre os 2 ou 3 eventos geopolíticos/macro mais relevantes
para o Brasil ontem. 3 a 4 frases.]

─── COMMODITIES ──────────────────────
[Parágrafo com comportamento do petróleo, ouro e soja (relevantes para
o Brasil exportador). Citar variações numéricas. 2 a 3 frases.]

─── DICA DO MENTOR ───────────────────
[Conceito financeiro do dia — SEMPRE diferente do dia anterior.
Explicação didática em 3 a 5 frases. Ex: "O que é um canal de tendência?",
"O que é retração de Fibonacci?", "O que é volatilidade implícita?"]

═══════════════════════════════════════
Mercado Brasil Daily | Gerado automaticamente
═══════════════════════════════════════
```

### RAG neste agente — Dica do Mentor
- O agente consulta o ChromaDB (`dicas_mentor`) para selecionar a dica do dia
- A seleção é feita por **contexto**: se o mercado ontem teve alta volatilidade, buscar dica sobre "volatilidade", "VIX", "stop loss"
- Se a notícia principal envolveu câmbio, buscar dica sobre "Forex", "carry trade", "hedge cambial"
- Registrar no SQLite qual dica foi usada (para não repetir nos próximos dias)
- Query RAG: `similarity_search(query=noticia_principal['titulo'], collection="dicas_mentor")`

### Tom e linguagem
- **Nunca usar jargão sem explicar**
- **Evitar termos como "player", "upside", "pivot"** sem definir
- Escrever como se fosse um professor de finanças explicando para alunos de graduação
- Usar números concretos: `"o dólar subiu 0,45%, fechando a R$ 5,87"` — nunca `"o dólar valorizou significativamente"`

---

## Workflow Agno (`workflow.py`)

### Implementação do Workflow sequencial

```python
from agno.workflow import Workflow, RunResponse, RunEvent
from agno.utils.log import logger
from agents.coletor_mercado import criar_agente_coletor_mercado
from agents.coletor_geopolitico import criar_agente_coletor_geopolitico
from agents.curador_noticias import criar_agente_curador
from agents.redator_financeiro import criar_agente_redator
import json

class MercadoBrasilDailyWorkflow(Workflow):
    description: str = "Pipeline diário de digest financeiro focado no Brasil"

    def run(self, force_refresh: bool = False) -> RunResponse:
        logger.info("=== Iniciando Mercado Brasil Daily ===")

        # --- ETAPA 1: Coleta de mercado ---
        logger.info("Agente 1: Coletando dados de mercado...")
        agente1 = criar_agente_coletor_mercado()
        resp1 = agente1.run("Colete os dados de mercado do dia anterior.")
        dados_brutos = json.loads(resp1.content)

        # --- ETAPA 2: Coleta geopolítica ---
        logger.info("Agente 2: Coletando contexto geopolítico...")
        agente2 = criar_agente_coletor_geopolitico()
        resp2 = agente2.run("Colete o contexto geopolítico global com impacto no Brasil.")
        contexto_global = json.loads(resp2.content)

        # --- ETAPA 3: Curadoria ---
        logger.info("Agente 3: Fazendo curadoria das notícias...")
        agente3 = criar_agente_curador()
        prompt3 = f"""
        Dados de mercado: {json.dumps(dados_brutos, ensure_ascii=False)}
        Contexto global: {json.dumps(contexto_global, ensure_ascii=False)}
        Faça a curadoria, checagem de fatos e identifique a notícia de maior impacto.
        """
        resp3 = agente3.run(prompt3)
        noticias_curadas = json.loads(resp3.content)

        # --- ETAPA 4: Redação ---
        logger.info("Agente 4: Redigindo o digest final...")
        agente4 = criar_agente_redator()
        prompt4 = f"""
        Dados de mercado: {json.dumps(dados_brutos, ensure_ascii=False)}
        Notícias curadas: {json.dumps(noticias_curadas, ensure_ascii=False)}
        Redija o digest financeiro diário completo em texto corrido.
        """
        resp4 = agente4.run(prompt4)
        digest_final = resp4.content

        logger.info("=== Pipeline concluído com sucesso ===")

        return RunResponse(
            event=RunEvent.workflow_completed,
            content=digest_final
        )
```

### Atenção sobre contexto entre agentes
- **Não** usar `session_state` do Agno para passar dados grandes entre agentes (pode inflar o contexto)
- Passar dados via prompt de texto (JSON serializado), mantendo o JSON enxuto
- Se o JSON ficar > 3000 tokens, fazer sumarização antes de passar ao próximo agente
- Todos os agentes usam Ollama local — `qwen3:8b` nas fases 1–2, `qwen3:14b` nas fases 3–4

---

## Tools (`tools/`)

### `tools/market_data.py`

```python
import yfinance as yf
from datetime import datetime, timedelta
from config.settings import TICKERS_BR, TICKERS_COMMODITIES, TICKERS_GLOBAL, ANALYSIS_PERIOD

def get_yesterday_data(ticker_symbol: str) -> dict:
    """Busca dados de fechamento do dia anterior (D-1)."""
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period=ANALYSIS_PERIOD)
    if len(hist) < 2:
        return {"erro": f"Dados insuficientes para {ticker_symbol}"}
    # D-1 = penúltima linha
    d1 = hist.iloc[-2]
    d0 = hist.iloc[-1] if len(hist) > 1 else d1
    variacao = ((d1["Close"] - hist.iloc[-3]["Close"]) / hist.iloc[-3]["Close"]) * 100 if len(hist) >= 3 else 0
    return {
        "fechamento": round(d1["Close"], 4),
        "abertura": round(d1["Open"], 4),
        "maxima": round(d1["High"], 4),
        "minima": round(d1["Low"], 4),
        "variacao_pct": round(variacao, 2),
        "data": str(d1.name.date()),
    }

def get_all_market_data() -> dict:
    """Coleta todos os tickers configurados."""
    resultado = {"mercado_br": {}, "commodities": {}, "mercado_global": {}}
    for nome, ticker in TICKERS_BR.items():
        resultado["mercado_br"][nome] = get_yesterday_data(ticker)
    for nome, ticker in TICKERS_COMMODITIES.items():
        resultado["commodities"][nome] = get_yesterday_data(ticker)
    for nome, ticker in TICKERS_GLOBAL.items():
        resultado["mercado_global"][nome] = get_yesterday_data(ticker)
    return resultado
```

### `tools/news_search.py`

```python
from duckduckgo_search import DDGS
from datetime import datetime, timedelta

def search_news(query: str, max_results: int = 5) -> list[dict]:
    """Busca notícias via DuckDuckGo."""
    results = []
    with DDGS() as ddgs:
        for r in ddgs.news(query, max_results=max_results, region="br-pt"):
            results.append({
                "titulo": r.get("title", ""),
                "fonte": r.get("source", ""),
                "url": r.get("url", ""),
                "data": r.get("date", ""),
                "resumo": r.get("body", ""),
            })
    return results

def search_news_brazil() -> list[dict]:
    """Agrega notícias financeiras brasileiras do dia anterior."""
    queries = [
        "Bovespa IBOVESPA fechamento ontem",
        "dólar real câmbio Brasil ontem",
        "Banco Central SELIC juros Brasil",
        "economia Brasil mercado financeiro ontem",
        "inflação IPCA Brasil recente",
        "ações B3 destaque ontem",
    ]
    todas = []
    for q in queries:
        todas.extend(search_news(q, max_results=3))
    # Deduplicar por URL
    seen = set()
    dedup = []
    for n in todas:
        if n["url"] not in seen:
            seen.add(n["url"])
            dedup.append(n)
    return dedup[:15]  # máximo 15

def search_news_global_brazil_impact() -> list[dict]:
    """Notícias globais com impacto no Brasil."""
    queries = [
        "Federal Reserve interest rates decision",
        "China economy commodities impact",
        "OPEC oil production decision",
        "Argentina economic crisis peso",
        "geopolitical risk emerging markets",
        "Ukraine war commodities",
    ]
    todas = []
    for q in queries:
        todas.extend(search_news(q, max_results=2))
    seen = set()
    dedup = []
    for n in todas:
        if n["url"] not in seen:
            seen.add(n["url"])
            dedup.append(n)
    return dedup[:10]
```

---

## RAG (`rag/`)

### Estrutura do ChromaDB

**Collection: `dicas_mentor`**  
Armazena dicas educativas sobre conceitos financeiros. Cada documento:
```python
{
    "id": "dica_001",
    "document": "Canal de tendência é uma ferramenta da análise técnica...",
    "metadata": {
        "titulo": "O que é um canal de tendência?",
        "categoria": "analise_tecnica",
        "tags": ["tendência", "suporte", "resistência", "gráfico"],
        "usado_em": []   # lista de datas em que foi usado
    }
}
```

**Collection: `glossario_financeiro`**  
Armazena definições de termos financeiros:
```python
{
    "id": "gloss_001",
    "document": "Volatilidade é a medida de variação do preço de um ativo...",
    "metadata": {
        "termo": "volatilidade",
        "categoria": "conceito_geral"
    }
}
```

### Dicas do mentor a serem pré-cadastradas no ChromaDB

Implementar script `rag/seed_knowledge_base.py` para popular com pelo menos 30 dicas:

```python
DICAS_MENTOR = [
    {"titulo": "O que é um canal de tendência?", "categoria": "analise_tecnica", "tags": ["tendência", "gráfico"]},
    {"titulo": "O que é retração de Fibonacci?", "categoria": "analise_tecnica", "tags": ["fibonacci", "suporte"]},
    {"titulo": "O que é a SELIC e por que ela importa?", "categoria": "juros", "tags": ["selic", "juros", "banco central"]},
    {"titulo": "O que é o IBOVESPA?", "categoria": "bolsa", "tags": ["ibovespa", "índice", "B3"]},
    {"titulo": "O que é volatilidade?", "categoria": "conceito_geral", "tags": ["volatilidade", "risco"]},
    {"titulo": "O que é carry trade?", "categoria": "cambio", "tags": ["câmbio", "juros", "arbitragem"]},
    {"titulo": "O que é diversificação de carteira?", "categoria": "estrategia", "tags": ["diversificação", "risco"]},
    {"titulo": "O que são dividendos?", "categoria": "acoes", "tags": ["dividendos", "proventos", "ações"]},
    {"titulo": "O que é stop loss?", "categoria": "gestao_risco", "tags": ["stop loss", "proteção", "perda"]},
    {"titulo": "O que é o P/L (Preço/Lucro)?", "categoria": "analise_fundamentalista", "tags": ["PE", "valuation"]},
    {"titulo": "O que é inflação e como afeta os investimentos?", "categoria": "macro", "tags": ["inflação", "ipca", "poder de compra"]},
    {"titulo": "O que são FIIs (Fundos de Investimento Imobiliário)?", "categoria": "fii", "tags": ["fii", "imóveis", "renda passiva"]},
    {"titulo": "O que é hedge cambial?", "categoria": "cambio", "tags": ["hedge", "câmbio", "proteção"]},
    {"titulo": "O que é um ETF?", "categoria": "produtos", "tags": ["etf", "fundo", "índice"]},
    {"titulo": "O que é liquidez?", "categoria": "conceito_geral", "tags": ["liquidez", "facilidade", "venda"]},
    # ... adicionar até 30+
]
```

### Lógica de seleção da dica do dia

```python
def selecionar_dica_do_dia(noticia_principal: dict, db) -> dict:
    """
    Seleciona a dica mais contextualmente relevante que ainda não foi usada hoje.
    """
    # 1. Busca por similaridade com a notícia principal
    query = noticia_principal.get("titulo", "") + " " + noticia_principal.get("ativo_mais_impactado", "")
    resultados = db.similarity_search(query, collection="dicas_mentor", n_results=5)
    
    # 2. Filtra dicas não usadas nos últimos 30 dias
    hoje = datetime.now().date().isoformat()
    for dica in resultados:
        if hoje not in dica["metadata"].get("usado_em", []):
            # Marca como usada
            dica["metadata"]["usado_em"].append(hoje)
            db.update(dica["id"], metadata=dica["metadata"])
            return dica
    
    # 3. Fallback: pega qualquer dica não usada recentemente
    return db.get_least_recently_used(collection="dicas_mentor")
```

---

## Persistência SQLite (`data/sqlite/digests.db`)

### Schema

```sql
CREATE TABLE IF NOT EXISTS digests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_referencia TEXT NOT NULL,          -- D-1, formato YYYY-MM-DD
    data_geracao TEXT NOT NULL,             -- timestamp de geração
    noticia_principal TEXT,                 -- título da notícia principal
    ativo_impactado TEXT,                   -- ex: "IBOVESPA"
    variacao_principal TEXT,                -- ex: "-2.3%"
    dica_mentor_titulo TEXT,                -- dica usada naquele dia
    digest_completo TEXT,                   -- texto completo do digest
    status_envio TEXT DEFAULT 'pendente'    -- 'enviado' / 'erro' / 'pendente'
);

CREATE TABLE IF NOT EXISTS erros_pipeline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_hora TEXT NOT NULL,
    agente TEXT NOT NULL,
    mensagem_erro TEXT,
    dados_contexto TEXT
);
```

---

## Entrega (`delivery/`)

### `delivery/file_writer.py`
- Recebe o texto do Agente 4 e salva como arquivo `.md` em `data/outputs/`
- Nome do arquivo: `digest_YYYY-MM-DD.md` (data de referência = D-1)
- Cria o diretório `data/outputs/` automaticamente se não existir
- Retorna o caminho completo do arquivo salvo para log

```python
import os
from datetime import datetime, timedelta

def salvar_digest_md(digest: str, data_referencia: str = None) -> str:
    """Salva o digest como arquivo .md e retorna o caminho."""
    if not data_referencia:
        data_referencia = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    output_dir = "./data/outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    caminho = os.path.join(output_dir, f"digest_{data_referencia}.md")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(digest)
    
    return caminho
```

> **Nota:** Entrega via Telegram, e-mail e WhatsApp será implementada em versão futura. A arquitetura já reserva o diretório `delivery/` para isso.

---

## `main.py` — Ponto de Entrada

```python
from workflow import MercadoBrasilDailyWorkflow
from delivery.file_writer import salvar_digest_md
from data.sqlite_manager import salvar_digest_sqlite
from datetime import datetime, timedelta

def main():
    print(f"[{datetime.now()}] Iniciando Mercado Brasil Daily...")
    
    workflow = MercadoBrasilDailyWorkflow(
        session_id="mercado_brasil_daily",
        storage=None
    )
    
    resultado = workflow.run()
    digest = resultado.content
    
    # Data de referência = D-1
    data_referencia = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Salvar como arquivo .md
    caminho = salvar_digest_md(digest, data_referencia)
    print(f"✅ Digest salvo em: {caminho}")
    
    # Persistir metadados no SQLite
    salvar_digest_sqlite(digest, data_referencia)
    print("✅ Metadados registrados no SQLite.")
    
    print(f"[{datetime.now()}] Concluído.")

if __name__ == "__main__":
    main()
```

---

## `requirements.txt`

```
agno>=0.9.0
ollama>=0.2.0
yfinance>=0.2.40
duckduckgo-search>=6.0.0
chromadb>=0.5.0
psutil>=5.9.0
python-dotenv>=1.0.0
sqlite-utils>=3.36
pydantic>=2.0.0
```

---

## Prompts dos Agentes (`config/prompts.py`)

### Prompt do Agente 1 (ColetorDeMercado)
```
Você é um coletor de dados de mercado financeiro. Sua única função é coletar 
e estruturar dados — não analise nem interprete.
Retorne APENAS um JSON válido com a estrutura definida. Sem texto adicional.
Foco: mercado financeiro brasileiro, dia anterior (D-1).
```

### Prompt do Agente 2 (ColetorGeopolitico)
```
Você é um coletor de notícias geopolíticas. Sua única função é buscar eventos 
geopolíticos e macroeconômicos globais com impacto direto no Brasil.
Para cada evento, classifique: relevancia_br = "alta", "media" ou "baixa".
Retorne APENAS um JSON válido. Sem texto adicional.
```

### Prompt do Agente 3 (CuradorDeNoticias)
```
Você é um curador e verificador de notícias financeiras. Sua função:
1. Eliminar duplicatas e notícias sem credibilidade
2. Cruzar notícias com os dados quantitativos reais de mercado fornecidos
3. Descartar notícias que contradizem os dados reais
4. Rankear as notícias por impacto de volatilidade (use os dados de variação % reais)
5. Identificar a notícia de MAIOR impacto de volatilidade do dia anterior
6. Explicar de forma simples e causal por que aquela notícia causou volatilidade

Retorne APENAS um JSON válido com a estrutura definida. Sem texto adicional.
Seja objetivo e preciso. Use apenas fatos verificáveis pelos dados fornecidos.
```

### Prompt do Agente 4 (RedatorFinanceiro)
```
Você é um redator financeiro especializado em comunicação para iniciantes.
Redija um digest diário do mercado financeiro brasileiro em texto corrido,
seguindo EXATAMENTE a estrutura fornecida.

Regras obrigatórias:
- Linguagem clara e direta, como um professor explicando para alunos
- SEMPRE citar números reais: cotações, variações percentuais
- NUNCA usar jargão sem explicar o que significa
- A seção "Dica do Mentor" deve ser didática e completa em 3 a 5 frases
- O texto final deve ter entre 400 e 600 palavras no total
- Escreva em português do Brasil, tom profissional mas acessível
```

---

## Agendamento com systemd (Beelink)

### `/etc/systemd/system/mercado-brasil-daily.service`
```ini
[Unit]
Description=Mercado Brasil Daily — Digest financeiro diário
After=network-online.target

[Service]
Type=oneshot
User=vitor
WorkingDirectory=/home/vitor/mercado_brasil_daily
ExecStart=/home/vitor/.venv/mercado_brasil/bin/python main.py
StandardOutput=journal
StandardError=journal
```

### `/etc/systemd/system/mercado-brasil-daily.timer`
```ini
[Unit]
Description=Timer — Mercado Brasil Daily (06h30 todo dia útil)

[Timer]
OnCalendar=Mon-Fri 06:30:00
Persistent=true

[Install]
WantedBy=timers.target
```

### Ativar
```bash
sudo systemctl daemon-reload
sudo systemctl enable mercado-brasil-daily.timer
sudo systemctl start mercado-brasil-daily.timer
```

---

## Considerações de Performance (CPU-only, Intel N95, 16GB RAM)

1. **Dois modelos, nunca simultâneos:** `qwen3:8b` serve os Agentes 1–2; `qwen3:14b` serve os Agentes 3–4. O Ollama descarrega o modelo anterior automaticamente, mas adicionar `time.sleep(3)` na transição entre as fases é obrigatório para evitar pico de RAM
2. **Agente 1 quase sem LLM:** Usar lógica Python pura com yfinance para coleta — chamar o modelo apenas se necessário para estruturar JSON corrompido
3. **Contexto enxuto nos prompts:** Serializar apenas os campos necessários do JSON ao passar dados entre agentes — evitar dumps completos com campos desnecessários. Limite prático: ~2000 tokens de contexto por chamada
4. **ChromaDB + nomic-embed-text:** O modelo de embedding (~270MB) fica residente em RAM sem conflitar com os modelos de inferência — inicializar uma única vez no startup
5. **max_tokens conservador:** Agente 3 → `max_tokens=800`; Agente 4 → `max_tokens=1200`. Evitar janelas de contexto maiores que 4096 tokens no total
6. **Log de uso de memória:** Registrar `psutil.virtual_memory().percent` antes e depois de cada agente para monitorar consumo ao longo do tempo

---

## Checklist de Implementação para o Claude Code

- [ ] Criar estrutura de diretórios completa
- [ ] Verificar que os modelos estão baixados: `ollama pull qwen3:8b && ollama pull qwen3:14b && ollama pull nomic-embed-text`
- [ ] Criar `.env.example` documentado (sem segredos, apenas estrutura)
- [ ] Implementar `config/settings.py` com todos os tickers e configurações
- [ ] Implementar `tools/market_data.py` com funções yfinance
- [ ] Implementar `tools/news_search.py` com DuckDuckGo
- [ ] Implementar `rag/chroma_client.py` e `rag/knowledge_base.py`
- [ ] Criar script `rag/seed_knowledge_base.py` com 30+ dicas do mentor
- [ ] Implementar `agents/coletor_mercado.py` (Agente 1) — usando `Ollama` provider do Agno com `qwen3:8b`
- [ ] Implementar `agents/coletor_geopolitico.py` (Agente 2) — `qwen3:8b`
- [ ] Implementar `agents/curador_noticias.py` (Agente 3) — `qwen3:14b`, mais crítico
- [ ] Implementar `agents/redator_financeiro.py` (Agente 4) — `qwen3:14b`
- [ ] Implementar `workflow.py` com Agno Workflow sequencial
- [ ] Implementar `delivery/file_writer.py` — salvar digest como `.md`
- [ ] Implementar `data/sqlite_manager.py` com schema e funções CRUD
- [ ] Implementar `main.py`
- [ ] Criar `requirements.txt`
- [ ] Configurar systemd timer para execução diária às 06h30
- [ ] Testar pipeline completo com `python main.py`

---

## Como instanciar os modelos Ollama no Agno

O sistema usa **dois modelos com papéis distintos**. Nunca carregue os dois simultaneamente — o Ollama descarrega automaticamente o modelo anterior quando um novo é solicitado, mas o workflow deve respeitar a sequência para evitar pico de RAM.

| Agente | Modelo | Justificativa |
|---|---|---|
| Agente 1 — ColetorDeMercado | `qwen3:8b` | Tarefa simples: estruturar JSON, sem raciocínio complexo |
| Agente 2 — ColetorGeopolitico | `qwen3:8b` | Classificação de relevância: tarefa leve |
| Agente 3 — CuradorDeNoticias | `qwen3:14b` | Raciocínio causal, checagem de fatos, rankeamento |
| Agente 4 — RedatorFinanceiro | `qwen3:14b` | Geração de texto em português com qualidade |
| Embeddings ChromaDB | `nomic-embed-text` | Residente permanente (~270MB), não conflita |

**RAM estimada por fase:**
- Fase 1–2 (`qwen3:8b` Q4): ~5–6GB → confortável
- Fase 3–4 (`qwen3:14b` Q4): ~9–10GB → no limite, seguro com folga de ~2GB

### Instanciação no código

```python
from agno.agent import Agent
from agno.models.ollama import Ollama
from config.settings import OLLAMA_BASE_URL, OLLAMA_MODEL_LEVE, OLLAMA_MODEL_FORTE

# Agentes 1 e 2 — modelo leve
def criar_agente_leve(instructions: str) -> Agent:
    return Agent(
        model=Ollama(
            id=OLLAMA_MODEL_LEVE,
            host=OLLAMA_BASE_URL,
        ),
        instructions=instructions,
        markdown=False,
    )

# Agentes 3 e 4 — modelo forte
def criar_agente_forte(instructions: str) -> Agent:
    return Agent(
        model=Ollama(
            id=OLLAMA_MODEL_FORTE,
            host=OLLAMA_BASE_URL,
        ),
        instructions=instructions,
        markdown=False,
    )
```

### Garantir descarga entre fases no workflow

Adicionar `time.sleep(3)` entre a execução dos Agentes 2 e 3 para dar tempo ao Ollama de descarregar o `qwen3:8b` antes de carregar o `qwen3:14b`:

```python
# workflow.py — entre etapa 2 e etapa 3
import time
...
resp2 = agente2.run(...)
time.sleep(3)   # aguarda Ollama descarregar qwen3:8b
resp3 = agente3.run(...)
```

> **Pré-requisito:** Garantir que os modelos e o embedding estão baixados no Ollama antes da primeira execução:
> ```bash
> ollama pull qwen3:8b
> ollama pull qwen3:14b
> ollama pull nomic-embed-text
> ```

---

*CLAUDE.md — Mercado Brasil Daily v1.2*  
*Modelos: Ollama qwen3:8b (Agentes 1–2) + qwen3:14b (Agentes 3–4) + nomic-embed-text (RAG)*  
*Entrega: arquivo .md local (v1) — Telegram/e-mail/WhatsApp em versão futura*  
*Gerado para uso com Claude Code*