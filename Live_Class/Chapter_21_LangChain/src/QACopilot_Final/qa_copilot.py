"""QA Copilot (CLI) — one front door that auto-routes to the right PRODUCTION
agent. All logic lives in copilot_core (shared with the Streamlit UI).

Run:
    cd Chapter_21_LangChain
    .venv/bin/python src/QACopilot_Final/qa_copilot.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import copilot_core as core


def _render(res: dict) -> str:
    if not res.get("ok"):
        return f"[{res.get('mode','?')}] ERROR: {res.get('error')}"
    src = res.get("source", "")
    if res["mode"] == "TRIAGE":
        t = res["triage"]
        return (f"[TRIAGE · {src}] {t.title}\n"
                f"  {t.severity} / {t.priority} -> {t.component}\n"
                f"  Owner: {t.suggested_team} | dupe? {t.likely_duplicate}\n  {t.reasoning}")
    if res["mode"] == "DESIGN":
        plan = res["plan"]
        head = f"[DESIGN · {src}] {plan.feature} ({len(plan.test_cases)} cases)"
        cases = "\n".join(f"  [{tc.priority}] {tc.id} {tc.title} ({tc.type})" for tc in plan.test_cases)
        return f"{head}\n{cases}"
    if res["mode"] == "RCA":
        return f"[RCA · {src}]\n" + "\n".join(res["steps"]) + "\n\n" + res["answer"]
    return str(res)


if __name__ == "__main__":
    for req in [
        "Bug: app freezes when uploading a 0-byte file on iOS.",
        "Write test cases for the password reset flow.",
        "The login smoke test just started failing — why?",
    ]:
        print("\n" + "#" * 72)
        print("REQUEST:", req)
        print(_render(core.handle(req)))
