"""QA Copilot — Streamlit UI over the three PRODUCTION agents.

Enter details, pick a task (or let it auto-route), and the copilot uses the
prod bug-triage / RCA / test-designer agent — with graceful fallback to dummy
data when JIRA / Jenkins / the RAG KB are not reachable.

Run:
    cd Chapter_21_LangChain
    .venv/bin/streamlit run src/QACopilot_Final/qa_copilot_ui.py
"""
import os
import sys
from pathlib import Path

import streamlit as st

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

st.set_page_config(page_title="QA Copilot", page_icon="🤖", layout="wide")

# ---- sidebar: config -> environment (prod agents read os.getenv) ----
with st.sidebar:
    st.header("⚙️ Configuration")
    st.caption("Blank fields fall back to .env / dummy data.")

    st.subheader("Model (Groq)")
    groq_key = st.text_input("GROQ_API_KEY", value="", type="password")
    llm_model = st.text_input("LLM_MODEL", value=os.getenv("LLM_MODEL", "openai/gpt-oss-120b"),
                              help="triage needs a json_schema-capable model, e.g. openai/gpt-oss-120b")

    st.subheader("JIRA (triage + design)")
    jira_url = st.text_input("JIRA_URL", value=os.getenv("JIRA_URL", ""))
    jira_email = st.text_input("JIRA_EMAIL", value=os.getenv("JIRA_EMAIL", ""))
    jira_token = st.text_input("JIRA_API_TOKEN", value="", type="password")

    st.subheader("RCA sources")
    jenkins_url = st.text_input("JENKINS_URL", value=os.getenv("JENKINS_URL", "http://localhost:8080"))
    jenkins_job = st.text_input("JENKINS_JOB", value=os.getenv("JENKINS_JOB", "AdvancePlaywrightFramework1x"))
    jenkins_user = st.text_input("JENKINS_USER", value=os.getenv("JENKINS_USER", "admin"))
    jenkins_token = st.text_input("JENKINS_TOKEN", value="", type="password")
    github_repo = st.text_input("GITHUB_REPO", value=os.getenv("GITHUB_REPO", "PramodDutta/AdvancePlaywrightFramework1x"))
    health_url = st.text_input("HEALTH_URL", value=os.getenv("HEALTH_URL", "https://app.thetestingacademy.com/playwright/ttacart/"))


def _apply_env():
    pairs = {
        "LLM_MODEL": llm_model, "JIRA_URL": jira_url, "JIRA_EMAIL": jira_email,
        "JENKINS_URL": jenkins_url, "JENKINS_JOB": jenkins_job, "JENKINS_USER": jenkins_user,
        "GITHUB_REPO": github_repo, "HEALTH_URL": health_url,
    }
    for k, v in pairs.items():
        if v.strip():
            os.environ[k] = v.strip()
    for k, v in {"GROQ_API_KEY": groq_key, "JIRA_API_TOKEN": jira_token, "JENKINS_TOKEN": jenkins_token}.items():
        if v.strip():
            os.environ[k] = v.strip()


st.title("🤖 QA Copilot")
st.caption("One front door → bug triage · root-cause analysis · test design (production agents, dummy fallback)")

mode = st.radio("Task", ["Auto-route", "Bug Triage", "Root-Cause Analysis", "Test Design"], horizontal=True)

col1, col2 = st.columns([2, 1])
with col1:
    if mode == "Root-Cause Analysis":
        text = st.text_area("Question", height=110,
                            value="Is the automation working fine, and do we have any error in the login?")
        jira_key = ""
    elif mode == "Auto-route":
        text = st.text_area("Your request", height=110,
                            value="The login smoke test just started failing — why?")
        jira_key = st.text_input("JIRA key (optional, for triage/design)", value="")
    else:
        jira_key = st.text_input("JIRA key (optional — leave blank to use the text below)",
                                 value="VWO-105" if mode == "Test Design" else "")
        text = st.text_area("Or paste a bug report / user story", height=110, value="")

with col2:
    st.info("Fallback order:\n\n1. JIRA / Jenkins / RAG (real)\n2. pasted text\n3. built-in dummy sample")

run = st.button("Run", type="primary")

if run:
    _apply_env()
    import copilot_core as core  # imported after env is set

    with st.spinner("Working…"):
        if mode == "Bug Triage":
            res = core.run_triage(jira_key=jira_key, report_text=text)
        elif mode == "Root-Cause Analysis":
            res = core.run_rca(question=text)
        elif mode == "Test Design":
            res = core.run_design(jira_key=jira_key, story_text=text)
        else:
            res = core.handle(text, jira_key=jira_key)

    if not res.get("ok"):
        st.error(res.get("error", "failed"))
        st.stop()

    st.success(f"**{res['mode']}** · source: {res.get('source','')}")

    if res["mode"] == "TRIAGE":
        t = res["triage"]
        st.subheader(t.title)
        c = st.columns(4)
        c[0].metric("Severity", t.severity)
        c[1].metric("Priority", t.priority)
        c[2].metric("Component", t.component)
        c[3].metric("Duplicate?", str(t.likely_duplicate))
        st.write(f"**Owner:** {t.suggested_team}")
        st.write(f"**Why:** {t.reasoning}")
        if res.get("context"):
            with st.expander("RAG prior knowledge"):
                st.code(res["context"])

    elif res["mode"] == "DESIGN":
        plan = res["plan"]
        st.subheader(f"{plan.feature}  ({len(plan.test_cases)} cases)")
        st.write(f"**Scope:** {plan.scope}")
        st.write("**Risks:** " + ", ".join(plan.risks))
        for tc in plan.test_cases:
            with st.expander(f"[{tc.priority}] {tc.id} — {tc.title}  ({tc.type})"):
                st.write(f"**Preconditions:** {tc.preconditions}")
                st.write("**Steps:**")
                for i, s in enumerate(tc.steps, 1):
                    st.write(f"{i}. {s}")
                st.write(f"**Expected:** {tc.expected}")

    elif res["mode"] == "RCA":
        with st.expander("Evidence gathered", expanded=True):
            for s in res["steps"]:
                st.markdown(s)
        st.subheader("Root-Cause Analysis")
        st.markdown(res["answer"])
