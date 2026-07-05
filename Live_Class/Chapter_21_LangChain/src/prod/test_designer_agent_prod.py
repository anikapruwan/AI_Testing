"""Test-designer agent (production) — JIRA story in, RAG-grounded test plan out.

Flow:
  user gives a JIRA key (project VWO)
    -> fetch_jira_story   pulls the story from JIRA (REST v3, ADF -> text)
    -> qa_copilot_search  retrieves similar EXISTING test cases from the QA
                          Copilot RAG (local Chroma KB, 200+ VWO items)
    -> the LLM designs a structured TestPlan grounded in BOTH the story and the
       prior test cases (so it reuses conventions and avoids duplicating cases).

Build the RAG first (once):   python -m rag.ingest    (from chapter root)

.env needs:
  GROQ_API_KEY   groq key
  LLM_MODEL      tool-calling Groq model (default llama-3.3-70b-versatile)
  JIRA_URL       e.g. https://your-org.atlassian.net
  JIRA_EMAIL     account email
  JIRA_API_TOKEN https://id.atlassian.com/manage-profile/security/api-tokens
RAG uses local Ollama nomic-embed-text — no extra keys.
"""
import os
import sys
from pathlib import Path
from typing import List

import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate

# make the sibling `rag` package importable (it lives in the chapter root)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from rag import retrieve, format_context  # QA Copilot RAG

load_dotenv()


# -------------------- structured output --------------------

class TestCase(BaseModel):
    id: str            = Field(description="e.g. TC-001")
    title: str
    type: str          = Field(description="Functional | Negative | Edge | Security")
    priority: str      = Field(description="P0 | P1 | P2")
    preconditions: str
    steps: List[str]
    expected: str


class TestPlan(BaseModel):
    feature: str
    scope: str         = Field(description="What is and isn't covered")
    risks: List[str]
    test_cases: List[TestCase]


# -------------------- tools --------------------

def _adf_to_text(node) -> str:
    """Flatten Atlassian Document Format (JIRA API v3 description) into text."""
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
        if node.get("type") in {"paragraph", "heading", "listItem", "blockquote", "codeBlock"}:
            text += "\n"
        return text
    return ""


@tool
def fetch_jira_story(ticket_key: str) -> str:
    """Fetch a JIRA story / requirement by its key (e.g. 'VWO-123') and return it
    as a plain-text requirement (summary + description) to design tests from."""
    base = (os.getenv("JIRA_URL") or "").rstrip("/")
    email, token = os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN")
    if not (base and email and token):
        return "ERROR: set JIRA_URL, JIRA_EMAIL and JIRA_API_TOKEN in .env"
    url = f"{base}/rest/api/3/issue/{ticket_key.strip()}"
    try:
        r = requests.get(
            url, auth=(email, token), headers={"Accept": "application/json"},
            params={"fields": "summary,description,issuetype,priority,components,labels"},
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
    components = ", ".join(c.get("name", "") for c in (f.get("components") or [])) or "—"
    return (
        f"[{ticket_key}] {summary}\n"
        f"Type: {issuetype} | Components: {components}\n\n"
        f"Description:\n{desc}"
    )


@tool
def qa_copilot_search(query: str, k: int = 5) -> str:
    """Search the QA Copilot RAG (existing VWO test cases / bug precedent) for the
    top-k items most similar to the query. Use this BEFORE designing tests so the
    plan reuses existing conventions and avoids duplicating known cases."""
    try:
        results = retrieve(query, k=k)
    except Exception as e:
        return f"ERROR searching QA Copilot RAG: {e} (is the KB built + Ollama running?)"
    return format_context(results)


# -------------------- designer chain --------------------

llm = ChatGroq(model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"), temperature=0)
designer = llm.with_structured_output(TestPlan)

prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a test design expert. Turn a requirement into a crisp plan and "
     "concrete, runnable cases. Cover happy path, negative, edge and security. "
     "Reuse the conventions (ids, style, teams) shown in the PRIOR TEST CASES and "
     "avoid duplicating cases that already exist there. No fluff."),
    ("human",
     "Requirement / user story:\n\n{story}\n\n"
     "PRIOR TEST CASES from the QA Copilot knowledge base:\n\n{prior}"),
])

chain = prompt | designer


def design_from_jira(ticket_key: str) -> TestPlan:
    """Fetch the story, pull RAG context, design the plan."""
    story = fetch_jira_story.invoke({"ticket_key": ticket_key})
    if story.startswith("ERROR"):
        raise RuntimeError(story)
    prior = qa_copilot_search.invoke({"query": story, "k": 5})
    return chain.invoke({"story": story, "prior": prior})


def _print_plan(plan: TestPlan) -> None:
    print(f"\nFeature: {plan.feature}  ({len(plan.test_cases)} cases)")
    print(f"Scope  : {plan.scope}")
    print("Risks  :")
    for r in plan.risks:
        print(f"  - {r}")
    print("\nTest cases:")
    for tc in plan.test_cases:
        print(f"\n[{tc.priority}] {tc.id} — {tc.title}  ({tc.type})")
        print(f"  Preconditions: {tc.preconditions}")
        print("  Steps:")
        for i, s in enumerate(tc.steps, 1):
            print(f"    {i}. {s}")
        print(f"  Expected: {tc.expected}")


if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else input("Enter JIRA story key (project VWO), e.g. VWO-123: ").strip()
    print(f"Fetching {key} + RAG context, designing plan ...")
    _print_plan(design_from_jira(key))
