from fastapi import APIRouter, HTTPException
import os

from app.models.settings import IngestRequest, IngestResponse
from app.config import settings
from app.services.data_loader import CSVLoader, PDFLoader, GitHubLoader
from app.services.embed_service import embed_service
from app.services.chroma_client import chroma_client

router = APIRouter()


@router.post("/ingest/csv", response_model=IngestResponse)
async def ingest_csv(source_path: str = None):
    file_path = source_path or settings.csv_data_path

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"CSV file not found: {file_path}")

    try:
        loader = CSVLoader(file_path)
        chunks = loader.chunk_by_row()

        if not chunks:
            return IngestResponse(
                status="error",
                message="No data found in CSV",
                documents_ingested=0,
                chunks_created=0
            )

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

        return IngestResponse(
            status="success",
            message=f"Successfully ingested {len(chunks)} test cases",
            documents_ingested=len(chunks),
            chunks_created=len(chunks)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/pdf", response_model=IngestResponse)
async def ingest_pdf(source_path: str = None):
    file_path = source_path or settings.pdf_data_path

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"PDF file not found: {file_path}")

    try:
        loader = PDFLoader(file_path)
        chunks = loader.chunk_by_paragraph()

        if not chunks:
            return IngestResponse(
                status="error",
                message="No data found in PDF",
                documents_ingested=0,
                chunks_created=0
            )

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

        return IngestResponse(
            status="success",
            message=f"Successfully ingested PDF with {len(chunks)} chunks",
            documents_ingested=1,
            chunks_created=len(chunks)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/github", response_model=IngestResponse)
async def ingest_github(request: IngestRequest):
    repo_url = request.repo_url or settings.github_repo_url

    try:
        loader = GitHubLoader(repo_url, request.github_token)
        files = loader.load_source_code()

        if not files:
            return IngestResponse(
                status="error",
                message="No code files found in repository",
                documents_ingested=0,
                chunks_created=0
            )

        chunks = loader.chunk_files(files)

        if not chunks:
            return IngestResponse(
                status="error",
                message="No chunks created from files",
                documents_ingested=len(files),
                chunks_created=0
            )

        documents = [c["content"] for c in chunks]
        ids = [c["id"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        embeddings = embed_service.embed_batch(documents)

        chroma_client.add_documents(
            collection_name=settings.collection_github,
            documents=documents,
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas
        )

        return IngestResponse(
            status="success",
            message=f"Successfully ingested {len(files)} files with {len(chunks)} chunks",
            documents_ingested=len(files),
            chunks_created=len(chunks)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rebuild-index")
async def rebuild_index():
    try:
        chroma_client.reset()

        from app.services.data_loader import load_all_data_sources
        results = load_all_data_sources()

        return {
            "status": "success",
            "message": "Index rebuilt successfully",
            "documents": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections")
async def list_collections():
    try:
        collections = chroma_client.list_collections()
        collection_info = []

        for coll in collections:
            info = chroma_client.get_collection_info(coll)
            collection_info.append(info)

        return {"collections": collection_info}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))