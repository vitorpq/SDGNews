# Setup — Guia de Configuração

Instruções passo a passo para configurar o SDG Daily News localmente.

## Pré-requisitos

- Python 3.11 ou superior
- pip ou uv (gerenciador de pacotes)
- Git
- Uma conta no Telegram (para receber digests)

## 1. Clonar o Repositório

```bash
git clone https://github.com/seu-usuario/NewsSentiment.git
cd NewsSentiment
```

## 2. Criar Ambiente Virtual

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

## 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

## 4. Obter Chaves de API

Você precisará de 3 chaves de API externas. **Todas têm tier gratuito**.

### 4.1 OpenRouter (Modelos de IA)

1. Acesse [https://openrouter.ai](https://openrouter.ai)
2. Faça sign-up (gratuito)
3. Vá para [https://openrouter.ai/keys](https://openrouter.ai/keys)
4. Copie sua chave: `sk-or-...`
5. Você receberá $5 em crédito inicial (suficiente para ~500 rodadas do pipeline)

### 4.2 Tavily (Busca de Notícias)

1. Acesse [https://tavily.com](https://tavily.com)
2. Faça sign-up (gratuito)
3. Vá para [https://dashboard.tavily.com/api-keys](https://dashboard.tavily.com/api-keys)
4. Copie sua chave: `tvly-...`
5. Tier gratuito: 100 buscas/mês

### 4.3 Perigon (Agregador de Notícias)

1. Acesse [https://www.perigon.com](https://www.perigon.com)
2. Faça sign-up (gratuito)
3. Vá para [https://dashboard.perigon.com](https://dashboard.perigon.com)
4. Copie sua chave: `perigon_...`
5. Tier gratuito: 250 requisições/mês

### 4.4 Telegram Bot (Entrega)

1. Abra o Telegram e procure por **@BotFather**
2. Envie `/newbot`
3. Siga as instruções (escolha nome e username para seu bot)
4. BotFather retornará seu **Bot Token**: `123456:ABC-DEF1234ghIkl-...`
5. Guarde esse token

**Obter seu Chat ID:**

1. Abra o Telegram e procure por **@userinfobot**
2. Envie `/start`
3. O bot retornará seu ID (um número como `123456789`)
4. Guarde esse ID

Ou alternativamente:

1. Abra seu bot criado acima no Telegram
2. Envie qualquer mensagem
3. Acesse: `https://api.telegram.org/bot<SEU_BOT_TOKEN>/getUpdates`
4. Procure por `"chat": {"id": <numero>}` e copie o número

## 5. Configurar Variáveis de Ambiente

```bash
# Copiar o arquivo de exemplo
cp .env.example .env

# Abrir em seu editor
nano .env  # ou use VS Code, Sublime, etc
```

Preencher com suas chaves:

```env
OPENROUTER_API_KEY=sk-or-...
TAVILY_API_KEY=tvly-...
PERIGON_API_KEY=perigon_...
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-...
TELEGRAM_CHAT_ID=123456789
```

Salvar e fechar.

## 6. Verificar Configuração

```bash
python -c "from config.settings import *; print('✓ Configuração OK')"
```

Se não houver erro, você está pronto!

## 7. Rodada de Teste

Executar uma rodada do pipeline:

```bash
python main.py
```

Esperado:

```
[Etapa 1/4] Coletando dados de mercado via yfinance...
  ibovespa: data=2026-04-10 fech=197324.0 var=1.12%
  ...
[Etapa 2/4] Agente Coletor buscando noticias...
[Etapa 3/4] Agente Curador verificando noticias...
[Etapa 4/4] Agente Redator gerando o digest...
Digest salvo em: ./data/outputs/digest_YYYY-MM-DD.md
Digest enviado via Telegram.
```

Verifique se o digest chegou no seu Telegram!

## 8. Agendamento Diário (Opcional)

### Linux/macOS com systemd

```bash
# Copiar arquivos de serviço
sudo cp setup/mercado-brasil-daily.service /etc/systemd/system/
sudo cp setup/mercado-brasil-daily.timer /etc/systemd/system/

# Editar o .service para apontar para seu path real
sudo nano /etc/systemd/system/mercado-brasil-daily.service
```

Alterar:
- `WorkingDirectory=/home/vitor/NewsSentiment` → seu path real
- `ExecStart=...python main.py` → seu python real (use `which python` para verificar)
- `User=vitor` → seu usuário

Adicionar as variáveis de ambiente no serviço:

```ini
[Service]
Type=oneshot
User=seu_usuario
WorkingDirectory=/caminho/real/NewsSentiment
Environment="OPENROUTER_API_KEY=sk-or-..."
Environment="TAVILY_API_KEY=tvly-..."
Environment="PERIGON_API_KEY=perigon_..."
Environment="TELEGRAM_BOT_TOKEN=..."
Environment="TELEGRAM_CHAT_ID=..."
ExecStart=/usr/bin/python3 main.py
StandardOutput=journal
StandardError=journal
```

Ativar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mercado-brasil-daily.timer
sudo systemctl start mercado-brasil-daily.timer

# Verificar status
sudo systemctl status mercado-brasil-daily.timer
sudo journalctl -u mercado-brasil-daily -f  # seguir logs
```

### macOS com launchd (alternativa a systemd)

1. Criar arquivo `~/Library/LaunchAgents/com.vitorbrasil.mercadobrasil.plist`
2. Adicionar:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.vitorbrasil.mercadobrasil</string>
    <key>ProgramArguments</key>
    <array>
        <string>/caminho/real/venv/bin/python</string>
        <string>/caminho/real/NewsSentiment/main.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/caminho/real/NewsSentiment</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>OPENROUTER_API_KEY</key>
        <string>sk-or-...</string>
        <key>TAVILY_API_KEY</key>
        <string>tvly-...</string>
        <!-- adicionar outras variáveis aqui -->
    </dict>
    <key>StartCalendarInterval</key>
    <array>
        <dict>
            <key>Hour</key>
            <integer>6</integer>
            <key>Minute</key>
            <integer>30</integer>
            <key>Weekday</key>
            <integer>0</integer>
        </dict>
        <!-- repetir para cada dia útil (1-5) -->
    </array>
    <key>StandardOutPath</key>
    <string>/tmp/mercado-brasil.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/mercado-brasil-error.log</string>
</dict>
</plist>
```

Ativar:

```bash
launchctl load ~/Library/LaunchAgents/com.vitorbrasil.mercadobrasil.plist
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'agno'"

```bash
# Reinstalar dependências
pip install --upgrade -r requirements.txt
```

### "OPENROUTER_API_KEY not set"

Verificar se `.env` foi criado e preenchido corretamente:

```bash
cat .env | grep OPENROUTER
```

### "Timeout ao buscar notícias"

Normal em conexões lentas. O timeout padrão é 10s. Aumentar em `tools/telegram_sender.py`:

```python
resp = requests.post(url, json=payload, timeout=30)  # aumentar de 10 para 30
```

### "SQLite database is locked"

Não rodas dois pipelines simultaneamente. Verificar:

```bash
ps aux | grep main.py
```

Se houver dois processos, matar um:

```bash
kill -9 <PID>
```

### "Telegram message too long"

O Telegram tem limite de 4096 caracteres por mensagem. O sistema já split automaticamente. Se problema persistir, reduzir o tamanho do digest em `config/prompts.py`:

```python
# Mudar de 400-600 palavras para 300-400
"O texto final deve ter entre 300 e 400 palavras"
```

## Estrutura de Diretórios Criada

Após primeira execução:

```
NewsSentiment/
├── .env                           # Sua configuração (NÃO commitar)
├── data/
│   ├── outputs/
│   │   ├── digest_2026-04-10.md
│   │   ├── digest_2026-04-11.md
│   │   └── ... (um por dia)
│   └── sqlite/
│       └── digests.db             # Histórico
└── logs/                          # Se configurado
```

## Próximos Passos

1. **Rodada manual** — `python main.py` e verificar output
2. **Revisar digest** — Abrir `data/outputs/digest_*.md` no editor
3. **Agendar** — Configurar systemd ou launchd para execução diária
4. **Customizar** — Ajustar tickers ou prompts em `config/settings.py` e `config/prompts.py`

## Suporte

Dúvidas ou problemas:

1. Verificar os logs: `tail -f /tmp/mercado-brasil.log`
2. Rodar manualmente: `python main.py` (mostra output detalhado)
3. Abrir uma issue no GitHub com logs

---

**Pronto! Seu SDG Daily News está configurado e rodando.** 🚀
