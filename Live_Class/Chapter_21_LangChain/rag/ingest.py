"""(Re)build the RAG knowledge base.

Run from the chapter root:
    .venv/bin/python -m rag.ingest          # ingest data + VWO jira
    .venv/bin/python -m rag.ingest PROJKEY  # different project
"""
import sys

from .knowledge_base import ingest

if __name__ == "__main__":
    project = sys.argv[1] if len(sys.argv) > 1 else "VWO"
    print(f"Ingesting knowledge base (project={project}) ...")
    stats = ingest(project=project, reset=True)
    print("\nDone. Indexed:")
    for k, v in stats.items():
        print(f"  {k:12} {v}")
