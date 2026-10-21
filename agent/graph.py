"""The LangGraph agent, built by hand so you can see every piece.

            +----------+   tool calls?   +---------+
  START --> |  agent   | ---- yes -----> |  tools  |
            |  (LLM)   | <-------------- |         |
            +----------+                 +---------+
                 | no
                 v
                END

(`langchain.agents.create_agent` builds this same loop in one line.)
"""

from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agent.llm import get_llm
from agent.tools import TOOLS

SYSTEM_PROMPT = """Tu es un assistant commercial intelligent.

Tu as accès à 3 outils :
- search_web : pour les infos récentes sur internet
- get_odoo_leads : pour voir le pipeline CRM Odoo et chercher un client
- send_email : pour envoyer un email via Gmail (l'utilisateur valide avant l'envoi)

Règles :
1. Toujours utiliser un outil avant de répondre si la question concerne des données concrètes
2. Si tu ne trouves pas l'info — dis-le clairement
3. Réponses courtes et factuelles
4. Réponds dans la langue de l'utilisateur"""


def build_graph():
    # bind_tools sends each tool's name, docstring and argument schema to the LLM.
    llm_with_tools = get_llm().bind_tools(TOOLS)

    def agent_node(state: MessagesState):
        messages = [SystemMessage(SYSTEM_PROMPT)] + state["messages"]
        return {"messages": [llm_with_tools.invoke(messages)]}

    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(TOOLS))  # runs the tool calls the LLM asked for

    builder.add_edge(START, "agent")
    # tools_condition: go to "tools" if the LLM asked for a tool, otherwise END.
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")

    # The checkpointer gives the agent memory (per thread_id) and is
    # required for interrupt() / human-in-the-loop.
    return builder.compile(checkpointer=InMemorySaver())
