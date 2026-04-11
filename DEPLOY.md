# Deploy — Docker + GitHub Actions (Hostinger - AlmaLinux)

Guia completo para configurar CI/CD automatizado com Docker e deploy em VPS Hostinger com AlmaLinux.

> **Nota**: Este guia foi customizado para **Hostinger + AlmaLinux**. Se usar uma distribuição diferente (Ubuntu, Debian, CentOS), alguns comandos podem variar. Os comandos principais (`docker compose`, `systemctl`) são os mesmos em qualquer Linux.

## Arquitetura

```
GitHub Push (main branch)
         ↓
  [GitHub Actions - CI]
    ├── Lint (ruff)
    ├── Build Docker image
    ├── Push para GHCR
    └── Dry-run test
         ↓ (se passar)
  [GitHub Actions - Deploy]
    ├── SSH na VPS Hostinger
    └── docker compose pull (pega imagem nova do GHCR)
         ↓
  [VPS Hostinger - systemd timer]
    └── 06h30 todos os dias úteis
         ↓
  [Container Docker] (imagem pré-compilada)
    └── python main.py (run once)
         ↓
  [Telegram + SQLite + .md]
    └── Digest entregue
```

**Diferença do fluxo anterior:**
- ❌ Não precisa clonar repositório na VPS
- ❌ Não precisa de Dockerfile na VPS
- ❌ Não precisa de código Python na VPS
- ✅ Imagem pré-compilada vem do GHCR
- ✅ Setup é 30 segundos: mkdir + docker-compose.yml + .env

## 1. Preparar a VPS (Hostinger - AlmaLinux)

### 1.1 Instalar Docker e Docker Compose

```bash
# SSH na VPS Hostinger
ssh vitor@seu_ip_vps

# Atualizar sistema (AlmaLinux/RHEL)
sudo dnf update -y

# Instalar dependências
sudo dnf install -y dnf-plugins-core

# Adicionar repositório Docker (oficial)
sudo dnf config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo

# Instalar Docker e Docker Compose (AlmaLinux)
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Iniciar Docker
sudo systemctl start docker
sudo systemctl enable docker

# Adicionar vitor ao grupo docker (sem sudo)
sudo usermod -aG docker vitor
newgrp docker

# Verificar instalação
docker ps
docker compose version
```

### 1.2 Gerar chave SSH para deploy automático

```bash
# Na VPS Hostinger, criar chave SSH exclusiva para deploy (SEM passphrase)
ssh-keygen -t ed25519 -f ~/.ssh/github_deploy -N ""

# Copiar a chave pública para authorized_keys
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Exibir a chave PRIVADA (será usada no GitHub Secrets)
cat ~/.ssh/github_deploy
```

> **Nota sobre Hostinger**: Se você estiver usando painel de controle Hostinger, verifique:
> - SSH está ativado (geralmente vem ativado)
> - Porta SSH (default 22, pode estar customizada)
> - IP público da VPS (vem no email de ativação)

### 1.3 Setup da VPS Hostinger (Muito Simples!)

Diferente do fluxo antigo, **você não precisa clonar o repositório**. Só de um `docker-compose.yml`:

```bash
# Na VPS Hostinger — criar diretórios
sudo mkdir -p /opt/SDGNews/{data/{outputs,sqlite}}
sudo chown -R vitor:vitor /opt/SDGNews

cd /opt/SDGNews

# Baixar docker-compose.yml do repositório
curl -o docker-compose.yml https://raw.githubusercontent.com/vitorpq/SDGNews/main/docker-compose.yml

# Baixar .env.example e adaptar
curl -o .env.example https://raw.githubusercontent.com/vitorpq/SDGNews/main/.env.example
cp .env.example .env
nano .env  # preencher: OPENROUTER_API_KEY, TAVILY_API_KEY, TELEGRAM_BOT_TOKEN, etc

# Verificar permissão de volumes
ls -la data/
```

**Isso é tudo!** A imagem Docker vem pré-compilada do GHCR.

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
WorkingDirectory=/opt/SDGNews
# ANTES:
# ExecStart=/home/vitor/.venv/mercado_brasil/bin/python main.py

# DEPOIS:
ExecStart=/usr/bin/docker compose -f /opt/SDGNews/docker-compose.yml run --rm app

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
| `BEELINK_HOST` | IP ou hostname da VPS Hostinger (ex: `123.45.67.89`) |
| `BEELINK_USER` | `vitor` (seu usuário SSH) |
| `BEELINK_SSH_KEY` | Conteúdo completo de `~/.ssh/github_deploy` (chave PRIVADA) |

**Notas:**
- ⚠️ Chave privada é sensível — nunca coloque em .env ou commit!
- `GITHUB_TOKEN` é automático (GitHub fornece no workflow, não precisa configurar)
- O token é usado para autenticar no GHCR (GitHub Container Registry)

---

## 3. Fluxo de CI/CD com GHCR

### .github/workflows/ci.yml (Build + Push)
1. **Lint** — ruff valida código
2. **Build Docker** — constrói imagem
3. **Push para GHCR** — `ghcr.io/vitorpq/sdgnews:latest`
   - Usa `GITHUB_TOKEN` (automático)
   - Imagem fica privada (acesso via token)

### .github/workflows/deploy.yml (Pull + Run)
1. **SSH na VPS** — conecta via chave privada
2. **Docker login GHCR** — autentica usando `GITHUB_TOKEN`
3. **docker compose pull** — baixa imagem nova
4. **Cleanup** — remove imagens dangling

### docker-compose.yml (Na VPS)
```yaml
services:
  app:
    image: ghcr.io/vitorpq/sdgnews:latest  # Imagem pré-compilada
    pull_policy: always                     # Sempre verifica atualizações
    volumes:
      - ./data:/app/data                    # Persiste saídas
    env_file: .env                          # Secrets locais
    restart: "no"                           # Run once (não daemon)
```

**Nota:** Não precisa de Dockerfile na VPS! A imagem já vem pronta.
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
[1] GitHub Actions — CI inicia (automático)
    ├── Lint com ruff
    ├── Build Docker image
    ├── Push para GHCR (ghcr.io/vitorpq/sdgnews:latest)
    └── Teste dry-run
    
[2] Tudo passa → Deploy inicia
    ├── SSH conecta à VPS Hostinger
    ├── Autentica no GHCR (docker login)
    └── docker compose pull (baixa image nova)
    
[3] VPS Hostinger — aguarda timer systemd
    └── 06h30 (seg-sex) → systemd dispara: docker compose run --rm app
    
[4] Container inicia (imagem pré-compilada do GHCR)
    ├── Coleta dados (yfinance)
    ├── Curador verifica notícias
    └── Redator gera digest
    
[5] Container termina
    ├── Arquivo .md salvo em ./data/outputs/
    ├── Digest enviado via Telegram
    └── Metadados no SQLite
    
[6] Próxima execução: amanhã 06h30 (automaticamente)
    (VPS usa a image já baixada, sem reconectar ao GHCR)
```

**Vantagens:**
- ✅ Cada push constrói **1 vez** no GitHub (máquina poderosa)
- ✅ VPS só **puxa** imagem (rápido, ~30s)
- ✅ Sem código-fonte na VPS (segurança)
- ✅ Sem Dockerfile na VPS

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

# Se não estiver, reinstalar (AlmaLinux)
sudo dnf install -y docker-compose-plugin
sudo systemctl restart docker
```

### "Error response from daemon: unauthorized: authentication required" (GHCR)

Significa que o Docker não conseguiu autenticar no GHCR. Solução:

```bash
# Fazer login manual no GHCR (use seu GitHub token)
docker login ghcr.io

# Username: seu_usuario_github
# Password: seu_github_token (Personal Access Token com acesso a packages)

# Testar pull
docker compose pull

# Se ainda não funcionar, logout e reconectar
docker logout ghcr.io
docker login ghcr.io
```

**Nota:** O workflow do GitHub usa `secrets.GITHUB_TOKEN` automaticamente, mas na VPS você pode precisar fazer login manualmente uma vez.

### "image not found" no docker compose pull

Significa que o workflow ainda não completou o push. Verifique:

```bash
# No GitHub Actions
1. Ir em Actions → workflow → logs
2. Procurar por "Build and push Docker image" — deve ter sucesso
3. Tag deve ser: ghcr.io/vitorpq/sdgnews:latest (ou seu username)

# Na VPS, validar imagem disponível
docker images | grep ghcr.io

# Se não aparecer, executar push manualmente (via GitHub Actions)
```

### "SELinux permission denied" (AlmaLinux/Hostinger)

AlmaLinux usa SELinux por padrão. Se vir erros de permissão ao rodar Docker:

```bash
# Opção 1: Desabilitar SELinux (simples, menos seguro)
sudo semanage permissive -a container_t
sudo semanage permissive -a docker_t

# Opção 2: Mudar modo SELinux para permissive
sudo setenforce 0
# Para tornar permanente, editar /etc/selinux/config e mudar SELINUX=permissive
```

Depois reiniciar Docker:

```bash
sudo systemctl restart docker
```

### Deploy falhou no GitHub Actions
Verificar:
1. Logs em: **Actions** → workflow → job → logs
2. SSH key está correta? (copiar com `cat`, sem extra linhas)
3. VPS Hostinger está online e acessível?
4. Pasta `/opt/SDGNews/` existe?
5. Porta SSH está aberta no firewall da Hostinger (painel → Segurança → Firewall)

---

## 6. Monitorar Execução

### Na VPS Hostinger, verificar logs do timer

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
cd /opt/SDGNews
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
