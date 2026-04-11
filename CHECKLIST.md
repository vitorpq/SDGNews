# Checklist — Deploy Automático

Guia passo a passo para colocar o projeto em produção com Docker + GitHub Actions.

## ✅ Fase 1: Preparação Local (Já Feito)

- [x] Criar `Dockerfile` (python:3.11-slim, non-root user)
- [x] Criar `docker-compose.yml` (volume data, env_file)
- [x] Criar `.dockerignore` (51 padrões)
- [x] Criar `.github/workflows/ci.yml` (lint + build + dry-run)
- [x] Criar `.github/workflows/deploy.yml` (SSH + git pull + docker compose build)
- [x] Criar `DEPLOY.md` (documentação completa)

## ⏳ Fase 2: Preparação do Beelink

### 2.1 Instalar Docker
```bash
ssh vitor@seu_ip_beelink

sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo usermod -aG docker vitor
newgrp docker
docker ps
```
- [ ] Docker instalado e testado

### 2.2 Gerar SSH Key para Deploy
```bash
ssh-keygen -t ed25519 -f ~/.ssh/github_deploy -N ""
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
cat ~/.ssh/github_deploy  # copiar este valor
```
- [ ] Chave SSH gerada e testada

### 2.3 Clonar e Configurar Repositório
```bash
cd /home/vitor
git clone https://github.com/seu-usuario/NewsSentiment.git
cd NewsSentiment
cp .env.example .env
nano .env  # preencher: OPENROUTER_API_KEY, TAVILY_API_KEY, etc
mkdir -p data/{outputs,sqlite}
```
- [ ] Repositório clonado
- [ ] `.env` configurado com secrets reais
- [ ] Diretórios criados

### 2.4 Testar Docker Localmente
```bash
docker compose run --rm app python dry_run.py --no-telegram
```
- [ ] Container builda sem erros
- [ ] dry_run executa com sucesso

## ⏳ Fase 3: Configuração do GitHub

### 3.1 Adicionar Secrets
1. Ir em **Settings** → **Secrets and variables** → **Actions**
2. Adicionar:
   - `BEELINK_HOST` = IP ou hostname do Beelink
   - `BEELINK_USER` = `vitor`
   - `BEELINK_SSH_KEY` = conteúdo da chave privada (~/.ssh/github_deploy)

- [ ] `BEELINK_HOST` adicionado
- [ ] `BEELINK_USER` adicionado
- [ ] `BEELINK_SSH_KEY` adicionado

### 3.2 Verificar Workflows
1. **Actions** → Verificar se `ci.yml` e `deploy.yml` aparecem
2. Fazer um push dummy para testar CI
   ```bash
   git push origin main
   ```
- [ ] CI rodou com sucesso (lint + build + dry-run)
- [ ] Deploy rodou com sucesso (SSH + git pull + docker compose build)

## ⏳ Fase 4: Atualizar systemd Timer

### 4.1 Editar arquivo de service
```bash
sudo nano /etc/systemd/system/mercado-brasil-daily.service
```

Substituir:
```ini
# ANTES:
ExecStart=/home/vitor/.venv/mercado_brasil/bin/python main.py

# DEPOIS:
ExecStart=/usr/bin/docker compose -f /home/vitor/NewsSentiment/docker-compose.yml run --rm app
```

### 4.2 Recarregar e ativar
```bash
sudo systemctl daemon-reload
sudo systemctl enable mercado-brasil-daily.timer
sudo systemctl restart mercado-brasil-daily.timer
sudo systemctl status mercado-brasil-daily.timer
```
- [ ] systemd timer configurado com docker compose

## ⏳ Fase 5: Testes de Ponta a Ponta

### 5.1 Testar execução manual no Beelink
```bash
cd /home/vitor/NewsSentiment
docker compose run --rm app
```
Verificar:
- Digest salvo em `data/outputs/digest_YYYY-MM-DD.md`
- Telegram recebeu a mensagem
- Metadados salvos no SQLite

- [ ] Execução manual bem-sucedida

### 5.2 Testar timer (simular execução agendada)
```bash
# Forçar execução do timer (será a próxima execução prevista)
sudo systemctl start mercado-brasil-daily.timer

# Acompanhar logs
sudo journalctl -u mercado-brasil-daily.service -f
```

Verificar:
- Container inicia e termina sem erros
- Arquivo .md gerado
- Telegram notificado
- Sem permissão ou erro de acesso

- [ ] Execução via timer bem-sucedida

### 5.3 Testar deploy automático
```bash
# No seu computador local
echo "# Teste de deploy" >> README.md
git add README.md
git commit -m "test: deploy automation"
git push origin main
```

Verificar no GitHub:
- CI roda automaticamente
- Deploy roda automaticamente
- No Beelink: verificar `cd NewsSentiment && git log --oneline | head -1`

- [ ] Deploy automático funcionando

## ⏳ Fase 6: Monitoramento Contínuo

### 6.1 Criar script de healthcheck (opcional)
```bash
# No Beelink, criar /home/vitor/check_digest.sh
#!/bin/bash
latest=$(ls -t data/outputs/digest_*.md | head -1)
if [ -f "$latest" ]; then
    modified=$(find "$latest" -type f -mtime -1)
    if [ ! -z "$modified" ]; then
        echo "✓ Digest atualizado hoje"
        exit 0
    fi
fi
echo "✗ Digest antigo ou não encontrado"
exit 1
```

Chamar via cron (verificação extra):
```bash
# 07h00 diariamente (10 min depois do pipeline)
0 7 * * * /home/vitor/check_digest.sh || curl -X POST https://hooks.slack.com/... -d "Alert: digest não foi gerado"
```

- [ ] Script de healthcheck criado (opcional)

## 📋 Resumo da Arquitetura Final

```
GitHub Repository
├── .github/workflows/
│   ├── ci.yml          → lint + docker build + dry-run (toda push)
│   └── deploy.yml      → SSH deploy (push em main)
├── Dockerfile          → python:3.11-slim
├── docker-compose.yml  → volumes + env
├── .dockerignore       → otimização de build
└── [outros arquivos]

        ↓ (git push main)

GitHub Actions
├── CI:
│   ├── Lint (ruff)
│   ├── Docker build
│   └── dry-run test
└── Deploy (se CI passar):
    ├── SSH no Beelink
    ├── git pull origin main
    └── docker compose build --no-cache

        ↓

Beelink VPS
├── /home/vitor/NewsSentiment/
│   ├── .env (secrets)
│   ├── data/ (volumes persistidos)
│   └── docker-compose.yml
└── systemd timer
    └── 06h30 todo dia útil
        └── docker compose run --rm app

        ↓

Container Docker
└── python main.py
    ├── Coleta dados (yfinance)
    ├── Curador verifica notícias
    ├── Redator gera digest
    └── Entrega (Telegram + SQLite + .md)
```

## 🎯 Próximas Ações

1. **Completar Checklist acima** ✓
2. **Git push** para GitHub
3. **Monitorar CI/CD** na aba Actions
4. **Verificar Beelink** — próxima execução 06h30
5. **Receber digest** no Telegram automaticamente 🎉

---

## 🔗 Referências Rápidas

- **Documentação completa**: `DEPLOY.md`
- **Troubleshooting**: `DEPLOY.md` seção 5
- **Logs no Beelink**: `sudo journalctl -u mercado-brasil-daily -f`
- **Logs no GitHub**: **Actions** tab → workflow

---

*Checklist criado: 2026-04-11 | Versão: 1.0*
