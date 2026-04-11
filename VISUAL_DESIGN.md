# Design Visual — SDG Daily News

## Redesign Implementado

O digest agora é **"escaneável"** — o leitor bate o olho e entende o cenário em segundos, sem precisar ler parágrafos inteiros.

---

## O Que Mudou

### 1. Dashboard de Abertura (Novo)
Gerado automaticamente pelo sistema com dados reais do yfinance:

```
📊 FECHAMENTO DO DIA

IBOVESPA          197.324  +1.12%  🟢
DÓLAR              5.0126  -1.72%  🟢
EUR/BRL            5.8658  -1.28%  🟢
PETR4               49.03  +2.36%  🟢
VALE3               85.59  +1.06%  🟢
ITUB4               46.07  +0.70%  🟢
BRENT                95.2  -0.75%  🔴
OURO            4761.8999  -0.63%  🔴
S&P 500             6.817  -0.11%  🔴
```

**Características:**
- Números alinhados em fonte `monospace` (legível em Telegram)
- **Semáforo de cores**: 🟢 (altas), 🔴 (baixas), 🔵 (neutro)
- **Lógica invertida para dólar/euro**: queda do dólar = 🟢 (bom para o brasileiro)
- **Ordem estratégica**: Brasil primeiro (ativos que o leitor se importa), depois commodities, depois global

---

### 2. Emojis Temáticos nas Seções
Substitui os separadores `---` por emojis que indicam o assunto:

```
📰 PANORAMA GERAL
[Comportamento geral do mercado]

🚀 O QUE MAIS MOVEU O MERCADO
[Notícia principal com lista de destaques]

🌍 CONTEXTO GLOBAL
[Eventos internacionais relevantes]

📦 COMMODITIES
[Preços de commodities]

🎓 ORIENTAÇÃO PARA INICIANTES
[Dica educativa do dia]
```

**Benefício**: Cada seção é imediatamente identificável pelo emoji, facilitando navegação no Telegram (scroll rápido).

---

### 3. Bold Estratégico
O bold (negrito) é usado **apenas** para os dados numéricos mais importantes, não para frases inteiras:

**❌ Antes:**
> O mercado brasileiro encerrou o dia em alta...

**✅ Depois:**
> O **IBOVESPA** avançou **+1,12%**, refletindo o otimismo dos investidores. O dólar registrou uma queda de **-1,72%**, fechando a **R$ 5,0126**.

**Por quê?** Se o leitor estiver com pressa, consegue ler apenas os números em bold e captar 80% da informação em 10 segundos.

---

### 4. Lista de Destaques com Emojis
Nova seção dentro de "O QUE MAIS MOVEU O MERCADO":

```
DESTAQUES DO DIA:
• ⚓ PETR4: subiu +2,36%, a R$ 49,03
• ⛏️ VALE3: avançou +1,06%, a R$ 85,59
• 🏦 Bancos: ITUB4 +0,70% | BBDC4 +0,74%
```

**Emojis por setor:**
- ⚓ Petróleo/Energia
- ⛏️ Mineração
- 🏦 Bancos/Financeiro
- 🌾 Agronegócio (quando relevante)

---

### 5. Divisores Temáticos
Divisores visuais que quebram o texto monótono:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

No Telegram, isso fica como uma linha contínua que ajuda a separar blocos visualmente.

---

## Exemplo Real de Output

```
🇧🇷 SDG DAILY NEWS
Sexta, 10 de abril de 2026

📊 FECHAMENTO DO DIA

IBOVESPA          197.324  +1.12%  🟢
DÓLAR              5.0126  -1.72%  🟢
EUR/BRL            5.8658  -1.28%  🟢
PETR4               49.03  +2.36%  🟢
VALE3               85.59  +1.06%  🟢
ITUB4               46.07  +0.70%  🟢
BRENT                95.2  -0.75%  🔴
OURO            4761.8999  -0.63%  🔴
S&P 500             6.817  -0.11%  🔴

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📰 PANORAMA GERAL
O mercado brasileiro fechou o dia em alta, impulsionado por um cenário externo 
mais favorável. O IBOVESPA avançou +1,12%, refletindo o otimismo dos investidores. 
O dólar registrou uma queda de -1,72%, fechando a R$ 5,0126.

🚀 O QUE MAIS MOVEU O MERCADO
A principal notícia do dia foi o cessar-fogo entre EUA e Irã. Essa notícia teve 
um impacto significativo no dólar, que caiu -1,72%, e nos preços do petróleo...

DESTAQUES DO DIA:
• ⚓ PETR4: subiu +2,36%, a R$ 49,03
• ⛏️ VALE3: avançou +1,06%, a R$ 85,59
• 🏦 Bancos: ITUB4 +0,70% | BBDC4 +0,74%

🌍 CONTEXTO GLOBAL
Nos mercados internacionais, o cenário foi misto...

📦 COMMODITIES
O petróleo registrou queda, com o Brent recuando -0,75%...

🎓 ORIENTAÇÃO PARA INICIANTES
Para quem está começando a investir, dias como hoje reforçam...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ NOTA SOBRE OS DADOS
Os dados de cotações... [informações sobre fontes]

📎 FONTES
Dados de mercado: Yahoo Finance
Notícias: Tavily e Perigon...
```

---

## Implementação Técnica

### Arquivos Modificados

1. **`delivery/file_writer.py`**
   - Adicionado `_gerar_dashboard_telegram()` — retorna HTML formatado
   - Adicionado `_gerar_dashboard_md()` — versão limpa para arquivo local
   - Função `_calcular_semaforo()` com lógica invertida para dólar/euro
   - Dashboard é injetado NO INÍCIO do digest (antes do conteúdo do LLM)

2. **`tools/telegram_sender.py`**
   - Mudado `parse_mode` de `"Markdown"` para `"HTML"`
   - HTML é mais robusto com números e símbolos financeiros

3. **`config/prompts.py` — PROMPT_REDATOR**
   - Novo template com emojis temáticos (📰 🚀 🌍 📦 🎓)
   - Instrução clara de usar `<b>bold</b>` APENAS para números
   - Seção de "DESTAQUES" com bullets e emojis por setor
   - Dashboard NÃO é gerado pelo LLM (já vem automático)

4. **`workflow.py`**
   - Passo `salvar_digest_md()` recebe `dados_mercado` como parâmetro
   - Retorna 3 valores: `(caminho, texto_telegram, texto_md)`
   - Telegram recebe versão com HTML; arquivo .md recebe versão limpa

---

## Experiência do Usuário

### No Telegram (Mobile)
- **Scroll rápido**: Emojis nas seções tornam fácil achar a informação
- **Leitura rápida**: Bold nos números permite entender em 30 segundos
- **Dashboard claro**: Números alinhados em fonte mono, com semáforo visual

### No Email/Desktop
- **Legível**: Arquivo .md salvo localmente sem tags HTML
- **Profissional**: Formatação Markdown limpa, sem poluição visual
- **Armazenável**: Fácil de arquivar e consultar histórico

---

## Métricas

| Aspecto | Antes | Depois |
|---------|-------|--------|
| Tempo para entender cenário | ~3 min (ler tudo) | ~30 seg (dashboard + bold) |
| Emojis de contexto | 0 | 15+ (semáforo + temas) |
| Linhas de dashboard | 0 | 10 (números principais) |
| Parse_mode Telegram | Markdown | HTML (mais robusto) |
| Versões do texto | 1 (genérico) | 2 (Telegram HTML + .md limpo) |

---

## Próximas Ideias

- [ ] Links clicáveis nas ações (ex: PETR4 → página do Status Invest)
- [ ] Gráficos/sparklines mostrando tendência (se API permitir)
- [ ] Categorização por setores (ex: "Destaque de Energia", "Destaque de Varejo")
- [ ] Voto de confiança: "Dia Bom" 🟢 / "Dia Misto" 🔵 / "Dia Ruim" 🔴 no início

---

*Design focado em experiência de usuário mobile, acessibilidade visual e leitura rápida.*
