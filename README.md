# SDG Daily News — Pipeline Multiagente de Digest Financeiro

Um sistema de **análise e curadoria automatizada de notícias financeiras** que gera um digest diário do mercado brasileiro focado em investidores iniciantes.

## Problema

Investidores iniciantes enfrentam dois desafios:
1. **Informação em excesso** — centenas de notícias financeiras por dia, sem priorização
2. **Falta de verificação** — notícias contradizem dados reais ou são defasadas

Este projeto resolve isso com um pipeline que:
- Coleta dados reais do mercado (yfinance)
- Busca notícias relevantes (Tavily + Perigon)
- **Verifica contradições** antes de publicar
- Gera um digest em linguagem acessível

## Arquitetura

```
┌──────────────────────────────────────────────────────────┐
│   SDG Daily News — Pipeline Multiagente (4 etapas) │
└──────────────────────────────────────────────────────────┘

ETAPA 1: Coleta de Dados (Python puro)
├─ yfinance: busca dados do dia anterior (D-1) em 17 tickers
├─ Cálculo de variações percentuais
└─ Validação de datas (evita mistura de dias)

ETAPA 2: Coletor (LLM via OpenRouter)
├─ Busca notícias financeiras (Tavily + Perigon)
├─ Filtra por relevância para o Brasil
└─ Estrutura dados em JSON

ETAPA 3: Curador (LLM via OpenRouter) ← NOVO
├─ Filtra noticias por data
├─ Detecta contradições com dados reais
├─ Verifica corroboração multi-fonte
├─ Rankeia por impacto (variação %)
└─ Identifica notícia principal com hipótese causal

ETAPA 4: Redator (LLM via OpenRouter)
├─ Redige digest em linguagem acessível
├─ Inclui orientações para iniciantes
└─ Estrutura em seções: panorama, destaque, global, commodities

ENTREGA: Arquivo .md + Telegram + SQLite
```

## Stack Técnico

- **Python 3.11+**
- **yfinance** — coleta de dados de mercado
- **Tavily + Perigon** — busca de notícias
- **OpenRouter** — acesso a Claude/Gemini via API
- **Agno Framework** — orquestração de agentes LLM
- **SQLite** — persistência de histórico
- **Telegram Bot API** — entrega diária

## Recursos Implementados

### ✅ Coleta Robusta de Dados
- **Bug fixado**: Corrigida lógica de busca de dia anterior que misturava D-1 e D-2
- Implementação: busca explícita por data (último dia útil antes de hoje)
- Validação: log de todas as datas coletadas antes de prosseguir

### ✅ Verificação de Notícias (Novo)
- **Filtro de data**: Remove notícias antigas (não D-1/D-0)
- **Detecção de contradições**: Cruza cada notícia com variações % reais
  - Exemplo: Notícia diz "IBOVESPA despenca" mas dados mostram +1,12% → Sinaliza
- **Corroboração multi-fonte**: Marca noticias por credibilidade
- **Rankeamento por impacto**: Ordena por variação real dos ativos
- **Hipótese causal**: LLM explica por que cada notícia impactou o mercado

### ✅ Digest Acessível
- Estrutura clara em 5 seções (panorama, destaque, global, commodities, orientação)
- Linguagem didática (explica termos financeiros)
- Sem jargão desnecessário
- Inclui nota sobre divergências de dados
- Lista fontes utilizadas

## Como Executar

### Pré-requisitos
```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Preencher: OPENROUTER_API_KEY, TAVILY_API_KEY, PERIGON_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
```

### Rodada única
```bash
python main.py
```

Output:
```
[Etapa 1/4] Coletando dados de mercado via yfinance...
  ibovespa: data=2026-04-10 fech=197324.0 var=1.12%
  usd_brl: data=2026-04-10 fech=5.0126 var=-1.72%
  ...
[Etapa 2/4] Agente Coletor buscando noticias...
[Etapa 3/4] Agente Curador verificando noticias...
[Etapa 4/4] Agente Redator gerando o digest...
Digest salvo em: ./data/outputs/digest_2026-04-10.md
Digest enviado via Telegram.
Registro salvo no SQLite.
Pipeline concluido.
```

### Agendamento diário (systemd - Linux/Mac)
```bash
# Copiar service + timer
sudo cp setup/mercado-brasil-daily.service /etc/systemd/system/
sudo cp setup/mercado-brasil-daily.timer /etc/systemd/system/

# Ativar (executa diariamente às 06h30 BRT)
sudo systemctl daemon-reload
sudo systemctl enable mercado-brasil-daily.timer
sudo systemctl start mercado-brasil-daily.timer

# Verificar
sudo systemctl status mercado-brasil-daily.timer
```

## Estrutura de Arquivos

```
mercado_brasil_daily/
├── README.md                          # Este arquivo
├── CLAUDE.md                          # Documentação arquitetural detalhada
├── main.py                            # Ponto de entrada
├── workflow.py                        # Orquestração do pipeline (4 etapas)
│
├── agents/
│   ├── coletor.py                    # Agente 1: busca notícias
│   ├── curador.py                    # Agente 2: verifica e filtra
│   └── redator.py                    # Agente 3: gera digest
│
├── tools/
│   ├── market_data.py                # Coleta yfinance (D-1 corrigido)
│   ├── news_search.py                # Buscas via DuckDuckGo (legacy)
│   ├── perigon_news.py               # Wrapper Perigon
│   ├── fact_check.py                 # Helpers de verificação
│   └── telegram_sender.py            # Entrega Telegram
│
├── config/
│   ├── settings.py                   # Configurações (tickers, APIs)
│   └── prompts.py                    # Prompts dos 3 agentes + curador
│
├── delivery/
│   └── file_writer.py                # Salva .md + seções fixas
│
├── data/
│   ├── outputs/                      # Digests gerados (digest_YYYY-MM-DD.md)
│   └── sqlite/
│       └── digests.db                # Histórico e metadados
│
├── setup/
│   ├── mercado-brasil-daily.service  # systemd service
│   └── mercado-brasil-daily.timer    # systemd timer (06h30 BRT)
│
└── requirements.txt
```

## Dados Coletados

### Mercado Brasil (8 ativos)
- **Índices**: IBOVESPA
- **Câmbio**: USD/BRL, EUR/BRL
- **Ações**: Petrobras (PETR4), Vale (VALE3), Itaú (ITUB4), Bradesco (BBDC4), Magalu (MGLU3)

### Commodities (5)
- Petróleo WTI, Brent
- Ouro, Soja, Milho

### Mercado Global (4)
- S&P 500, Nasdaq
- Índice do Dólar (DXY), Treasury 10Y

## Fluxo de Verificação de Notícias

```
Notícia bruta (Tavily/Perigon)
         ↓
[FILTRO 1: Data]
├─ Remove notícias de semanas atrás
└─ Mantém apenas D-1/D-0
         ↓
[FILTRO 2: Contradição]
├─ Cruza com dados yfinance
├─ "IBOVESPA despenca" + dados mostram +1,12% → Sinaliza inconsistência
└─ Mantém notícia mas marca como "suspeita"
         ↓
[FILTRO 3: Corroboração]
├─ 1 fonte = "nao_corroborada"
└─ 2+ fontes = "corroborada"
         ↓
[RANKEAMENTO]
├─ Variação > 2% = impacto ALTO
├─ Variação > 1% = impacto ALTO
└─ Demais = MEDIO/BAIXO
         ↓
[HIPÓTESE CAUSAL]
├─ Por que essa notícia impactou?
├─ Baseada em lógica econômica
└─ Com dados numéricos reais
         ↓
Digest final
```

## Exemplo de Output

```markdown
═══════════════════════════════════════
MERCADO BRASIL DAILY - 2026-04-10
═══════════════════════════════════════

Bom dia! Aqui está o resumo do que moveu os mercados ontem.

--- PANORAMA GERAL ---
O mercado brasileiro encerrou o dia em alta, com o Ibovespa renovando recorde 
e atingindo 197.324,0 pontos, uma valorização de 1,12%. O dólar e o euro 
registraram queda expressiva frente ao real, com o dólar fechando a R$ 5,0126 
(-1,72%) e o euro a R$ 5,8658 (-1,28%).

--- O QUE MAIS MOVEU O MERCADO ---
Ontem, a Petrobras foi destaque, com suas ações PETR4 registrando uma 
valorização de 2,36%, fechando a R$ 49,03. A valorização indicou que, 
apesar das incertezas sobre política de preços, o mercado reagiu 
positivamente ao cenário global, incluindo expectativas de cessar-fogo 
no Oriente Médio.

--- CONTEXTO GLOBAL ---
No cenário internacional, o mercado norte-americano teve um dia misto, 
com o S&P 500 em leve queda de 0,11%, enquanto o Nasdaq avançou 0,35%. 
O DXY recuou 0,17%, indicando um dólar mais fraco no mercado global.

--- COMMODITIES ---
O petróleo teve um dia de baixa, com WTI caindo 1,33% para US$ 96,57 
e Brent recuando 0,75% para US$ 95,20. O ouro também recuou 0,63%, 
enquanto a soja apresentou alta de 0,90%.

--- ORIENTAÇÃO PARA INICIANTES ---
Para o investidor iniciante, oscilações diárias como as de ontem são 
normais. O importante é manter o foco nos objetivos de longo prazo, 
diversificar investimentos entre diferentes classes de ativos, e estar 
atento a como fatores econômicos e geopolíticos globais podem influenciar 
seus ativos indiretamente.

--- NOTA SOBRE OS DADOS ---
Os dados de cotações e variações percentuais deste digest são obtidos via 
Yahoo Finance e podem apresentar pequenas divergências em relação aos valores 
oficiais divulgados pela B3 ou pelo Banco Central. Isso acontece porque 
diferentes fontes utilizam horários de corte, metodologias de cálculo e 
referências distintas.

--- FONTES ---
Dados de mercado: Yahoo Finance. Notícias: Tavily e Perigon (agregadores que 
indexam fontes como Valor Econômico, Folha de São Paulo, Estadão, O Globo, 
Bloomberg, Infomoney, Reuters, entre outras).

═══════════════════════════════════════
SDG Daily News | Gerado automaticamente
═══════════════════════════════════════
```

## Correções e Melhorias

### 🔧 Bug 1: Dados de Dias Errados (CORRIGIDO)

**Problema identificado**:
```
A função get_yesterday_data() usava iloc[-2] (índice relativo) sem validar a data real.
Se o pipeline rodava antes da abertura do mercado (06h30), iloc[-1] já era D-1,
então iloc[-2] retornava D-2. Resultado: digest misturava dados de dois dias.

Exemplo real: digest de 11/04 incluía dados de 09/04 e 10/04 ao mesmo tempo.
```

**Solução implementada**:
```python
def _get_last_business_day() -> date:
    """Calcula explicitamente o último dia útil antes de hoje."""
    hoje = datetime.now().date()
    d = hoje - timedelta(days=1)
    while d.weekday() >= 5:  # Pula sábado/domingo
        d -= timedelta(days=1)
    return d

# Buscar a linha correspondente àquela data específica
if target_date in dates:
    idx = dates.index(target_date)
```

**Resultado**: Todos os 17 tickers agora retornam dados consistentemente de D-1

### 🔧 Bug 2: Agente Reescrevendo Cotações (CORRIGIDO)

**Problema**:
```
O Coletor tinha YFinanceTools e podia buscar dados próprios via LLM,
conflitando com os dados pré-coletados. O LLM às vezes retornava valores
diferentes ou antigos dos que o Python puro tinha coletado.
```

**Solução**:
1. Remover `YFinanceTools` do Coletor
2. Atualizar prompt para instruir copiar valores exatamente
3. Dados de mercado vêm APENAS do Python puro

### ✨ Feature: Agente Curador (NOVO)

**Implementado no workflow.py — etapa 3 de 4**

Verifica notícias antes de publicação:
1. **Filtro de data** — Remove notícias antigas
2. **Detecção de contradições** — Cruza com dados reais
3. **Corroboração** — Marca credibilidade multi-fonte
4. **Rankeamento** — Ordena por impacto real
5. **Hipótese causal** — Explica impacto com dados

**Exemplo de detecção**:
- Notícia: "Petrobras recua com queda do petróleo"
- Dados reais: PETR4 +2,36%, Brent -0,75%
- Curador: Detecta contradição, mas reconhece virada intraday
- Redator: Contextualiza na seção de destaques

## Métricas de Performance

| Métrica | Valor |
|---------|-------|
| Tempo total do pipeline | ~37 segundos |
| Etapa 1 (yfinance) | ~8s |
| Etapa 2 (Coletor) | ~12s |
| Etapa 3 (Curador) | ~7s |
| Etapa 4 (Redator) | ~10s |
| Tickers monitorados | 17 |
| Notícias coletadas/rodada | ~15 brutas |
| Notícias curadas/rodada | ~7 verificadas |
| Palavras/digest | 400-600 |
| Leitura média | ~5 minutos |

## Tecnologias Principais

### APIs Externas
- **OpenRouter** — acesso a Claude/Gemini sem vendor lock-in
- **Tavily** — busca de notícias em tempo real
- **Perigon** — agregador alternativo de notícias
- **Telegram Bot API** — entrega automatizada

### Frameworks Python
- **Agno** — orquestração de agentes LLM com multi-turn
- **yfinance** — dados de mercado (sem API key necessária)
- **Pydantic** — validação de esquemas JSON

### Armazenamento
- **SQLite** — histórico local de digests
- **Markdown** — formato portável para digests

## Próximas Melhorias

- [ ] Fetch de URLs para validação de títulos (evita clickbait)
- [ ] Análise de sentimento das notícias
- [ ] Dashboard histórico com métricas de acertos
- [ ] Integração com WhatsApp
- [ ] Suporte a múltiplos idiomas (EN, ES)
- [ ] Watchlist personalizada por usuário
- [ ] Cache de notícias para evitar duplicatas multi-dia

## Aprendizados e Insights

### Por que 4 etapas e não 3?

Inicialmente tinha Coletor + Redator. Após testes reais:
- **Problema**: Notícias contraditórias ou defasadas chegavam ao digest
- **Solução**: Inserir Curador entre Coletor e Redator
- **Trade-off**: +15-20s no pipeline, mas 100% mais confiável

O Curador é o "quality gate" que garante que apenas informações verificáveis chegam ao usuário final.

### Por que OpenRouter e não API direta?

- **Flexibility**: Pode-se trocar entre Claude, Gemini, Llama sem mexer no código
- **Cost**: Geralmente mais barato que APIs diretas para cargas baixas
- **Reliability**: Fallback automático entre modelos

## Contribuindo

Este é um projeto de portfolio. Ideias/issues:
- Abra uma issue descrevendo o problema
- Com dados/exemplos quando possível
- PRs são bem-vindas com testes

## Licença

MIT — Livre para usar e modificar

---

**Desenvolvido com**: Python, LLMs (Claude/Gemini), Agno Framework  
**Para**: Investidores iniciantes brasileiros  
**Objetivo**: Democratizar análise financeira automatizada  

*SDG Daily News — Seu resumo financeiro diário, verificado.*
Vítor Emmanuel - Soli Deo Gloria (SDG)
---
*Este README foi atualizado automaticamente em 2026-06-23 09:17:04.*
---
*Este README foi atualizado automaticamente em 2026-06-23 09:23:59.*
