import pandas as pd
from PyPDF2 import PdfReader
import os
import tempfile
import shutil
from typing import List, Dict, Any, Tuple
from pathlib import Path
from github import Github
import base64


class CSVLoader:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> pd.DataFrame:
        return pd.read_csv(self.file_path)

    def chunk_by_row(self) -> List[Dict[str, Any]]:
        df = self.load()
        chunks = []

        for idx, row in df.iterrows():
            chunk_text = self._row_to_text(row)
            chunks.append({
                "id": f"tc_{row.get('id', idx)}",
                "content": chunk_text,
                "metadata": {
                    "source": "test_cases",
                    "jira_id": row.get("jira_id", ""),
                    "module": row.get("module", ""),
                    "priority": row.get("priority", ""),
                    "severity": row.get("severity", ""),
                    "labels": row.get("labels", ""),
                    "test_type": row.get("test_type", ""),
                    "row_index": idx
                }
            })

        return chunks

    def _row_to_text(self, row: pd.Series) -> str:
        parts = []
        for col in ["summary", "preconditions", "steps", "expected_result"]:
            if pd.notna(row.get(col)):
                parts.append(f"{col}: {row[col]}")

        return " | ".join(parts)


class PDFLoader:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> List[Dict[str, Any]]:
        reader = PdfReader(self.file_path)
        pages = []

        for idx, page in enumerate(reader.pages):
            text = page.extract_text()
            pages.append({
                "page_number": idx + 1,
                "content": text
            })

        return pages

    def chunk_by_page(self) -> List[Dict[str, Any]]:
        pages = self.load()
        chunks = []

        for page in pages:
            chunks.append({
                "id": f"pdf_page_{page['page_number']}",
                "content": page["content"],
                "metadata": {
                    "source": "pdf_docs",
                    "page_number": page["page_number"]
                }
            })

        return chunks

    def chunk_by_paragraph(self, chunk_size: int = 1000) -> List[Dict[str, Any]]:
        pages = self.load()
        chunks = []
        chunk_id = 0

        for page in pages:
            text = page["content"]
            paragraphs = text.split("\n\n")

            current_chunk = ""
            for para in paragraphs:
                if len(current_chunk) + len(para) < chunk_size:
                    current_chunk += para + "\n\n"
                else:
                    if current_chunk:
                        chunks.append({
                            "id": f"pdf_chunk_{chunk_id}",
                            "content": current_chunk.strip(),
                            "metadata": {
                                "source": "pdf_docs",
                                "page_number": page["page_number"]
                            }
                        })
                        chunk_id += 1
                    current_chunk = para + "\n\n"

            if current_chunk:
                chunks.append({
                    "id": f"pdf_chunk_{chunk_id}",
                    "content": current_chunk.strip(),
                    "metadata": {
                        "source": "pdf_docs",
                        "page_number": page["page_number"]
                    }
                })
                chunk_id += 1

        return chunks


class GitHubLoader:
    def __init__(self, repo_url: str, token: str = None):
        self.repo_url = repo_url
        self.token = token

    def get_repo_info(self) -> Dict[str, str]:
        parts = self.repo_url.rstrip("/").split("/")
        owner = parts[-2]
        repo_name = parts[-1].replace(".git", "")

        return {
            "owner": owner,
            "repo_name": repo_name
        }

    def load_source_code(self, branch: str = "main") -> List[Dict[str, Any]]:
        repo_info = self.get_repo_info()

        if self.token:
            g = Github(self.token)
        else:
            g = Github()

        repo = g.get_repo(f"{repo_info['owner']}/{repo_info['repo_name']}")

        files = []
        contents = repo.get_contents("", ref=branch)

        while contents:
            file_content = contents.pop(0)

            if file_content.type == "dir":
                contents.extend(repo.get_contents(file_content.path, ref=branch))
            else:
                if self._is_code_file(file_content.name):
                    try:
                        decoded_content = base64.b64decode(file_content.content).decode("utf-8")
                        files.append({
                            "path": file_content.path,
                            "name": file_content.name,
                            "content": decoded_content,
                            "size": file_content.size
                        })
                    except Exception as e:
                        print(f"Error reading {file_content.path}: {e}")

        return files

    def chunk_files(self, files: List[Dict[str, Any]], chunk_size: int = 2000) -> List[Dict[str, Any]]:
        chunks = []

        for file in files:
            content = file["content"]
            file_name = file["name"]
            file_path = file["path"]

            if len(content) <= chunk_size:
                chunks.append({
                    "id": f"code_{file_path.replace('/', '_').replace('.', '_')}",
                    "content": content,
                    "metadata": {
                        "source": "code_base",
                        "file_name": file_name,
                        "file_path": file_path
                    }
                })
            else:
                lines = content.split("\n")
                current_chunk = ""
                chunk_id = 0

                for line in lines:
                    if len(current_chunk) + len(line) < chunk_size:
                        current_chunk += line + "\n"
                    else:
                        chunks.append({
                            "id": f"code_{file_path.replace('/', '_').replace('.', '_')}_chunk_{chunk_id}",
                            "content": current_chunk.strip(),
                            "metadata": {
                                "source": "code_base",
                                "file_name": file_name,
                                "file_path": file_path,
                                "chunk_index": chunk_id
                            }
                        })
                        chunk_id += 1
                        current_chunk = line + "\n"

                if current_chunk:
                    chunks.append({
                        "id": f"code_{file_path.replace('/', '_').replace('.', '_')}_chunk_{chunk_id}",
                        "content": current_chunk.strip(),
                        "metadata": {
                            "source": "code_base",
                            "file_name": file_name,
                            "file_path": file_path,
                            "chunk_index": chunk_id
                        }
                    })

        return chunks

    def _is_code_file(self, filename: str) -> bool:
        code_extensions = [".java", ".py", ".js", ".ts", ".xml", ".json", ".yaml", ".yml", ".properties", ".gradle", ".kt", ".swift"]
        return any(filename.endswith(ext) for ext in code_extensions)


def load_all_data_sources():
    from app.config import settings
    from app.services.embed_service import embed_service
    from app.services.chroma_client import chroma_client

    results = {
        "test_cases": 0,
        "pdf_docs": 0,
        "code_base": 0
    }

    # Load CSV test cases
    if os.path.exists(settings.csv_data_path):
        csv_loader = CSVLoader(settings.csv_data_path)
        chunks = csv_loader.chunk_by_row()

        if chunks:
            documents = [c["content"] for c in chunks]
            ids = [c["id"] for c in chunks]
            metadatas = [c["metadata"] for c in chunks]

            embeddings = embed_service.embed_batch(documents)

            chroma_client.add_documents(
                collection_name=settings.collection_test_cases,
                documents=documents,
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas
            )
            results["test_cases"] = len(chunks)

    # Load PDFs
    if os.path.exists(settings.pdf_data_path):
        pdf_loader = PDFLoader(settings.pdf_data_path)
        chunks = pdf_loader.chunk_by_paragraph()

        if chunks:
            documents = [c["content"] for c in chunks]
            ids = [c["id"] for c in chunks]
            metadatas = [c["metadata"] for c in chunks]

            embeddings = embed_service.embed_batch(documents)

            chroma_client.add_documents(
                collection_name=settings.collection_pdfs,
                documents=documents,
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas
            )
            results["pdf_docs"] = len(chunks)

    return results