import requests
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

MAX_MESSAGE_LENGTH = 4096


def enviar_telegram(mensagem: str, chat_id: str | None = None, token: str | None = None) -> bool:
    """Envia mensagem via Telegram Bot API. Suporta mensagens longas com split."""
    token = token or TELEGRAM_BOT_TOKEN
    chat_id = chat_id or TELEGRAM_CHAT_ID

    if not token or not chat_id:
        print("Erro: TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID nao configurados.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    chunks = _split_message(mensagem)

    for chunk in chunks:
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"Erro ao enviar Telegram: {e}")
            # Tenta sem parse_mode caso o HTML falhe
            payload.pop("parse_mode")
            try:
                resp = requests.post(url, json=payload, timeout=10)
                resp.raise_for_status()
            except requests.RequestException as e2:
                print(f"Erro ao enviar Telegram (sem parse_mode): {e2}")
                return False

    return True


def _split_message(text: str) -> list[str]:
    """Divide mensagem em chunks de ate MAX_MESSAGE_LENGTH caracteres."""
    if len(text) <= MAX_MESSAGE_LENGTH:
        return [text]

    chunks = []
    while text:
        if len(text) <= MAX_MESSAGE_LENGTH:
            chunks.append(text)
            break
        # Tenta quebrar na ultima quebra de linha antes do limite
        split_pos = text.rfind("\n", 0, MAX_MESSAGE_LENGTH)
        if split_pos == -1:
            split_pos = MAX_MESSAGE_LENGTH
        chunks.append(text[:split_pos])
        text = text[split_pos:].lstrip("\n")

    return chunks
