"""Streamlit UI for the production RCA agent.

Enter your Jenkins job, GitHub repo, app URL and a question — the agent gathers
evidence from all three real sources and returns a root-cause analysis.

Run:
    cd Chapter_21_LangChain
    .venv/bin/streamlit run src/UI/rca_ui.py
"""
import importlib
import os
import sys
from pathlib import Path

import streamlit as st

# make the sibling agent module importable (it lives in ../  -> src/)
SRC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC))

AGENT_MODULE = "rca_agent_prod_jenkins_github_apitestping"


def _normalize_repo(value: str) -> str:
    """Accept a full GitHub URL or an owner/repo string, return 'owner/repo'."""
    v = value.strip()
    if "github.com" in v:
        v = v.split("github.com/", 1)[1]
    # strip trailing /commits/main, .git, trailing slash
    v = v.replace(".git", "").strip("/")
    parts = [p for p in v.split("/") if p]
    return "/".join(parts[:2]) if len(parts) >= 2 else v


st.set_page_config(page_title="RCA Agent", page_icon="🔎", layout="wide")
st.title("🔎 Root-Cause Analysis Agent")
st.caption("Jenkins log + GitHub commits + live health ping → grounded RCA")

with st.sidebar:
    st.header("Configuration")

    st.subheader("Jenkins")
    jenkins_url = st.text_input("Jenkins URL", value="http://localhost:8080")
    jenkins_job = st.text_input("Job name", value="AdvancePlaywrightFramework1x")
    jenkins_build = st.text_input("Build", value="lastBuild", help="Build number or 'lastBuild'")
    jenkins_user = st.text_input("Jenkins user", value="admin")
    jenkins_token = st.text_input("Jenkins token / password", value="admin", type="password")

    st.subheader("GitHub")
    github_repo = st.text_input(
        "Repo (URL or owner/repo)",
        value="https://github.com/PramodDutta/AdvancePlaywrightFramework1x/commits/main/",
    )
    github_token = st.text_input("GitHub token (optional)", value="", type="password")

    st.subheader("App under test")
    health_url = st.text_input(
        "Application URL", value="https://app.thetestingacademy.com/playwright/ttacart/"
    )

    st.subheader("Model")
    llm_model = st.text_input("Groq model", value="llama-3.3-70b-versatile")
    groq_key = st.text_input("GROQ_API_KEY (blank = use .env)", value="", type="password")

question = st.text_area(
    "Your question",
    value="Can you check the RCA — is the automation working fine, and do we have any error in the login?",
    height=90,
)

run = st.button("Run RCA", type="primary")

if run:
    # push the form values into the environment, then (re)load the agent module
    # so its tools pick up the new Jenkins / GitHub / health config.
    os.environ["JENKINS_URL"] = jenkins_url
    os.environ["JENKINS_JOB"] = jenkins_job
    os.environ["JENKINS_BUILD"] = jenkins_build
    os.environ["JENKINS_USER"] = jenkins_user
    os.environ["JENKINS_TOKEN"] = jenkins_token
    os.environ["GITHUB_REPO"] = _normalize_repo(github_repo)
    os.environ["HEALTH_URL"] = health_url
    os.environ["LLM_MODEL"] = llm_model
    if github_token.strip():
        os.environ["GITHUB_TOKEN"] = github_token.strip()
    if groq_key.strip():
        os.environ["GROQ_API_KEY"] = groq_key.strip()

    st.info(f"Repo → `{os.environ['GITHUB_REPO']}` | Jenkins → `{jenkins_job}/{jenkins_build}`")

    try:
        with st.spinner("Agent gathering evidence (Jenkins, GitHub, health)…"):
            if AGENT_MODULE in sys.modules:
                agent_mod = importlib.reload(sys.modules[AGENT_MODULE])
            else:
                agent_mod = importlib.import_module(AGENT_MODULE)
            result = agent_mod.agent.invoke(
                {"messages": [{"role": "user", "content": question}]}
            )
    except Exception as e:
        st.error(f"Run failed: {type(e).__name__}: {e}")
        st.stop()

    # evidence trail
    st.subheader("Evidence gathered")
    for m in result["messages"]:
        calls = getattr(m, "tool_calls", None)
        if calls:
            for c in calls:
                st.markdown(f"🔧 **{c['name']}**(`{c['args']}`)")
        elif getattr(m, "type", "") == "tool":
            with st.expander(f"↳ result: {m.name}", expanded=False):
                st.code(m.content)

    # final answer
    st.subheader("Root-Cause Analysis")
    st.markdown(result["messages"][-1].content)
