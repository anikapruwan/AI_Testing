"""Bug triage agent (RAG-grounded) — fetch JIRA ticket(s), triage each one.

Flow:
  user enters one or more JIRA keys  ->  fetch_jira_ticket pulls each ticket
  from the JIRA REST API and formats it as a bug report  ->  the RAG knowledge
  base returns the top-3 most-similar items (past bugs / test cases / related
  VWO tickets / PDFs)  ->  the LLM triages the report GROUNDED in that prior
  knowledge into a structured Triage  ->  printed one by one.

Build the knowledge base first:  python -m rag.ingest   (from chapter root)

.env needs:
  GROQ_API_KEY      groq key (judge/triager)
  LLM_MODEL         a Groq model that supports json_schema structured output
                    (e.g. openai/gpt-oss-120b — llama-3.1-8b-instant does NOT)
  JIRA_URL          e.g. https://your-org.atlassian.net
  JIRA_EMAIL        the account email
  JIRA_API_TOKEN    https://id.atlassian.com/manage-profile/security/api-tokens
RAG uses local Ollama `nomic-embed-text` + a local Chroma DB (no extra keys).
"""
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool

# make the chapter-root `rag` package importable when run from src/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rag import retrieve, format_context

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
    ("system", "You triage bugs for the VWO web product. You are given PRIOR "
               "KNOWLEDGE retrieved from a RAG knowledge base — the most similar "
               "past bugs, test cases and related tickets. Ground your decision "
               "in that precedent: if similar past items map a component to a "
               "team / severity / priority, follow that mapping unless the "
               "report clearly differs. Map user impact to severity and "
               "business urgency to priority. Be decisive."),
    ("human", "PRIOR KNOWLEDGE (top matches from RAG):\n{context}\n\n"
              "Bug report to triage:\n\n{report}"),
])


def build_chain():
    """Build the triage chain. Reads GROQ_API_KEY / LLM_MODEL at call time, so
    the .env can be (re)written by the UI before this runs."""
    llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)
    triager = llm.with_structured_output(Triage, method="json_schema")
    return prompt | triager


def get_rag_context(report: str, k: int = 3, exclude_ids=None) -> tuple[str, list]:
    """Retrieve top-k knowledge items for a report. Returns (rendered, items).
    Degrades gracefully to empty context if the RAG/Ollama is unavailable."""
    try:
        items = retrieve(report, k=k, exclude_ids=exclude_ids)
    except Exception as e:
        return f"(RAG unavailable: {e})", []
    return format_context(items), items


def triage_ticket(ticket_key: str, chain=None, k: int = 3) -> dict:
    """Fetch -> RAG-retrieve -> triage one ticket. Returns a dict:
       {"key", "report", "context", "rag": [items], "triage": Triage}
       or {"key", "report", "error"}."""
    report = fetch_jira_ticket.invoke({"ticket_key": ticket_key})
    if report.startswith("ERROR"):
        return {"key": ticket_key, "report": report, "error": report}
    # exclude the ticket's own indexed copy so precedent comes from OTHER items
    context, items = get_rag_context(report, k=k, exclude_ids=[f"JIRA-{ticket_key}"])
    chain = chain or build_chain()
    result = chain.invoke({"report": report, "context": context})
    return {"key": ticket_key, "report": report, "context": context,
            "rag": items, "triage": result}


def _print_result(res: dict) -> None:
    print("=" * 70)
    print(f"TICKET: {res['key']}")
    if res.get("error"):
        print(res["error"])
        return
    rag = res.get("rag") or []
    print(f"RAG top-{len(rag)} used:")
    for r in rag:
        m = r["metadata"]
        print(f"  - [{m.get('type')}] {r['id']}  (score {1 - r['distance']:.2f})")
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
