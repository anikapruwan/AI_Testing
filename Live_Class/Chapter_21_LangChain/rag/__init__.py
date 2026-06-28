"""Lightweight local RAG for the VWO bug-triage agent.

Knowledge sources ingested into a local Chroma DB (embeddings = Ollama
nomic-embed-text, fully local / free):
  - data/test_cases.csv     100 test cases
  - data/bug_reports/*.md   past-triaged bugs (triage precedent)
  - data/*.pdf              any PDFs you drop in
  - JIRA project VWO        all tickets fetched live via JQL

Public API:
  from rag import retrieve, format_context, ingest
"""
from .knowledge_base import retrieve, format_context, ingest, get_collection

__all__ = ["retrieve", "format_context", "ingest", "get_collection"]
