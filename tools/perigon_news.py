import os
import requests
from agno.tools import Toolkit


class PerigonTools(Toolkit):
    """Custom Agno toolkit para buscar noticias via Perigon API."""

    def __init__(self, api_key: str | None = None):
        super().__init__(name="perigon_tools")
        self.api_key = api_key or os.getenv("PERIGON_API_KEY")
        self.base_url = "https://api.goperigon.com/v1"
        self.register(self.search_news)

    def search_news(self, query: str, country: str = "br", max_results: int = 5) -> str:
        """Busca noticias financeiras via Perigon API.

        Args:
            query: Termo de busca (ex: 'Bovespa mercado financeiro')
            country: Codigo do pais (default: 'br' para Brasil)
            max_results: Numero maximo de resultados (default: 5)

        Returns:
            String com as noticias encontradas formatadas.
        """
        if not self.api_key:
            return "Erro: PERIGON_API_KEY nao configurada."

        try:
            params = {
                "apiKey": self.api_key,
                "q": query,
                "country": country,
                "size": max_results,
                "sortBy": "date",
                "sourceGroup": "top100",
            }
            resp = requests.get(f"{self.base_url}/all", params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            articles = data.get("articles", [])
            if not articles:
                return f"Nenhuma noticia encontrada para: {query}"

            resultados = []
            for art in articles:
                resultados.append(
                    f"- Titulo: {art.get('title', 'N/A')}\n"
                    f"  Fonte: {art.get('source', {}).get('domain', 'N/A')}\n"
                    f"  Data: {art.get('pubDate', 'N/A')}\n"
                    f"  Resumo: {art.get('description', art.get('summary', 'N/A'))}"
                )

            return f"Noticias encontradas ({len(resultados)}):\n\n" + "\n\n".join(resultados)

        except requests.RequestException as e:
            return f"Erro ao buscar noticias no Perigon: {str(e)}"
