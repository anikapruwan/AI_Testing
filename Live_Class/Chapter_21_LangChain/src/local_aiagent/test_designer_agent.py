from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_agent
from typing import List

import os
load_dotenv()
import requests

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


llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
designer = llm.with_structured_output(TestPlan)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a test design expert. Turn a requirement into a "
               "crisp plan and concrete, runnable cases. Cover happy path, "
               "negative, edge and security. No fluff."),
    ("human", "Requirement / user story:\n\n{story}"),
])

chain = prompt | designer


if __name__ == "__main__":
    plan = chain.invoke({"story": """
As a user, I can reset my password via a 'Forgot password' link.
A reset email is sent if the account exists; the link expires in
30 minutes; the new password must meet the strength policy.
"""})

    print(f"Feature: {plan.feature}  ({len(plan.test_cases)} cases)")
    for tc in plan.test_cases:
        print(f"  [{tc.priority}] {tc.id}  {tc.title}  ({tc.type})")

