# Comandos de Referência Rápida

Comandos úteis para desenvolvimento, testes e troubleshooting.

## Desenvolvimento Local

### Rodar pipeline completo
```bash
python main.py
```

### Rodar apenas dry-run (sem APIs)
```bash
# Mostrar no terminal
python dry_run.py --output-only

# Enviar ao Telegram (testa configuração)
python dry_run.py

# Apenas salvar arquivo .md
python dry_run.py --no-telegram
```

### Lint com ruff
```bash
# Verificar código
ruff check . --select E,W,F,I

# Formatar código
ruff format .

# Verificar formatação
ruff format . --check
```

---

## Docker Local (no seu computador)

### Build da imagem
```bash
docker build -t mercado-brasil-daily:latest .
```

### Rodar container uma vez
```bash
docker compose run --rm app
```

### Rodar container com shell interativo
```bash
docker compose run --rm app /bin/bash
```

### Ver logs do container
```bash
docker compose logs -f
```

### Limpar volumes e rebuild
```bash
docker compose down -v
docker compose up --build
```

---

## Beelink — Manutenção

### SSH no Beelink
```bash
ssh vitor@seu_ip_beelink
cd /home/vitor/NewsSentiment
```

### Verificar status do timer
```bash
sudo systemctl status mercado-brasil-daily.timer
sudo systemctl status mercado-brasil-daily.service
```

### Ver logs do serviço
```bash
# Últimas execuções
sudo journalctl -u mercado-brasil-daily.service --no-pager | head -50

# Seguir em tempo real
sudo journalctl -u mercado-brasil-daily.service -f
```

### Forçar execução imediata do timer
```bash
cd /home/vitor/NewsSentiment
docker compose run --rm app
```

### Verificar dados persistidos
```bash
ls -lah data/outputs/         # digests gerados
sqlite3 data/sqlite/digests.db ".tables"  # verificar banco
```

### Atualizar repositório manualmente
```bash
cd /home/vitor/NewsSentiment
git pull origin main
docker compose build --no-cache
```

### Verificar uso de disco (Docker)
```bash
docker system df
docker image prune -a  # limpar imagens antigos
docker volume prune    # limpar volumes
```

---

## GitHub — CI/CD

### Verificar workflows
```bash
# Local: validar YAML
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"
python -c "import yaml; yaml.safe_load(open('.github/workflows/deploy.yml'))"
```

### Forçar rerun de workflow
1. Ir em **Actions** → workflow
2. Clicar em um run
3. **Re-run all jobs** ou **Re-run failed jobs**

### Debug de SSH no Beelink (via GitHub Actions)
```bash
# Ativar debug mode (no arquivo workflow)
# adicionar: env: { ACTIONS_STEP_DEBUG: true }

# Ou testar SSH localmente:
ssh -i ~/.ssh/github_deploy vitor@seu_ip_beelink "echo OK"
```

---

## Troubleshooting Rápido

### "Port 5432 already in use" (PostgreSQL/Redis conflitando)
```bash
docker compose down -v
docker ps -a | grep mercado-brasil-daily
docker rm <container-id>
```

### "Permission denied" ao acessar volumes
```bash
# Verificar proprietário
ls -la data/
sudo chown -R 1000:1000 data/
```

### "Docker daemon not running"
```bash
# Iniciar daemon
sudo systemctl start docker

# Verificar status
sudo systemctl status docker

# Ver logs
sudo journalctl -u docker -f
```

### "ModuleNotFoundError" no container
```bash
# Verificar requirements.txt está atualizado
pip freeze > requirements_check.txt
diff requirements.txt requirements_check.txt

# Reinstalar deps
docker compose build --no-cache
```

### Terraform/Kubernetes não aplicável
Este projeto usa **Docker Compose + systemd**, não Kubernetes. K8s é overkill para um bot diário.

---

## Monitoramento e Alertas

### Verificar se digest foi gerado hoje
```bash
# No Beelink
find data/outputs -name "digest_$(date +%Y-%m-%d).md"
```

### Ver quantos digests foram gerados
```bash
ls -1 data/outputs/ | wc -l
```

### Consultar histórico no SQLite
```bash
sqlite3 data/sqlite/digests.db "SELECT data_referencia, status_envio FROM digests ORDER BY data_geracao DESC LIMIT 10;"
```

### Testar conexão Telegram
```bash
# No Beelink, testar se token e chat ID estão corretos
python3 << 'EOF'
import os
import requests
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

url = f"https://api.telegram.org/bot{token}/sendMessage"
payload = {"chat_id": chat_id, "text": "✓ Teste de conexão OK"}
resp = requests.post(url, json=payload)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.json()}")
EOF
```

---

## Git — Workflow

### Criar branch para feature
```bash
git checkout -b feat/nova-feature
# fazer alterações
git add .
git commit -m "feat: descrição da mudança"
git push origin feat/nova-feature
# criar PR no GitHub
```

### Revert de último commit (se houver erro)
```bash
git revert HEAD --no-edit
git push origin main
```

### Ver histórico de deployments
```bash
git log --oneline | head -20
git tag -l  # se usar tags para releases
```

---

## Checklist Diário (Ops)

- [ ] Verificar se digest foi gerado e enviado
  ```bash
  tail data/outputs/digest_*.md
  ```

- [ ] Verificar logs de sucesso
  ```bash
  sudo journalctl -u mercado-brasil-daily --no-pager | grep "Pipeline concluido"
  ```

- [ ] Monitorar uso de disco
  ```bash
  df -h data/
  ```

- [ ] Verificar erros no SQLite
  ```bash
  sqlite3 data/sqlite/digests.db "SELECT * FROM erros_pipeline ORDER BY data_hora DESC LIMIT 5;" 2>/dev/null || echo "Nenhum erro"
  ```

---

## Links Úteis

- **Dashboard GitHub**: https://github.com/seu-usuario/NewsSentiment/actions
- **Logs Beelink**: `sudo journalctl -u mercado-brasil-daily -f`
- **Documentação**: `README.md`, `SETUP.md`, `DEPLOY.md`, `VISUAL_DESIGN.md`
- **Docker Hub**: https://hub.docker.com/_/python/tags (imagem base)

---

*Atualizado: 2026-04-11*
