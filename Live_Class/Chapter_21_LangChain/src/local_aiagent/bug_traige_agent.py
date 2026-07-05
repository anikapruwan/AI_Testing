"""Bug triage agent — fetch JIRA ticket(s), triage each one.

Flow:
  user enters one or more JIRA keys  ->  fetch_jira_ticket (tool) pulls each
  ticket from the JIRA REST API and formats it as a bug report  ->  the LLM
  triages each report into a structured Triage  ->  printed one by one.

.env needs:
  GROQ_API_KEY      groq key (judge/triager)
  LLM_MODEL         a Groq model that supports json_schema structured output
                    (e.g. openai/gpt-oss-120b — llama-3.1-8b-instant does NOT)
  JIRA_URL          e.g. https://your-org.atlassian.net
  JIRA_EMAIL        the account email
  JIRA_API_TOKEN    https://id.atlassian.com/manage-profile/security/api-tokens
"""
import os

import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool

load_dotenv()


# -------------------- structured triage output --------------------

class Triage(BaseModel):
    title: str            = Field(description="One-line normalized title")
    severity: str         = Field(description="Critical | High | Medium | Low")
    priority: str         = Field(description="P0 | P1 | P2 | P3")
    component: str        = Field(description="Most likely affected area")
    suggested_team: str   = Field(description="Team that should own this")
    likely_duplicate: bool = Field(description="True if it looks known")
    reasoning: str        = Field(description="2-3 line justification")


# -------------------- JIRA fetch tool --------------------

def _adf_to_text(node) -> str:
    """Flatten Atlassian Document Format (API v3 description) into plain text."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "".join(_adf_to_text(n) for n in node)
    if isinstance(node, dict):
        if node.get("type") == "text":
            return node.get("text", "")
        text = _adf_to_text(node.get("content"))
        # block-level nodes get a trailing newline so paragraphs/lists stay readable
        if node.get("type") in {"paragraph", "heading", "listItem", "blockquote", "codeBlock"}:
            text += "\n"
        return text
    return ""


@tool
def fetch_jira_ticket(ticket_key: str) -> str:
    """Fetch a single JIRA ticket by its key (e.g. 'PROJ-123') and return it
    formatted as a bug report (title, type, priority, status, components,
    description). Use this whenever you need the details of a JIRA issue."""
    base = (os.getenv("JIRA_URL") or "").rstrip("/")
    email = os.getenv("JIRA_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")
    if not (base and email and token):
        return "ERROR: set JIRA_URL, JIRA_EMAIL and JIRA_API_TOKEN in .env"

    url = f"{base}/rest/api/3/issue/{ticket_key.strip()}"
    try:
        r = requests.get(
            url,
            auth=(email, token),
            headers={"Accept": "application/json"},
            params={"fields": "summary,description,issuetype,priority,status,components,labels,reporter"},
            timeout=30,
        )
        r.raise_for_status()
    except requests.HTTPError as e:
        return f"ERROR fetching {ticket_key}: {e.response.status_code} {e.response.text[:200]}"
    except requests.RequestException as e:
        return f"ERROR fetching {ticket_key}: {e}"

    f = r.json().get("fields", {})
    summary = f.get("summary", "(no summary)")
    desc = _adf_to_text(f.get("description")).strip() or "(no description)"
    issuetype = (f.get("issuetype") or {}).get("name", "?")
    priority = (f.get("priority") or {}).get("name", "?")
    status = (f.get("status") or {}).get("name", "?")
    components = ", ".join(c.get("name", "") for c in (f.get("components") or [])) or "—"
    labels = ", ".join(f.get("labels") or []) or "—"
    reporter = (f.get("reporter") or {}).get("displayName", "?")

    return (
        f"[{ticket_key}] {summary}\n"
        f"Type: {issuetype} | Priority: {priority} | Status: {status}\n"
        f"Components: {components} | Labels: {labels} | Reporter: {reporter}\n\n"
        f"Description:\n{desc}"
    )


# -------------------- triager (structured output) --------------------
# json_schema constrains generation to the schema, so booleans come back as real
# booleans (function_calling lets the model emit "False" as a string -> Groq 400).

prompt = ChatPromptTemplate.from_messages([
    ("system", "You triage bugs for a web product. Map user impact to "
               "severity and business urgency to priority. Be decisive."),
    ("human", "Bug report:\n\n{report}"),
])


def build_chain():
    """Build the triage chain. Reads GROQ_API_KEY / LLM_MODEL at call time, so
    the .env can be (re)written by the UI before this runs."""
    llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)
    triager = llm.with_structured_output(Triage, method="json_schema")
    return prompt | triager


def triage_ticket(ticket_key: str, chain=None) -> dict:
    """Fetch + triage one ticket. Returns a dict:
       {"key", "report", "triage": Triage}  or  {"key", "report", "error"}."""
    report = fetch_jira_ticket.invoke({"ticket_key": ticket_key})
    if report.startswith("ERROR"):
        return {"key": ticket_key, "report": report, "error": report}
    chain = chain or build_chain()
    result = chain.invoke({"report": report})
    return {"key": ticket_key, "report": report, "triage": result}


def _print_result(res: dict) -> None:
    print("=" * 70)
    print(f"TICKET: {res['key']}")
    if res.get("error"):
        print(res["error"])
        return
    t = res["triage"]
    print(f"Title : {t.title}")
    print(f"{t.severity} / {t.priority}  ->  {t.component}")
    print(f"Owner : {t.suggested_team}  | dupe? {t.likely_duplicate}")
    print(f"Why   : {t.reasoning}")


if __name__ == "__main__":
    raw = input("Enter JIRA ticket key(s), comma-separated (e.g. PROJ-1, PROJ-2): ")
    keys = [k.strip() for k in raw.replace(",", " ").split() if k.strip()]
    if not keys:
        print("No ticket keys given.")
    chain = build_chain() if keys else None
    for key in keys:
        _print_result(triage_ticket(key, chain))
