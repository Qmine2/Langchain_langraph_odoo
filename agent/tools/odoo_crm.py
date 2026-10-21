"""Tool 2 — Read CRM leads from Odoo through its XML-RPC external API.

Docs: https://www.odoo.com/documentation/18.0/developer/reference/external_api.html
"""

import os
import xmlrpc.client

from langchain_core.tools import tool

FIELDS = ["name", "partner_name", "email_from", "expected_revenue", "probability", "stage_id"]


@tool
def get_odoo_leads(limit: int = 5, search: str = "") -> str:
    """Récupère les leads CRM depuis Odoo.
    Utilise pour : voir le pipeline, chercher un client,
    vérifier les opportunités en cours.

    Args:
        limit: nombre de leads à récupérer (défaut: 5)
        search: nom du client ou du lead à chercher (optionnel, vide = tous)
    """
    url = os.getenv("ODOO_URL", "").rstrip("/")
    db = os.getenv("ODOO_DB")
    user = os.getenv("ODOO_USER")
    password = os.getenv("ODOO_PASSWORD")  # password OR API key

    if not all([url, db, user, password]):
        return "Erreur Odoo : ODOO_URL, ODOO_DB, ODOO_USER et ODOO_PASSWORD doivent être définis dans .env"

    try:
        # 1. Authenticate -> returns the numeric user id (uid), or False.
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        uid = common.authenticate(db, user, password, {})
        if not uid:
            return "Erreur Odoo : authentification refusée (vérifie user / mot de passe / base)."

        # 2. Build an Odoo "domain" (a list of filters). Empty = all records.
        domain = []
        if search:
            domain = ["|", ("name", "ilike", search), ("partner_name", "ilike", search)]

        # 3. Call search_read on the crm.lead model.
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
        leads = models.execute_kw(
            db, uid, password,
            "crm.lead", "search_read",
            [domain],
            {"fields": FIELDS, "limit": limit, "order": "create_date desc"},
        )
    except Exception as e:
        return f"Erreur Odoo : {e}"

    if not leads:
        return "Aucun lead trouvé."

    # Many2one fields like stage_id come back as [id, "Display name"].
    lines = []
    for lead in leads:
        stage = lead["stage_id"][1] if lead["stage_id"] else "-"
        lines.append(
            f"- {lead['name']} | client: {lead['partner_name'] or '-'} | "
            f"email: {lead['email_from'] or '-'} | étape: {stage} | "
            f"revenu attendu: {lead['expected_revenue']} | probabilité: {lead['probability']}%"
        )
    return "\n".join(lines)
