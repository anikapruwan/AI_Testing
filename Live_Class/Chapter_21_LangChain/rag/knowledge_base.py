"""Local Chroma knowledge base for bug triage.

Embeddings: Ollama `nomic-embed-text` (local, free). Persisted to rag/chroma_db.
"""
import csv
import os
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

from .jira_source import fetch_project_issues

ROOT = Path(__file__).resolve().parent.parent      # Chapter_21_LangChain/
DATA = ROOT / "data"
DB_DIR = ROOT / "rag" / "chroma_db"
COLLECTION = "vwo_knowledge"

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

load_dotenv(ROOT / ".env")


def _embedder():
    return embedding_functions.OllamaEmbeddingFunction(
        url=OLLAMA_URL, model_name=EMBED_MODEL
    )


def get_collection():
    client = chromadb.PersistentClient(path=str(DB_DIR))
    return client.get_or_create_collection(
        COLLECTION, embedding_function=_embedder(),
        metadata={"hnsw:space": "cosine"},
    )


# -------------------- ingest --------------------

def _load_test_cases() -> tuple[list, list, list]:
    ids, docs, metas = [], [], []
    csv_path = DATA / "test_cases.csv"
    if not csv_path.exists():
        return ids, docs, metas
    with csv_path.open() as fh:
        for row in csv.DictReader(fh):
            ids.append(f"TC-{row['id']}")
            docs.append(
                f"Test case {row['id']} [{row['area']}]: {row['title']}\n"
                f"Steps: {row['steps']}\nExpected: {row['expected']}\n"
                f"Severity: {row['severity']} | Priority: {row['priority']} | Team: {row['team']}"
            )
            metas.append({"type": "test_case", "source": "test_cases.csv",
                          "component": row["component"], "severity": row["severity"],
                          "priority": row["priority"], "team": row["team"]})
    return ids, docs, metas


def _load_bug_reports() -> tuple[list, list, list]:
    ids, docs, metas = [], [], []
    for md in sorted((DATA / "bug_reports").glob("*.md")) if (DATA / "bug_reports").exists() else []:
        text = md.read_text()
        ids.append(f"BUG-{md.stem}")
        docs.append(text)
        metas.append({"type": "bug_report", "source": md.name})
    return ids, docs, metas


def _load_pdfs() -> tuple[list, list, list]:
    ids, docs, metas = [], [], []
    pdfs = list(DATA.glob("*.pdf"))
    if not pdfs:
        return ids, docs, metas
    try:
        from pypdf import PdfReader
    except ImportError:
        print("  ! pypdf not installed, skipping PDFs")
        return ids, docs, metas
    for pdf in pdfs:
        try:
            reader = PdfReader(str(pdf))
        except Exception as e:
            print(f"  ! could not read {pdf.name}: {e}")
            continue
        for pno, page in enumerate(reader.pages, 1):
            text = (page.extract_text() or "").strip()
            if not text:
                continue
            ids.append(f"PDF-{pdf.stem}-p{pno}")
            docs.append(f"[{pdf.name} p.{pno}]\n{text}")
            metas.append({"type": "pdf", "source": pdf.name, "page": pno})
    return ids, docs, metas


def _load_jira(project: str) -> tuple[list, list, list]:
    ids, docs, metas = [], [], []
    try:
        issues = fetch_project_issues(project)
    except Exception as e:
        print(f"  ! JIRA fetch skipped: {e}")
        return ids, docs, metas
    for it in issues:
        f = it["fields"]
        ids.append(f"JIRA-{it['key']}")
        docs.append(it["report"])
        metas.append({
            "type": "jira", "source": "jira", "key": it["key"],
            "priority": (f.get("priority") or {}).get("name", "?"),
            "status": (f.get("status") or {}).get("name", "?"),
            "component": ", ".join(c.get("name", "") for c in (f.get("components") or [])) or "—",
        })
    return ids, docs, metas


def _add_batched(col, ids, docs, metas, batch=64):
    for i in range(0, len(ids), batch):
        col.add(ids=ids[i:i + batch], documents=docs[i:i + batch],
                metadatas=metas[i:i + batch])


def ingest(project: str = "VWO", reset: bool = True) -> dict:
    """(Re)build the knowledge base. Returns counts per source."""
    client = chromadb.PersistentClient(path=str(DB_DIR))
    if reset:
        try:
            client.delete_collection(COLLECTION)
        except Exception:
            pass
    col = client.get_or_create_collection(
        COLLECTION, embedding_function=_embedder(),
        metadata={"hnsw:space": "cosine"})

    stats = {}
    for name, loader in [
        ("test_cases", _load_test_cases),
        ("bug_reports", _load_bug_reports),
        ("pdfs", _load_pdfs),
        ("jira", lambda: _load_jira(project)),
    ]:
        ids, docs, metas = loader()
        if ids:
            print(f"  embedding {len(ids)} {name} ...")
            _add_batched(col, ids, docs, metas)
        stats[name] = len(ids)
    stats["total"] = col.count()
    return stats


# -------------------- retrieve --------------------

def retrieve(query: str, k: int = 3, exclude_ids: list[str] | None = None) -> list[dict]:
    """Top-k most-similar knowledge items. Returns
    [{id, document, metadata, distance}] sorted best-first.
    `exclude_ids` drops self-matches (e.g. the ticket being triaged)."""
    col = get_collection()
    n = col.count()
    if n == 0:
        return []
    exclude = set(exclude_ids or [])
    fetch = min(n, k + len(exclude) + 3)        # over-fetch, filter, slice
    res = col.query(query_texts=[query], n_results=fetch)
    out = []
    for i in range(len(res["ids"][0])):
        _id = res["ids"][0][i]
        if _id in exclude:
            continue
        out.append({
            "id": _id,
            "document": res["documents"][0][i],
            "metadata": res["metadatas"][0][i],
            "distance": res["distances"][0][i],
        })
        if len(out) >= k:
            break
    return out


def format_context(results: list[dict]) -> str:
    """Render retrieved items as a prompt-ready 'prior knowledge' block."""
    if not results:
        return "(no prior knowledge found)"
    blocks = []
    for i, r in enumerate(results, 1):
        m = r["metadata"]
        tag = m.get("type", "?")
        extra = ""
        if tag in ("test_case", "jira", "bug_report"):
            bits = [m.get(x) for x in ("component", "severity", "priority", "team") if m.get(x)]
            if bits:
                extra = "  [" + " | ".join(bits) + "]"
        blocks.append(
            f"--- #{i} ({tag}, id={r['id']}, score={1 - r['distance']:.2f}){extra} ---\n"
            f"{r['document'].strip()[:800]}"
        )
    return "\n\n".join(blocks)
