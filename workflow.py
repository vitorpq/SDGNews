import json
import sqlite3
import os
from datetime import datetime, timedelta

from agents.coletor import criar_agente_coletor
from agents.curador import criar_agente_curador
from agents.redator import criar_agente_redator
from tools.market_data import get_all_market_data
from delivery.file_writer import salvar_digest_md
from tools.telegram_sender import enviar_telegram
from config.settings import SQLITE_DB_PATH


def init_db():
    """Cria tabela de digests se nao existir."""
    os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS digests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_referencia TEXT NOT NULL,
            data_geracao TEXT NOT NULL,
            digest_completo TEXT,
            status_envio TEXT DEFAULT 'pendente'
        )
    """)
    conn.commit()
    conn.close()


def salvar_no_sqlite(digest: str, data_referencia: str, status_envio: str = "pendente"):
    """Registra o digest no SQLite."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.execute(
        "INSERT INTO digests (data_referencia, data_geracao, digest_completo, status_envio) VALUES (?, ?, ?, ?)",
        (data_referencia, datetime.now().isoformat(), digest, status_envio),
    )
    conn.commit()
    conn.close()


def run_pipeline():
    """Executa o pipeline completo: coleta -> redacao -> entrega."""
    print(f"[{datetime.now()}] Iniciando SDG Daily News...")

    init_db()
    data_referencia = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # --- ETAPA 1: Coleta de dados de mercado via yfinance (Python puro) ---
    print("[Etapa 1/4] Coletando dados de mercado via yfinance...")
    dados_mercado = get_all_market_data()

    # Log de verificacao: mostrar datas coletadas para debug
    for categoria in ["mercado_br", "commodities", "mercado_global"]:
        for nome, dados in dados_mercado[categoria].items():
            if "data" in dados:
                print(f"  {nome}: data={dados['data']} fech={dados.get('fechamento', 'N/A')} var={dados.get('variacao_pct', 'N/A')}%")
            elif "erro" in dados:
                print(f"  {nome}: ERRO - {dados['erro']}")

    print(f"  Coletados: {len(dados_mercado['mercado_br'])} ativos BR, "
          f"{len(dados_mercado['commodities'])} commodities, "
          f"{len(dados_mercado['mercado_global'])} globais")

    # --- ETAPA 2: Agente Coletor busca noticias ---
    print("[Etapa 2/4] Agente Coletor buscando noticias...")
    agente_coletor = criar_agente_coletor()

    prompt_coletor = (
        f"Data de referencia: {data_referencia}\n\n"
        f"Dados de mercado ja coletados (yfinance):\n"
        f"{json.dumps(dados_mercado, ensure_ascii=False, indent=2)}\n\n"
        f"Com base nesses dados, busque noticias financeiras relevantes usando "
        f"Tavily e Perigon. Foque em noticias que expliquem as variacoes observadas. "
        f"Retorne o JSON completo com dados de mercado + noticias curadas."
    )

    resp_coletor = agente_coletor.run(prompt_coletor)
    dados_coletados = resp_coletor.content

    # --- ETAPA 3: Agente Curador verifica e filtra noticias ---
    print("[Etapa 3/4] Agente Curador verificando noticias...")
    agente_curador = criar_agente_curador()

    prompt_curador = (
        f"Data de referencia: {data_referencia}\n\n"
        f"=== DADOS DE MERCADO REAIS (yfinance) ===\n"
        f"{json.dumps(dados_mercado, ensure_ascii=False, indent=2)}\n\n"
        f"=== NOTICIAS BRUTAS (coletadas pelo agente anterior) ===\n"
        f"{dados_coletados}\n\n"
        f"Faca a curadoria: filtre por data, descarte contradicoes com os dados "
        f"reais, verifique corroboracao, rankeie por impacto e identifique a "
        f"noticia principal."
    )

    resp_curador = agente_curador.run(prompt_curador)
    noticias_curadas = resp_curador.content

    # --- ETAPA 4: Agente Redator gera o digest ---
    print("[Etapa 4/4] Agente Redator gerando o digest...")
    agente_redator = criar_agente_redator()

    prompt_redator = (
        f"Data de referencia: {data_referencia}\n\n"
        f"Dados de mercado (yfinance):\n"
        f"{json.dumps(dados_mercado, ensure_ascii=False, indent=2)}\n\n"
        f"Noticias curadas e verificadas:\n{noticias_curadas}\n\n"
        f"Redija o digest financeiro diario completo."
    )

    resp_redator = agente_redator.run(prompt_redator)
    digest_final = resp_redator.content

    # --- ENTREGA ---
    # Salvar como arquivo .md (retorna caminho, texto_telegram, texto_md)
    caminho, texto_telegram, texto_md = salvar_digest_md(digest_final, data_referencia, dados_mercado)
    print(f"Digest salvo em: {caminho}")

    # Enviar via Telegram (texto com dashboard + HTML)
    sucesso_telegram = enviar_telegram(texto_telegram)
    status = "enviado" if sucesso_telegram else "erro_telegram"
    if sucesso_telegram:
        print("Digest enviado via Telegram.")
    else:
        print("Falha ao enviar via Telegram (digest salvo em arquivo).")

    # Registrar no SQLite (versão Telegram que será entregue)
    salvar_no_sqlite(texto_telegram, data_referencia, status)
    print(f"Registro salvo no SQLite.")

    print(f"[{datetime.now()}] Pipeline concluido.")
    return digest_final
