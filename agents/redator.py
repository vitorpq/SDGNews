from agno.agent import Agent
from agno.models.openrouter import OpenRouter

from config.settings import OPENROUTER_MODEL
from config.prompts import PROMPT_REDATOR


def criar_agente_redator() -> Agent:
    """Cria o Agente 2: Redator do digest financeiro."""
    return Agent(
        name="RedatorFinanceiro",
        model=OpenRouter(id=OPENROUTER_MODEL),
        instructions=PROMPT_REDATOR,
        markdown=False,
    )
