from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.tools.tavily import TavilyTools

from config.settings import OPENROUTER_MODEL
from config.prompts import PROMPT_COLETOR
from tools.perigon_news import PerigonTools


def criar_agente_coletor() -> Agent:
    """Cria o Agente 1: Coletor de noticias (dados de mercado vem do yfinance via Python)."""
    return Agent(
        name="ColetorDeMercado",
        model=OpenRouter(id=OPENROUTER_MODEL),
        tools=[
            TavilyTools(
                enable_search=True,
                max_tokens=4000,
                search_depth="advanced",
                include_answer=True,
            ),
            PerigonTools(),
        ],
        instructions=PROMPT_COLETOR,
        markdown=False,
        debug_mode=True,
    )
