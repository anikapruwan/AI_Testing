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
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advanced RAG Explorer - Nexus</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    fontFamily: { sans: ['Outfit', 'sans-serif'] },
                    colors: {
                        dark: '#0B0F19',
                        darker: '#06080D',
                        card: 'rgba(30, 41, 59, 0.5)',
                        accent: '#38BDF8',
                        accentDark: '#0284C7',
                        neonPink: '#EC4899',
                        neonPurple: '#8B5CF6'
                    }
                }
            }
        }
    </script>
    <style>
        body { background-color: #0B0F19; color: #E2E8F0; }
        .glass-panel {
            background: rgba(30, 41, 59, 0.4);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        }
        .btn-gradient {
            background: linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%);
            transition: all 0.3s ease;
        }
        .btn-gradient:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px -10px rgba(236, 72, 153, 0.5);
        }
        .bg-animated {
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            z-index: -1;
            background: radial-gradient(circle at 15% 50%, rgba(139, 92, 246, 0.15), transparent 25%),
                        radial-gradient(circle at 85% 30%, rgba(236, 72, 153, 0.15), transparent 25%);
            animation: pulseBg 10s infinite alternate;
        }
        @keyframes pulseBg {
            0% { opacity: 0.8; }
            100% { opacity: 1.2; }
        }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.2); }
        .chunk-preview { font-family: 'Fira Code', monospace; font-size: 13px; line-height: 1.5; }
        .step-badge { 
            background: linear-gradient(90deg, #38BDF8, #8B5CF6);
            color: white; font-size: 11px; padding: 3px 8px; border-radius: 6px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;
        }
    </style>
</head>
<body class="flex h-screen overflow-hidden antialiased text-gray-200">
    <div class="bg-animated"></div>

    <!-- Left Panel -->
    <div class="glass-panel w-80 h-full flex flex-col p-8 z-10">
        <div class="mb-10">
            <h1 class="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-accent to-neonPurple mb-1">Nexus RAG</h1>
            <p class="text-xs text-gray-400 uppercase tracking-widest font-semibold">Test Case Intelligence</p>
        </div>

        <div class="space-y-8 flex-1">
            <div class="p-5 glass-panel rounded-xl">
                <label class="block text-sm font-semibold mb-3 text-gray-300">Upload Knowledge Base</label>
                <div class="relative group">
                    <input type="file" id="fileInput" class="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-gray-800 file:text-gray-300 hover:file:bg-gray-700 cursor-pointer transition-all" accept=".csv, .xlsx">
                </div>
                <button onclick="uploadFile()" class="btn-gradient w-full mt-4 py-2.5 rounded-lg font-semibold text-sm shadow-lg">Initialize Engine</button>
            </div>
            
            <div class="pt-6 border-t border-gray-800">
                <h3 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">Neural Architecture</h3>
                <div class="text-xs space-y-3">
                    <div class="flex justify-between items-center"><span class="text-gray-500">Embeddings</span> <span class="px-2 py-1 bg-gray-800 rounded font-mono text-accent">BGE-Small</span></div>
                    <div class="flex justify-between items-center"><span class="text-gray-500">Vector Engine</span> <span class="px-2 py-1 bg-gray-800 rounded font-mono text-neonPink">ChromaDB</span></div>
                    <div class="flex justify-between items-center"><span class="text-gray-500">Re-ranker</span> <span class="px-2 py-1 bg-gray-800 rounded font-mono text-accent">CrossEncoder</span></div>
                    <div class="flex justify-between items-center"><span class="text-gray-500">LLM Core</span> <span class="px-2 py-1 bg-gray-800 rounded font-mono text-neonPurple">Groq 120B</span></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Right Content -->
    <div class="flex-1 overflow-y-auto p-10 z-10 relative" id="mainScroll">
        
        <!-- SECTION 1: INGESTION PREVIEW -->
        <div id="ingestionSection" class="max-w-5xl mx-auto mb-16">
            <div id="ingestionStats" class="hidden grid grid-cols-4 gap-6 mb-8 transform transition-all">
                <div class="glass-panel p-6 rounded-2xl text-center border-t-2 border-t-accent">
                    <div class="text-xs text-gray-400 uppercase tracking-wide font-semibold mb-2">Total Rows</div>
                    <div id="statRows" class="text-4xl font-light text-white">0</div>
                </div>
                <div class="glass-panel p-6 rounded-2xl text-center border-t-2 border-t-neonPink">
                    <div class="text-xs text-gray-400 uppercase tracking-wide font-semibold mb-2">Total Vectors</div>
                    <div id="statChunks" class="text-4xl font-light text-white">0</div>
                </div>
                <div class="glass-panel p-6 rounded-2xl text-center border-t-2 border-t-neonPurple">
                    <div class="text-xs text-gray-400 uppercase tracking-wide font-semibold mb-2">Chunk Size</div>
                    <div id="statSize" class="text-4xl font-light text-white">0</div>
                </div>
                <div class="glass-panel p-6 rounded-2xl text-center border-t-2 border-t-accent">
                    <div class="text-xs text-gray-400 uppercase tracking-wide font-semibold mb-2">Overlap</div>
                    <div id="statOverlap" class="text-4xl font-light text-white">0</div>
                </div>
            </div>

            <div id="chunkPreview" class="hidden glass-panel rounded-2xl p-8 shadow-xl">
                <h3 class="text-xl font-medium mb-6 flex items-center gap-3">
                    <svg class="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                    Vectorization Pipeline Preview
                </h3>
                <div id="chunkList" class="space-y-4 max-h-[400px] overflow-y-auto pr-2">
                    <!-- Chunks injected here -->
                </div>
            </div>
        </div>

        <!-- SECTION 2: CHAT & RETRIEVAL -->
        <div id="chatSection" class="max-w-5xl mx-auto">
            <div class="glass-panel p-2 rounded-2xl flex gap-2 items-center mb-10 border border-gray-700 focus-within:border-accent transition-colors shadow-2xl">
                <div class="pl-4 text-gray-400">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                </div>
                <input type="text" id="queryInput" placeholder="Enter query to initiate semantic search and generation..." class="flex-1 p-4 bg-transparent border-none outline-none text-white placeholder-gray-500 text-lg">
                <button onclick="askQuery()" class="btn-gradient px-8 py-4 rounded-xl font-bold tracking-wide flex items-center gap-2">
                    <span>Synthesize</span>
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                </button>
            </div>

            <div id="resultPipeline" class="hidden space-y-8">
                <!-- Final Answer displayed first for better UX -->
                <div class="glass-panel p-8 rounded-2xl relative overflow-hidden">
                    <div class="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-neonPink to-neonPurple"></div>
                    <h3 class="font-bold flex items-center gap-3 mb-6 text-xl">
                        <span class="step-badge">Stage 3</span> Generated Response
                    </h3>
                    <div id="finalAnswer" class="text-gray-300 leading-relaxed text-lg font-light whitespace-pre-wrap">
                        <!-- LLM Result -->
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-8">
                    <!-- STEP 1: RETRIEVAL -->
                    <div class="glass-panel p-6 rounded-2xl opacity-80 hover:opacity-100 transition-opacity">
                        <div class="flex justify-between items-center mb-5">
                            <h3 class="font-semibold flex items-center gap-2 text-sm text-gray-300">
                                <span class="step-badge">Stage 1</span> Vector Retrieval
                            </h3>
                            <span id="retrievedCount" class="text-xs font-mono text-accent bg-gray-800 px-2 py-1 rounded">0</span>
                        </div>
                        <div id="initialChunks" class="grid grid-cols-1 gap-3 max-h-60 overflow-y-auto pr-2">
                            <!-- Initial chunks -->
                        </div>
                    </div>

                    <!-- STEP 2: RE-RANKING -->
                    <div class="glass-panel p-6 rounded-2xl opacity-80 hover:opacity-100 transition-opacity">
                        <div class="flex justify-between items-center mb-5">
                            <h3 class="font-semibold flex items-center gap-2 text-sm text-gray-300">
                                <span class="step-badge">Stage 2</span> Cross-Encoder Re-rank
                            </h3>
                            <span id="rerankedCount" class="text-xs font-mono text-neonPink bg-gray-800 px-2 py-1 rounded">0</span>
                        </div>
                        <div id="rerankedChunks" class="space-y-3 max-h-60 overflow-y-auto pr-2">
                            <!-- Reranked chunks -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function uploadFile() {
            const fileInput = document.getElementById('fileInput');
            if (!fileInput.files[0]) return alert('Please select a file');

            const btn = document.querySelector('button[onclick="uploadFile()"]');
            const originalText = btn.innerText;
            btn.innerText = 'Processing...';
            btn.classList.add('opacity-50');

            try {
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);

                const res = await fetch('/upload', { method: 'POST', body: formData });
                const data = await res.json();

                if (data.error) throw new Error(data.error);

                document.getElementById('ingestionStats').classList.remove('hidden');
                
                // Animate numbers
                animateValue("statRows", 0, data.total_rows, 1000);
                animateValue("statChunks", 0, data.total_chunks, 1000);
                document.getElementById('statSize').innerText = data.chunk_size;
                document.getElementById('statOverlap').innerText = data.overlap;

                document.getElementById('chunkPreview').classList.remove('hidden');
                const list = document.getElementById('chunkList');
                list.innerHTML = '';
                data.preview.forEach(c => {
                    list.innerHTML += `
                        <div class="p-4 bg-gray-800/50 border border-gray-700/50 rounded-xl hover:border-accent/50 transition-colors">
                            <div class="flex justify-between text-xs text-gray-500 mb-2 font-mono">
                                <span>ID: ${c.id}</span>
                                <span class="bg-gray-900 px-2 py-1 rounded">R:${c.row} | C:${c.chunk_idx}</span>
                            </div>
                            <div class="chunk-preview text-gray-300">${c.text}</div>
                        </div>
                    `;
                });
            } catch (err) {
                alert(err.message);
            } finally {
                btn.innerText = originalText;
                btn.classList.remove('opacity-50');
            }
        }

        async function askQuery() {
            const query = document.getElementById('queryInput').value;
            if (!query) return;

            const pipeline = document.getElementById('resultPipeline');
            pipeline.classList.remove('hidden');
            
            document.getElementById('finalAnswer').innerHTML = '<div class="flex gap-2 items-center text-accent"><svg class="animate-spin h-5 w-5" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Synthesizing response...</div>';
            
            document.getElementById('initialChunks').innerHTML = '<div class="text-gray-500 text-xs animate-pulse">Searching vector space...</div>';
            document.getElementById('rerankedChunks').innerHTML = '<div class="text-gray-500 text-xs animate-pulse">Waiting for retrieval...</div>';
            
            try {
                const res = await fetch('/query', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ query })
                });
                const data = await res.json();

                document.getElementById('retrievedCount').innerText = `${data.retrieved_count}`;
                const initialDiv = document.getElementById('initialChunks');
                initialDiv.innerHTML = '';
                for (let i = 0; i < Math.min(data.retrieved_count, 10); i++) {
                   initialDiv.innerHTML += `<div class="p-2 bg-gray-800/30 border border-gray-700/50 rounded text-xs text-gray-400">Context Vector #${i+1} loaded</div>`;
                }

                document.getElementById('rerankedCount').innerText = `${data.reranked_count}`;
                const rerankDiv = document.getElementById('rerankedChunks');
                rerankDiv.innerHTML = '';
                data.reranked_docs.forEach((doc, idx) => {
                    const scoreColor = doc.score > 0.5 ? 'text-green-400' : 'text-yellow-400';
                    rerankDiv.innerHTML += `
                        <div class="p-3 bg-gray-800/30 border border-gray-700/50 rounded-xl flex justify-between gap-3 hover:border-neonPink/30 transition-colors">
                            <div class="text-xs text-gray-400 flex-1 line-clamp-3 leading-relaxed">${doc.text}</div>
                            <div class="text-xs font-mono font-bold ${scoreColor} whitespace-nowrap bg-gray-900 px-2 py-1 rounded h-fit">${doc.score.toFixed(3)}</div>
                        </div>
                    `;
                });

                document.getElementById('finalAnswer').innerText = data.answer;
            } catch (err) {
                document.getElementById('finalAnswer').innerHTML = `<span class="text-red-400">Error: ${err.message}</span>`;
            }
        }

        function animateValue(id, start, end, duration) {
            if (start === end) return;
            const obj = document.getElementById(id);
            let startTimestamp = null;
            const step = (timestamp) => {
                if (!startTimestamp) startTimestamp = timestamp;
                const progress = Math.min((timestamp - startTimestamp) / duration, 1);
                obj.innerHTML = Math.floor(progress * (end - start) + start);
                if (progress < 1) {
                    window.requestAnimationFrame(step);
                }
            };
            window.requestAnimationFrame(step);
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    app.run(host="0.0.0.0", port=5001, debug=False)
