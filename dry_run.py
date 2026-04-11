#!/usr/bin/env python3
"""
Dry-run do pipeline — testa formato visual sem chamar APIs externas.

Útil para:
- Validar formatação do Telegram
- Testar sem gastar tokens/créditos
- Desenvolvimento e debugging

Uso:
    python dry_run.py                    # Enviar ao Telegram
    python dry_run.py --no-telegram      # Apenas salvar arquivo .md
    python dry_run.py --output-only      # Mostrar output no terminal
"""

import sys
from delivery.file_writer import salvar_digest_md
from tools.telegram_sender import enviar_telegram


# Dados fictícios para o dashboard
DADOS_MERCADO_MOCK = {
    "mercado_br": {
        "ibovespa": {"fechamento": 197324.0, "variacao_pct": 1.12, "data": "2026-04-10"},
        "usd_brl": {"fechamento": 5.0126, "variacao_pct": -1.72, "data": "2026-04-10"},
        "eur_brl": {"fechamento": 5.8658, "variacao_pct": -1.28, "data": "2026-04-10"},
        "petr4": {"fechamento": 49.03, "variacao_pct": 2.36, "data": "2026-04-10"},
        "vale3": {"fechamento": 85.59, "variacao_pct": 1.06, "data": "2026-04-10"},
        "itub4": {"fechamento": 46.07, "variacao_pct": 0.70, "data": "2026-04-10"},
        "bbdc4": {"fechamento": 20.44, "variacao_pct": 0.74, "data": "2026-04-10"},
        "mglu3": {"fechamento": 9.15, "variacao_pct": -0.87, "data": "2026-04-10"},
    },
    "commodities": {
        "petroleo_wti": {"fechamento": 96.57, "variacao_pct": -1.33, "data": "2026-04-10"},
        "petroleo_brent": {"fechamento": 95.2, "variacao_pct": -0.75, "data": "2026-04-10"},
        "ouro": {"fechamento": 4761.8999, "variacao_pct": -0.63, "data": "2026-04-10"},
        "soja": {"fechamento": 1175.75, "variacao_pct": 0.90, "data": "2026-04-10"},
        "milho": {"fechamento": 441.0, "variacao_pct": -0.68, "data": "2026-04-10"},
    },
    "mercado_global": {
        "sp500": {"fechamento": 6816.8901, "variacao_pct": -0.11, "data": "2026-04-10"},
        "nasdaq": {"fechamento": 22902.8906, "variacao_pct": 0.35, "data": "2026-04-10"},
        "dxy": {"fechamento": 98.65, "variacao_pct": -0.17, "data": "2026-04-10"},
        "treasury_10y": {"fechamento": 4.317, "variacao_pct": 0.56, "data": "2026-04-10"},
    },
}

# Conteúdo narrativo fictício (simulando saída do LLM)
CONTEUDO_NARRATIVO = """
📰 <b>PANORAMA GERAL</b>
O mercado brasileiro fechou o dia em alta, impulsionado por um cenário externo mais favorável. O <b>IBOVESPA</b> avançou <b>+1,12%</b>, refletindo o otimismo dos investidores. O dólar registrou uma queda expressiva de <b>-1,72%</b>, fechando a <b>R$ 5,0126</b>, o que aliviou a pressão sobre a inflação.

🚀 <b>O QUE MAIS MOVEU O MERCADO</b>
A principal notícia do dia foi o anúncio de um cessar-fogo de 15 dias entre os Estados Unidos e o Irã. Essa notícia teve um impacto significativo no dólar, que caiu <b>-1,72%</b>, e nos preços do petróleo, com o Brent recuando <b>-0,75%</b>. A estabilização na relação entre as potências do Oriente Médio tende a diminuir a percepção de risco geopolítico global.

DESTAQUES DO DIA:
• ⚓ <b>PETR4</b>: subiu <b>+2,36%</b>, a <b>R$ 49,03</b>
• ⛏️ <b>VALE3</b>: avançou <b>+1,06%</b>, a <b>R$ 85,59</b>
• 🏦 <b>Bancos</b>: <b>ITUB4 +0,70%</b> | <b>BBDC4 +0,74%</b>

🌍 <b>CONTEXTO GLOBAL</b>
Nos mercados internacionais, o cenário foi misto. O <b>S&P 500</b> registrou uma leve queda de <b>-0,11%</b>, enquanto o Nasdaq teve um desempenho positivo, subindo <b>+0,35%</b>. A notícia do cessar-fogo entre EUA e Irã foi o principal destaque, contribuindo para uma percepção de menor risco.

📦 <b>COMMODITIES</b>
As commodities tiveram um dia de oscilações. O petróleo registrou queda, com o Brent recuando <b>-0,75%</b> para <b>US$ 95,20</b> e o WTI caindo <b>-1,33%</b>, fechando a <b>US$ 96,57</b>. O ouro também apresentou desvalorização de <b>-0,63%</b>, cotado a <b>US$ 4.761,90</b>.

🎓 <b>ORIENTAÇÃO PARA INICIANTES</b>
Para quem está começando a investir, dias como hoje reforçam a importância de entender como eventos globais afetam o seu patrimônio. A queda do dólar e as variações nas commodities são exemplos de como o mundo está conectado. Em vez de reagir impulsivamente, o ideal é focar em construir uma carteira diversificada com objetivos de longo prazo.
"""


def dry_run(enviar_telegram_flag=True, output_only=False):
    """
    Executa um dry-run do pipeline com dados fictícios.

    Args:
        enviar_telegram_flag: Se True, envia ao Telegram
        output_only: Se True, apenas mostra no terminal (não salva em arquivo)
    """
    print("\n" + "="*60)
    print("DRY-RUN — SDG Daily News")
    print("="*60)
    print("\n[*] Usando dados fictícios (sem chamar yfinance, Tavily, OpenRouter)")

    data_referencia = "2026-04-10"

    # Gerar o digest com dados ficticíos
    print(f"[*] Gerando digest para {data_referencia}...")
    caminho, texto_telegram, texto_md = salvar_digest_md(
        CONTEUDO_NARRATIVO,
        data_referencia,
        DADOS_MERCADO_MOCK
    )

    print(f"[✓] Digest gerado")
    print(f"    - Arquivo .md: {caminho}")
    print(f"    - Telegram: {len(texto_telegram)} caracteres")

    # Opção 1: Apenas mostrar no terminal
    if output_only:
        print("\n" + "="*60)
        print("OUTPUT (versão Telegram)")
        print("="*60)
        print(texto_telegram)
        print("\n" + "="*60)
        print("OUTPUT (versão .md)")
        print("="*60)
        print(texto_md)
        return

    # Opção 2: Enviar ao Telegram
    if enviar_telegram_flag:
        print("\n[*] Enviando ao Telegram...")
        sucesso = enviar_telegram(texto_telegram)
        if sucesso:
            print("[✓] Enviado com sucesso ao Telegram!")
        else:
            print("[✗] Falha ao enviar. Verifique TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID")
            return False
    else:
        print("\n[*] Skipped Telegram (use --send-telegram para enviar)")

    print("\n[✓] Dry-run concluído!")
    print(f"    Arquivo salvo: {caminho}")
    return True


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Dry-run do pipeline — testa sem chamar APIs externas"
    )
    parser.add_argument(
        "--no-telegram",
        action="store_true",
        help="Não enviar ao Telegram (apenas salvar arquivo)"
    )
    parser.add_argument(
        "--output-only",
        action="store_true",
        help="Apenas mostrar output no terminal (não salva arquivo nem envia Telegram)"
    )
    parser.add_argument(
        "--send-telegram",
        action="store_true",
        help="Enviar ao Telegram (padrão se nem --no-telegram nem --output-only)"
    )

    args = parser.parse_args()

    # Determinar comportamento
    enviar = not args.no_telegram and not args.output_only
    if args.output_only:
        enviar = False

    try:
        sucesso = dry_run(
            enviar_telegram_flag=enviar,
            output_only=args.output_only
        )
        sys.exit(0 if sucesso else 1)
    except Exception as e:
        print(f"\n[✗] Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
