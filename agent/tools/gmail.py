"""Tool 3 — Send an email with the Gmail API (Google OAuth 2.0).

First run: a browser window opens, you log in with Google and accept the
"send email" permission. The resulting token is saved to GMAIL_TOKEN_FILE
so you are not asked again.

Safety: before anything is sent, the graph PAUSES (LangGraph `interrupt`)
and main.py asks the human to approve the email.
"""

import base64
import os
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from langchain_core.tools import tool
from langgraph.types import interrupt

# Smallest scope we need: send only (cannot read the inbox).
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def get_gmail_service():
    """Return an authenticated Gmail API client, running the OAuth flow if needed."""
    credentials_file = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
    token_file = os.getenv("GMAIL_TOKEN_FILE", "token.json")

    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # silent refresh
        else:
            if not os.path.exists(credentials_file):
                raise FileNotFoundError(
                    f"{credentials_file} introuvable — télécharge-le depuis Google Cloud Console (voir README)."
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)  # opens the browser
        with open(token_file, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Envoie un email depuis le compte Gmail de l'utilisateur.
    Utilise pour : relancer un client, envoyer un récapitulatif,
    répondre à un prospect. L'utilisateur doit valider avant l'envoi.

    Args:
        to: adresse email du destinataire
        subject: objet de l'email
        body: contenu de l'email (texte brut)
    """
    # Human-in-the-loop: pause the graph and wait for approval.
    decision = interrupt({"to": to, "subject": subject, "body": body})
    if decision != "yes":
        return "Envoi annulé par l'utilisateur."

    try:
        message = EmailMessage()
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        sent = (
            get_gmail_service()
            .users().messages()
            .send(userId="me", body={"raw": raw})
            .execute()
        )
        return f"Email envoyé à {to} (id: {sent['id']})."
    except Exception as e:
        return f"Erreur Gmail : {e}"
