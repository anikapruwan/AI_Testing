"""QA Copilot core — orchestrates the THREE PRODUCTION agents with graceful
fallback, so it keeps working even when local resources (JIRA, Jenkins, the RAG
KB / Ollama) are unavailable in a shipped environment.

  TRIAGE  -> prod/bug_traige_agent_prod_ready   (JIRA + RAG; falls back to plain
                                                 triage on pasted text)
  DESIGN  -> prod/test_designer_agent_prod      (JIRA + RAG; falls back to a
                                                 pasted story with no prior)
  RCA     -> prod/rca_agent_prod_...            (Jenkins/GitHub/health; the
                                                 Jenkins tool self-falls-back to
                                                 a sample log)

Both the CLI router (`qa_copilot.py`) and the Streamlit UI (`qa_copilot_ui.py`)
use this module — one place, no duplicated logic.
"""
import sys
from pathlib import Path

from dotenv import load_dotenv

# --- make the prod agents + the rag package importable, wherever we run from ---
HERE = Path(__file__).resolve().parent          # src/QACopilot_Final
SRC = HERE.parent                               # src
CH_ROOT = SRC.parent                            # Chapter_21_LangChain
for p in (str(CH_ROOT), str(SRC), str(SRC / "prod")):
    if p not in sys.path:
        sys.path.insert(0, p)

load_dotenv(CH_ROOT / ".env")

import bug_traige_agent_prod_ready as triage_prod          # noqa: E402
import test_designer_agent_prod as design_prod             # noqa: E402
import rca_agent_prod_jenkins_github_apitestping as rca_prod  # noqa: E402

# fallback samples used when nothing real is reachable
_DUMMY_BUG = ("App freezes when uploading a 0-byte file on iOS after the 4.2.0 "
              "release; the spinner never stops and the user is stuck.")
_DUMMY_STORY = ("As a user, I can reset my password via a 'Forgot password' link. "
                "A reset email is sent if the account exists; the link expires in "
                "30 minutes; the new password must meet the strength policy.")


# -------------------- TRIAGE --------------------

def run_triage(jira_key: str = "", report_text: str = "") -> dict:
    """Prod path: fetch JIRA + RAG-grounded triage. Fallback: plain triage on the
    pasted report text (or a dummy) with no JIRA/RAG."""
    if jira_key.strip():
        try:
            res = triage_prod.triage_ticket(jira_key.strip())
            if not res.get("error"):
                return {"ok": True, "mode": "TRIAGE", "source": "prod · JIRA + RAG", **res}
            reason = res["error"]
        except Exception as e:
            reason = f"{type(e).__name__}: {e}"
    else:
        reason = "no JIRA key given"

    text = report_text.strip() or _DUMMY_BUG
    try:
        chain = triage_prod.build_chain()
        triage = chain.invoke({"report": text, "context": "(no prior knowledge — fallback)"})
        return {"ok": True, "mode": "TRIAGE",
                "source": f"fallback · pasted text ({reason})",
                "report": text, "triage": triage}
    except Exception as e:
        return {"ok": False, "mode": "TRIAGE", "error": f"triage failed: {e}"}


# -------------------- DESIGN --------------------

def run_design(jira_key: str = "", story_text: str = "") -> dict:
    """Prod path: JIRA story + RAG context -> TestPlan. Fallback: pasted story
    (or dummy) with RAG best-effort, no JIRA."""
    if jira_key.strip():
        try:
            plan = design_prod.design_from_jira(jira_key.strip())
            return {"ok": True, "mode": "DESIGN", "source": "prod · JIRA + RAG", "plan": plan}
        except Exception as e:
            reason = f"{type(e).__name__}: {e}"
    else:
        reason = "no JIRA key given"

    story = story_text.strip() or _DUMMY_STORY
    try:
        try:
            prior = design_prod.qa_copilot_search.invoke({"query": story, "k": 5})
        except Exception:
            prior = "(no prior knowledge — RAG unavailable)"
        plan = design_prod.chain.invoke({"story": story, "prior": prior})
        return {"ok": True, "mode": "DESIGN",
                "source": f"fallback · pasted story ({reason})", "plan": plan}
    except Exception as e:
        return {"ok": False, "mode": "DESIGN", "error": f"design failed: {e}"}


# -------------------- RCA --------------------

def run_rca(question: str = "") -> dict:
    """Prod RCA agent — Jenkins log + GitHub commits + live health ping. The
    Jenkins tool self-falls-back to a sample log when unreachable."""
    q = question.strip() or "Is the automation healthy and is there any error in the login?"
    try:
        result = rca_prod.agent.invoke({"messages": [{"role": "user", "content": q}]})
    except Exception as e:
        return {"ok": False, "mode": "RCA", "error": f"RCA failed: {e}"}
    steps = []
    for m in result["messages"]:
        calls = getattr(m, "tool_calls", None)
        if calls:
            steps += [f"🔧 {c['name']}({c['args']})" for c in calls]
        elif getattr(m, "type", "") == "tool":
            body = m.content if len(m.content) < 500 else m.content[:500] + " …"
            steps.append(f"↳ {body}")
    return {"ok": True, "mode": "RCA", "source": "prod · Jenkins/GitHub/health (dummy fallback)",
            "steps": steps, "answer": result["messages"][-1].content}


# -------------------- router --------------------

def route(request: str) -> str:
    """Classify a free-text request into TRIAGE / RCA / DESIGN via a small LLM."""
    from langchain_groq import ChatGroq
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    import os

    llm = ChatGroq(model=os.getenv("ROUTER_MODEL", "llama-3.3-70b-versatile"), temperature=0)
    tmpl = ChatPromptTemplate.from_messages([
        ("system", "Classify the request into exactly one label: TRIAGE, RCA, or DESIGN. "
                   "TRIAGE = a bug to prioritise. DESIGN = write test cases for a feature/story. "
                   "RCA = a test/build/system is failing, find why. Reply with the label only."),
        ("human", "{input}"),
    ])
    label = (tmpl | llm | StrOutputParser()).invoke({"input": request}).strip().upper()
    for tag in ("TRIAGE", "DESIGN", "RCA"):
        if tag in label:
            return tag
    return "TRIAGE"


def handle(request: str, jira_key: str = "") -> dict:
    """Auto-route a free-text request to the right prod agent."""
    label = route(request)
    if label == "TRIAGE":
        return run_triage(jira_key=jira_key, report_text=request)
    if label == "DESIGN":
        return run_design(jira_key=jira_key, story_text=request)
    return run_rca(question=request)
