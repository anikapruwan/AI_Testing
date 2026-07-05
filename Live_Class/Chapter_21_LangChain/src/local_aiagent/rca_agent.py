from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_agent

import os
load_dotenv()
import requests



# Tools = the agent's senses. Real versions hit Jira / Git / logs / CI.
@tool
def fetch_test_logs(test_name: str) -> str:
    # http://localhost:8080/job/AdvancePlaywrightFramework1x/5/consoleText
    """Return the failure log / stack trace for a failing test."""
    return ("AssertionError: expected status 200 but got 503\n"
            "  at checkout.spec.ts:42\n"
            "  POST /api/v2/payment -> 503 Service Unavailable")

@tool
def recent_commits(area: str) -> str:
    # https://github.com/PramodDutta/AITesterBlueprint2x/commits/main/
    """Return recent commits that touched a given area/module."""
    return ("- a1b2c3 'switch payment gateway to v2 endpoint' (2h ago)\n"
            "- d4e5f6 'cut payment client timeout 3s -> 1s' (3h ago)")

@tool
def service_health(service: str) -> str:
    #  https://restful-booker.herokuapp.com/ping
    """Return current health / error rate for a backend service."""
    return "payment-svc: error rate 18%, p99 latency 9.4s (degraded)"


llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
tools = [fetch_test_logs, recent_commits, service_health]

# langchain v1: create_agent replaces create_tool_calling_agent + AgentExecutor.
# The tool-calling loop + scratchpad are handled internally.
agent = create_agent(
    llm,
    tools,
    system_prompt=("You are a root-cause analysis agent. Gather evidence "
                   "with tools BEFORE concluding. Then give: the single most "
                   "likely root cause, the evidence for it, and one fix."),
)

if __name__ == "__main__":
    result = agent.invoke({"messages": [{"role": "user", "content":
        "The test 'checkout payment flow' just started failing. Find the root cause."
    }]})

    # show the tool calls the agent made, then its final answer
    for m in result["messages"]:
        calls = getattr(m, "tool_calls", None)
        if calls:
            for c in calls:
                print(f"[tool] {c['name']}({c['args']})")
        elif m.type == "tool":
            print(f"[result] {m.content}")

    print("\n" + "=" * 70)
    print(result["messages"][-1].content)