from agno.agent import Agent
from agno.models.openrouter import OpenRouter

from config.settings import OPENROUTER_MODEL
from config.prompts import PROMPT_CURADOR


def criar_agente_curador() -> Agent:
    """Cria o Agente Curador: verifica, filtra e rankeia noticias contra dados reais."""
    return Agent(
        name="CuradorDeNoticias",
        model=OpenRouter(id=OPENROUTER_MODEL),
        instructions=PROMPT_CURADOR,
        markdown=False,
        debug_mode=True,
    )
