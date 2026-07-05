"""Streamlit UI for the bug-triage agent.

Run:
    cd Chapter_21_LangChain
    .venv/bin/streamlit run src/app.py

Settings (sidebar) -> writes Jira + Groq creds into .env AND the live process env,
then triages each JIRA key you enter and streams the result cards.
"""
import os
from pathlib import Path

import streamlit as st
from dotenv import dotenv_values, load_dotenv

import Chapter_21_LangChain.src.prod.bug_traige_agent_prod_ready as agent  # RAG-grounded triage
from rag import ingest as rag_ingest, get_collection

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

# fields shown in the settings sidebar -> .env key + label + secret?
SETTINGS = [
    ("JIRA_EMAIL",    "Jira email ID",      False),
    ("JIRA_API_TOKEN", "Jira API token",    True),
    ("JIRA_URL",      "Jira URL",           False),
    ("GROQ_API_KEY",  "Groq (GROQ) token",  True),
    ("LLM_MODEL",     "Groq model",         False),
]

load_dotenv(ENV_PATH)


def update_env(values: dict) -> None:
    """Merge values into .env (preserving other keys) and into os.environ so the
    agent — which reads os.getenv() at call time — sees them immediately."""
    current = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}
    for k, v in values.items():
        if v:
            current[k] = v
            os.environ[k] = v
    lines = [f"{k}={v}" for k, v in current.items() if v is not None]
    ENV_PATH.write_text("\n".join(lines) + "\n")


# -------------------- page --------------------

st.set_page_config(page_title="Bug Triage Agent", page_icon="🐞", layout="wide")
st.title("🐞 Bug Triage Agent")
st.caption("Fetch JIRA tickets → LLM triages severity, priority, owner. Powered by LangChain + Groq.")

# -------------------- settings sidebar --------------------

with st.sidebar:
    st.header("⚙️ Settings")
    st.write("Saved to `.env`. Tokens stored locally only.")
    inputs = {}
    for key, label, secret in SETTINGS:
        inputs[key] = st.text_input(
            label,
            value=os.getenv(key, ""),
            type="password" if secret else "default",
            placeholder="https://your-org.atlassian.net" if key == "JIRA_URL"
            else "openai/gpt-oss-120b" if key == "LLM_MODEL" else "",
        )
    if st.button("💾 Save settings", use_container_width=True):
        update_env(inputs)
        st.success("Saved to .env")

    st.divider()
    missing = [lbl for k, lbl, _ in SETTINGS if not os.getenv(k)]
    if missing:
        st.warning("Missing: " + ", ".join(missing))
    else:
        st.success("All settings present ✅")

    st.divider()
    st.header("📚 Knowledge base (RAG)")
    try:
        kb_count = get_collection().count()
    except Exception as e:
        kb_count = None
        st.error(f"RAG unavailable: {e}")
    if kb_count is not None:
        st.metric("Indexed items", kb_count)
        st.caption("test cases + bug reports + PDFs + VWO Jira tickets · "
                   "embeddings: Ollama nomic-embed-text (local)")
    if st.button("🔄 Rebuild knowledge base", use_container_width=True):
        with st.spinner("Ingesting data + fetching VWO tickets + embedding…"):
            try:
                stats = rag_ingest(project="VWO", reset=True)
                st.success("Indexed: " + ", ".join(f"{k}={v}" for k, v in stats.items()))
            except Exception as e:
                st.error(f"Ingest failed: {e}")

# -------------------- triage input --------------------

st.subheader("Tickets to triage")
raw = st.text_input(
    "JIRA ticket key(s), comma-separated",
    placeholder="VWO-29, VWO-30, VWO-31",
)
run = st.button("🚀 Run triage", type="primary")

SEV_COLOR = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}


def render_card(res: dict) -> None:
    key = res["key"]
    if res.get("error"):
        with st.container(border=True):
            st.markdown(f"### ❌ {key}")
            st.error(res["error"])
        return
    t = res["triage"]
    with st.container(border=True):
        st.markdown(f"### {SEV_COLOR.get(t.severity, '⚪')} {key} — {t.title}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Severity", t.severity)
        c2.metric("Priority", t.priority)
        c3.metric("Component", t.component)
        c4.metric("Owner", t.suggested_team)
        st.markdown(f"**Likely duplicate:** {'Yes' if t.likely_duplicate else 'No'}")
        st.markdown(f"**Reasoning:** {t.reasoning}")

        rag = res.get("rag") or []
        if rag:
            chips = " · ".join(
                f"`{r['id']}` ({1 - r['distance']:.2f})" for r in rag
            )
            st.markdown(f"**🔎 Grounded on top-{len(rag)} RAG matches:** {chips}")
            with st.expander("RAG context used for this decision"):
                st.code(res.get("context", ""), language="text")
        with st.expander("Raw JIRA report"):
            st.code(res["report"], language="text")


if run:
    keys = [k.strip() for k in raw.replace(",", " ").split() if k.strip()]
    if not keys:
        st.warning("Enter at least one ticket key.")
    elif (m := [lbl for k, lbl, _ in SETTINGS if not os.getenv(k)]):
        st.error("Fill settings first — missing: " + ", ".join(m))
    else:
        try:
            chain = agent.build_chain()
        except Exception as e:
            st.error(f"Could not init Groq model: {e}")
            chain = None
        if chain is not None:
            st.write(f"Triaging **{len(keys)}** ticket(s)…")
            progress = st.progress(0.0)
            for i, key in enumerate(keys, 1):
                with st.spinner(f"Triaging {key}…"):
                    try:
                        res = agent.triage_ticket(key, chain)
                    except Exception as e:
                        res = {"key": key, "report": "", "error": f"ERROR: {e}"}
                render_card(res)          # streams in as each finishes
                progress.progress(i / len(keys))
            st.success("Done ✅")
