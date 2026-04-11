# Build stage
FROM python:3.11-slim as builder

WORKDIR /tmp
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Criar usuário não-root para segurança
RUN useradd -m -u 1000 appuser

# Copiar dependências do builder
COPY --from=builder /root/.local /home/appuser/.local

# Copiar código da aplicação
COPY --chown=appuser:appuser . .

# Definir variáveis de ambiente
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Switch para usuário não-root
USER appuser

# Health check (opcional — verifica se main.py consegue ser importado)
HEALTHCHECK --interval=60s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import main; print('OK')" || exit 1

# Comando padrão: executar o pipeline
CMD ["python", "main.py"]
