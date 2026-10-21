"""The agent's toolbox. Add a new tool here and the agent will see it."""

from agent.tools.gmail import send_email
from agent.tools.odoo_crm import get_odoo_leads
from agent.tools.web_search import search_web

TOOLS = [search_web, get_odoo_leads, send_email]
