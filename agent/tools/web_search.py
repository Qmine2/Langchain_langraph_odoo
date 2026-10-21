"""Tool 1 — Web search with Tavily (https://tavily.com).

Tavily is a search API designed for LLMs: it returns short, clean text
snippets instead of raw HTML pages.
"""

from langchain_core.tools import tool
from langchain_tavily import TavilySearch


@tool
def search_web(query: str) -> str:
    """Cherche des informations récentes sur internet.
    Utilise pour : actualités, prix marché, infos concurrents,
    tout ce que tu ne trouves pas dans les autres outils.

    Args:
        query: la requête de recherche (ex: "Odoo 18 nouveautés CRM")
    """
    try:
        # Reads TAVILY_API_KEY from the environment.
        response = TavilySearch(max_results=3).invoke({"query": query})
    except Exception as e:
        return f"Erreur recherche web : {e}"

    results = response.get("results", [])
    if not results:
        return "Aucun résultat trouvé."

    return "\n\n".join(
        f"- {r['title']}\n  {r['url']}\n  {r['content']}" for r in results
    )
