# Deploy — Docker + GitHub Actions

Guia completo para configurar CI/CD automatizado com Docker e deploy no Beelink.

## Arquitetura

```
GitHub Push (main branch)
         ↓
  [GitHub Actions - CI]
    ├── Lint (ruff)
    ├── Docker build
    └── dry-run test
         ↓ (se passar)
  [GitHub Actions - Deploy]
    ├── SSH no Beelink
    ├── git pull origin main
    └── docker compose build --no-cache
         ↓
  [Beelink - systemd timer]
    └── 06h30 todos os dias úteis
         ↓
  [Container Docker]
    └── python main.py (run once)
         ↓
  [Telegram + SQLite + .md]
    └── Digest entregue
```

## 1. Preparar o Beelink

### 1.1 Instalar Docker e Docker Compose

```bash
# SSH no Beelink
ssh vitor@seu_ip_beelink

# Instalar Docker (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# Adicionar vitor ao grupo docker (sem sudo)
sudo usermod -aG docker vitor
newgrp docker

# Verificar instalação
docker ps
docker compose version
```

### 1.2 Gerar chave SSH para deploy automático

```bash
# No Beelink, criar chave SSH exclusiva para deploy (SEM passphrase)
ssh-keygen -t ed25519 -f ~/.ssh/github_deploy -N ""

# Copiar a chave pública para authorized_keys
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Exibir a chave PRIVADA (será usada no GitHub Secrets)
cat ~/.ssh/github_deploy
```

### 1.3 Clonar repositório no Beelink

```bash
# No Beelink
cd /home/vitor
git clone https://github.com/seu-usuario/NewsSentiment.git
cd NewsSentiment

# Criar arquivo .env com as secrets reais
cp .env.example .env
nano .env  # preencher: OPENROUTER_API_KEY, TAVILY_API_KEY, TELEGRAM_BOT_TOKEN, etc

# Testar permissão de volume
mkdir -p data/{outputs,sqlite}
docker compose run --rm app echo "✓ Volumes OK"
```

### 1.4 Atualizar systemd timer para usar Docker

```bash
# Editar o arquivo de service
sudo nano /etc/systemd/system/mercado-brasil-daily.service
```

Substituir:

```ini
[Service]
Type=oneshot
User=vitor
WorkingDirectory=/home/vitor/NewsSentiment
# ANTES:
# ExecStart=/home/vitor/.venv/mercado_brasil/bin/python main.py

# DEPOIS:
ExecStart=/usr/bin/docker compose -f /home/vitor/NewsSentiment/docker-compose.yml run --rm app

StandardOutput=journal
StandardError=journal
```

Ativar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mercado-brasil-daily.timer
sudo systemctl restart mercado-brasil-daily.timer

# Verificar
sudo systemctl status mercado-brasil-daily.timer
journalctl -u mercado-brasil-daily -f  # seguir logs
```

---

## 2. Configurar GitHub Secrets

No repositório GitHub:

1. **Settings** → **Secrets and variables** → **Actions**
2. Adicionar 3 secrets:

| Nome | Valor |
|------|-------|
| `BEELINK_HOST` | IP ou hostname do Beelink (ex: `123.45.67.89` ou `seu-beelink.com`) |
| `BEELINK_USER` | `vitor` |
| `BEELINK_SSH_KEY` | Conteúdo completo de `~/.ssh/github_deploy` (chave PRIVADA do Beelink) |

⚠️ **IMPORTANTE:** A chave privada é sensível — nunca coloque em .env ou commit!

---

## 3. Arquivos de Docker e CI/CD

### Dockerfile
- Base: `python:3.11-slim` (leve, ~140MB)
- Instala dependências via `requirements.txt`
- Roda como usuário não-root (`appuser`)
- CMD: `python main.py`

### docker-compose.yml
- Volume: `./data` → `/app/data` (persiste outputs, SQLite)
- env_file: `.env` (secrets carregadas localmente)
- restart: `"no"` (run once, sem daemon)

### .github/workflows/ci.yml
Roda em **cada push e PR** em `main` ou `develop`:
1. **Lint** — `ruff check` para qualidade de código
2. **Build** — Constrói imagem Docker sem push
3. **Dry-run** — Executa `dry_run.py --output-only` para validar pipeline

### .github/workflows/deploy.yml
Roda **apenas em push para `main`** (após CI passar):
1. SSH no Beelink
2. `git pull origin main`
3. `docker compose build --no-cache`
4. Pronto para próxima execução do timer

---

## 4. Fluxo Completo de um Deploy

### Exemplo: Você faz um push em main

```
[1] GitHub Actions — CI inicia
    ├── Lint (ruff)
    ├── Docker build
    └── dry-run test
    
[2] Tudo passa → Deploy inicia
    ├── SSH connect ao Beelink
    ├── git pull origin main
    └── docker compose build --no-cache
    
[3] Beelink — aguarda timer
    └── 06h30 → systemd dispara: docker compose run --rm app
    
[4] Container inicia
    ├── Coleta dados (yfinance)
    ├── Curador verifica notícias
    └── Redator gera digest
    
[5] Container termina
    ├── Arquivo .md salvo em data/outputs/
    ├── Digest enviado via Telegram
    └── Metadados no SQLite
    
[6] Próxima execução: amanhã 06h30
```

---

## 5. Troubleshooting

### "Docker não acessível"
```bash
# Verificar se Docker está rodando
sudo systemctl status docker

# Adicionar vitor ao grupo docker (se necessário)
sudo usermod -aG docker vitor
# Logout e login para aplicar
```

### "Permission denied (publickey)"
```bash
# Verificar SSH key no Beelink
ls -la ~/.ssh/github_deploy

# Verificar authorized_keys
cat ~/.ssh/authorized_keys | grep "$(cat ~/.ssh/github_deploy.pub)"

# Testar SSH local
ssh -i ~/.ssh/github_deploy localhost "echo OK"
```

### "docker compose: command not found"
```bash
# Verificar instalação
docker compose version

# Se não estiver, reinstalar
sudo apt-get install -y docker-compose
```

### Deploy falhou no GitHub Actions
Verificar:
1. Logs em: **Actions** → workflow → job → logs
2. SSH key está correta? (copiar com `cat`, sem extra linhas)
3. Beelink está online e acessível?
4. Pasta `/home/vitor/NewsSentiment/` existe?

---

## 6. Monitorar Execução

### No Beelink, verificar logs do timer

```bash
# Últimas execuções do timer
sudo journalctl -u mercado-brasil-daily.timer --no-pager

# Logs detalhados do serviço
sudo journalctl -u mercado-brasil-daily.service -f

# Verificar se container rodou
docker ps -a | grep mercado-brasil-daily

# Logs do último run
docker logs $(docker ps -aq --filter="ancestor=mercado-brasil-daily:latest" | head -1)
```

### No GitHub, verificar CI/CD

1. **Actions** → workflow name
2. Clicar em cada run para ver output
3. Se Deploy falhar, investigar erro SSH

---

## 7. Atualizações Futuras

Sempre que você fizer uma mudança:

1. **Push para GitHub**
   ```bash
   git add .
   git commit -m "feat: melhorias visuais"
   git push origin main
   ```

2. **GitHub Actions roda automaticamente**
   - Lint ✓
   - Docker build ✓
   - Dry-run ✓
   - Se tudo passa → Deploy ✓

3. **Beelink recebe update**
   ```bash
   # Logs mostram:
   # [*] Deploy iniciado
   # [*] Atualizando código...
   # [*] Buildando imagem Docker...
   # [✓] Deploy concluído
   ```

4. **Próximo timer dispara**
   - 06h30 do dia seguinte
   - Usa código novo

---

## 8. Rollback (se necessário)

Se um deploy quebrou:

```bash
# No Beelink, reverter para commit anterior
cd /home/vitor/NewsSentiment
git log --oneline -n 5
git reset --hard <hash_anterior>

# Rebuild
docker compose build --no-cache

# Pronto para próximo timer
```

Ou, no GitHub, criar um novo commit que reverter as mudanças — o deploy é automático.

---

## Resumo

| Componente | Tecnologia | Frequência |
|---|---|---|
| **CI** | GitHub Actions | A cada push/PR |
| **Lint** | ruff | A cada push/PR |
| **Deploy** | SSH + appleboy/ssh-action | A cada push em main |
| **Execução** | systemd timer | 06h30 todo dia útil |
| **Container** | Docker Compose | Uma vez por dia (run once) |
| **Entrega** | Telegram + SQLite + .md | Após execução |

**Tudo automático, zero manual.** ✅

---

*Guia de deploy atualizado: 2026-04-11*
