import os
import pandas as pd
import numpy as np
import uuid
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer, CrossEncoder
import requests

from flask import Flask, render_template_string, request, jsonify, send_from_directory

load_dotenv()

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CHROMA_DIR = APP_DIR / "chroma_db"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Environment Variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
RERANK_MODEL_NAME = os.getenv("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

# RAG Settings
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
TOP_K_RETRIEVAL = 20
TOP_K_RERANK = 5

# -----------------------------------------------------------------------------
# RAG Core Logic
# -----------------------------------------------------------------------------
class AdvancedRAGEngine:
    def __init__(self):
        # Embedding Model
        self.embed_model = SentenceTransformer(EMBED_MODEL_NAME)
        
        # Re-ranker Model
        self.reranker = CrossEncoder(RERANK_MODEL_NAME)
        
        # Vector DB
        self.db_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection = self.db_client.get_or_create_collection(
            name="test_cases_collection",
            embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL_NAME)
        )

    def chunk_text(self, text: str):
        """Splits text into overlapping chunks."""
        chunks = []
        start = 0
        text_len = len(text)
        while start < text_len:
            end = start + CHUNK_SIZE
            chunks.append(text[start:end])
            start += CHUNK_SIZE - CHUNK_OVERLAP
            if start >= text_len:
                break
        return chunks

    def process_file(self, file_path: str):
        """Processes CSV/Excel and returns chunking preview and DB status."""
        df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
        
        # Combine all columns into a single text block for each row (test case)
        all_texts = df.apply(lambda row: " ".join(row.astype(str)), axis=1).tolist()
        
        full_chunks = []
        preview_chunks = []
        
        for i, text in enumerate(all_texts):
            chunks = self.chunk_text(text)
            # Store metadata about which row this chunk came from
            for j, c in enumerate(chunks):
                chunk_id = f"row_{i}_chunk_{j}"
                full_chunks.append({
                    "id": chunk_id,
                    "text": c,
                    "metadata": {"row": i, "chunk_index": j}
                })
                if len(preview_chunks) <  50: # Limit preview
                    preview_chunks.append({
                        "id": chunk_id,
                        "text": c,
                        "row": i,
                        "chunk_idx": j
                    })

        # Ingest into ChromaDB
        ids = [c["id"] for c in full_chunks]
        texts = [c["text"] for c in full_chunks]
        metadatas = [c["metadata"] for c in full_chunks]
        
        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )
        
        return {
            "total_rows": len(all_texts),
            "total_chunks": len(full_chunks),
            "preview": preview_chunks,
            "chunk_size": CHUNK_SIZE,
            "overlap": CHUNK_OVERLAP
        }

    def retrieve_and_rerank(self, query: str):
        """Retrieves top-K, then re-ranks them using Cross-Encoder."""
        # 1. Initial Retrieval
        results = self.collection.query(
            query_texts=[query],
            n_results=TOP_K_RETRIEVAL
        )
        
        initial_docs = results['documents'][0]
        initial_ids = results['ids'][0]
        
        # 2. Re-ranking
        pairs = [[query, doc] for doc in initial_docs]
        scores = self.reranker.predict(pairs)
        
        # Combine and sort
        ranked_results = []
        for i in range(len(initial_docs)):
            ranked_results.append({
                "id": initial_ids[i],
                "text": initial_docs[i],
                "score": float(scores[i])
            })
        
        ranked_results = sorted(ranked_results, key=lambda x: x['score'], reverse=True)
        return initial_docs, ranked_results[:TOP_K_RERANK]

    def generate_answer(self, query: str, context_chunks: List[str]):
        """Calls Groq API to generate final response."""
        if not GROQ_API_KEY:
            return "[Error] Groq API Key missing."

        context_text = "\n\n---\n\n".join([f"Chunk: {c}" for c in context_chunks])
        
        system_prompt = (
            "You are an advanced Quality Assurance assistant. "
            "Use the provided context (test case chunks) to answer the user's request. "
            "If asked to create a test case, follow the patterns found in the context. "
            "Be precise, professional, and cite the information used."
        )
        
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"CONTEXT:\n{context_text}\n\nQUERY: {query}"}
            ],
            "temperature": 0.2
        }
        
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=60)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[Groq Error] {str(e)}"

# -----------------------------------------------------------------------------
# Flask Application
# -----------------------------------------------------------------------------
app = Flask(__name__)
rag_engine = AdvancedRAGEngine()

@app.route('/')
def index():
    return render_template_string(CLAUDE_UI)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
        
    file_path = UPLOAD_DIR / file.filename
    file.save(file_path)
    
    try:
        stats = rag_engine.process_file(str(file_path))
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/query', methods=['POST'])
def query():
    data = request.json
    user_query = data.get("query", "")
    if not user_query:
        return jsonify({"error": "Query is empty"}), 400
    
    # RAG Pipeline
    initial_chunks, reranked_chunks = rag_engine.retrieve_and_rerank(user_query)
    
    context_texts = [c['text'] for c in reranked_chunks]
    answer = rag_engine.generate_answer(user_query, context_texts)
    
    return jsonify({
        "answer": answer,
        "retrieved_count": len(initial_chunks),
        "reranked_count": len(reranked_chunks),
        "reranked_docs": reranked_chunks
    })

# -----------------------------------------------------------------------------
# UI Template (Claude-themed)
# -----------------------------------------------------------------------------
CLAUDE_UI = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advanced RAG Explorer</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        :root {
            --claude-bg: #f9f7f2;
            --claude-sidebar: #f0eada;
            --claude-accent: #d97757;
            --claude-text: #3d3a35;
            --claude-panel: #ffffff;
            --claude-border: #e5e2db;
        }
        body { background-color: var(--claude-bg); color: var(--claude-text); font-family: 'Inter', sans-serif; }
        .sidebar { background-color: var(--claude-sidebar); border-right: 1px solid var(--claude-border); }
        .main-content { background-color: var(--claude-bg); }
        .card { background-color: var(--claude-panel); border: 1px solid var(--claude-border); border-radius: 12px; }
        .btn-primary { background-color: var(--claude-accent); color: white; transition: opacity 0.2s; }
        .btn-primary:hover { opacity: 0.9; }
        .chunk-preview { font-family: 'Fira Code', monospace; font-size: 12px; }
        .step-badge { background: var(--claude-accent); color: white; font-size: 10px; padding: 2px 6px; border-radius: 4px; }
    </style>
</head>
<body class="flex h-screen">

    <!-- Left Panel -->
    <div class="sidebar w-80 h-full flex flex-col p-6 shadow-sm">
        <div class="mb-8">
            <h1 class="text-xl font-bold text-gray-800">Advanced RAG</h1>
            <p class="text-xs text-gray-500">Test Case Explorer</p>
        </div>

        <div class="space-y-6">
            <div>
                <label class="block text-sm font-medium mb-2">Upload Test Cases</label>
                <input type="file" id="fileInput" class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-orange-50 file:text-orange-700 hover:file:bg-orange-100 cursor-pointer" accept=".csv, .xlsx">
                <button onclick="uploadFile()" class="btn-primary w-full mt-3 py-2 rounded-lg font-medium">Ingest Data</button>
            </div>
            
            <div class="pt-6 border-t border-gray-300">
                <h3 class="text-sm font-semibold mb-3">System Config</h3>
                <div class="text-xs space-y-2 text-gray-600">
                    <div class="flex justify-between"><span>Embed Model:</span> <span class="font-mono">BGE-Small</span></div>
                    <div class="flex justify-between"><span>Vector DB:</span> <span class="font-mono">ChromaDB</span></div>
                    <div class="flex justify-between"><span>Re-ranker:</span> <span class="font-mono">Cross-Encoder</span></div>
                    <div class="flex justify-between"><span>LLM:</span> <span class="font-mono">Groq (Open Source)</span></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Right Content -->
    <div class="main-content flex-1 overflow-y-auto p-8">
        
        <!-- SECTION 1: INGESTION PREVIEW -->
        <div id="ingestionSection" class="mb-12">
            <h2 class="text-2xl font-semibold mb-6">Stage 1: Ingestion Pipeline</h2>
            <div id="ingestionStats" class="hidden grid grid-cols-4 gap-4 mb-6">
                <div class="card p-4 text-center">
                    <div class="text-sm text-gray-500">Total Rows</div>
                    <div id="statRows" class="text-2xl font-bold">0</div>
                </div>
                <div class="card p-4 text-center">
                    <div class="text-sm text-gray-500">Total Chunks</div>
                    <div id="statChunks" class="text-2xl font-bold">0</div>
                </div>
                <div class="card p-4 text-center">
                    <div class="text-sm text-gray-500">Chunk Size</div>
                    <div id="statSize" class="text-2xl font-bold">0</div>
                </div>
                <div class="card p-4 text-center">
                    <div class="text-sm text-gray-500">Overlap</div>
                    <div id="statOverlap" class="text-2xl font-bold">0</div>
                </div>
            </div>

            <div id="chunkPreview" class="hidden card p-6">
                <h3 class="text-lg font-medium mb-4">Chunking Algorithm Preview</h3>
                <div id="chunkList" class="space-y-4 max-h-96 overflow-y-auto">
                    <!-- Chunks injected here -->
                </div>
            </div>
        </div>

        <!-- SECTION 2: CHAT & RETRIEVAL -->
        <div id="chatSection">
            <h2 class="text-2xl font-semibold mb-6">Stage 2: Intelligent Retrieval</h2>
            <div class="card p-6 flex gap-4 items-center mb-6">
                <input type="text" id="queryInput" placeholder="Ask about test cases or request a new Jira test case..." class="flex-1 p-3 border border-gray-300 rounded-lg outline-none focus:border-orange-400">
                <button onclick="askQuery()" class="btn-primary px-6 py-3 rounded-lg font-medium">Send Query</button>
            </div>

            <div id="resultPipeline" class="hidden space-y-6">
                <!-- STEP 1: RETRIEVAL -->
                <div class="card p-6">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="font-semibold flex items-center gap-2">
                            <span class="step-badge">STEP 1</span> Vector Retrieval
                        </h3>
                        <span id="retrievedCount" class="text-sm text-gray-500">Fetched 0 chunks</span>
                    </div>
                    <div id="initialChunks" class="grid grid-cols-1 gap-3 max-h-60 overflow-y-auto text-xs text-gray-600">
                        <!-- Initial chunks -->
                    </div>
                </div>

                <!-- STEP 2: RE-RANKING -->
                <div class="card p-6">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="font-semibold flex items-center gap-2">
                            <span class="step-badge">STEP 2</span> Cross-Encoder Re-ranking
                        </h3>
                        <span id="rerankedCount" class="text-sm text-gray-500">Re-ranked to 0 chunks</span>
                    </div>
                    <div id="rerankedChunks" class="space-y-3">
                        <!-- Reranked chunks -->
                    </div>
                </div>

                <!-- STEP 3: FINAL ANSWER -->
                <div class="card p-6" style="border-left: 4px solid var(--claude-accent);">
                    <h3 class="font-semibold flex items-center gap-2 mb-4">
                        <span class="step-badge">STEP 3</span> LLM Generation (Groq)
                    </h3>
                    <div id="finalAnswer" class="text-gray-800 leading-relaxed">
                        <!-- LLM Result -->
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function uploadFile() {
            const fileInput = document.getElementById('fileInput');
            if (!fileInput.files[0]) return alert('Please select a file');

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            const res = await fetch('/upload', { method: 'POST', body: formData });
            const data = await res.json();

            if (data.error) return alert(data.error);

            document.getElementById('ingestionStats').classList.remove('hidden');
            document.getElementById('statRows').innerText = data.total_rows;
            document.getElementById('statChunks').innerText = data.total_chunks;
            document.getElementById('statSize').innerText = data.chunk_size;
            document.getElementById('statOverlap').innerText = data.overlap;

            document.getElementById('chunkPreview').classList.remove('hidden');
            const list = document.getElementById('chunkList');
            list.innerHTML = '';
            data.preview.forEach(c => {
                list.innerHTML += `
                    <div class="p-3 border border-gray-200 rounded-lg bg-gray-50">
                        <div class="flex justify-between text-xs text-gray-400 mb-1">
                            <span>ID: ${c.id}</span>
                            <span>Row: ${c.row} | Chunk Index: ${c.chunk_idx}</span>
                        </div>
                        <div class="chunk-preview text-gray-700">${c.text}</div>
                    </div>
                `;
            });
        }

        async function askQuery() {
            const query = document.getElementById('queryInput').value;
            if (!query) return;

            document.getElementById('resultPipeline').classList.add('hidden');
            
            const res = await fetch('/query', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ query })
            });
            const data = await res.json();

            document.getElementById('resultPipeline').classList.remove('hidden');
            
            document.getElementById('retrievedCount').innerText = `Fetched ${data.retrieved_count} chunks`;
            const initialDiv = document.getElementById('initialChunks');
            initialDiv.innerHTML = '';
            for (let i = 0; i < Math.min(data.retrieved_count, 10); i++) {
               initialDiv.innerHTML += `<div class="p-2 bg-gray-100 rounded">Chunk #${i+1}...</div>`;
            }

            document.getElementById('rerankedCount').innerText = `Re-ranked to ${data.reranked_count} chunks`;
            const rerankDiv = document.getElementById('rerankedChunks');
            rerankDiv.innerHTML = '';
            data.reranked_docs.forEach((doc, idx) => {
                rerankDiv.innerHTML += `
                    <div class="p-3 border border-gray-200 rounded-lg bg-blue-50 flex justify-between">
                        <div class="text-xs text-gray-700 flex-1 pr-4">${doc.text}</div>
                        <div class="text-xs font-bold text-blue-600">Score: ${doc.score.toFixed(4)}</div>
                    </div>
                `;
            });

            document.getElementById('finalAnswer').innerText = data.answer;
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    app.run(host="0.0.0.0", port=5001, debug=False)
