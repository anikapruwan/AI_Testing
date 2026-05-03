# Naive RAG Pipeline

A beautiful, interactive, and functional Retrieval-Augmented Generation (RAG) system with a visual pipeline. 

Features:
- **Hybrid LLM Support**: Use local models via Ollama or cloud models via Groq API.
- **Visual Pipeline**: Step-by-step UI showing Document Upload, Chunking, Embeddings, Vector DB, Retrieval, and LLM Generation.
- **Modern UI**: Built with React, TailwindCSS, and Framer Motion for a stunning "Nexus" theme.

## 🚀 Setup Instructions

### 1. Backend Setup

1. Open a terminal and navigate to the `backend` folder:
   ```bash
   cd rag-app
   ```
2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up your `.env` file in the root directory (`rag-app/.env`) with your Groq API key:
   ```
   GROQ_API_KEY=gsk_your_api_key_here
   ```
5. (Optional) Setup Ollama for local inference:
   - Install [Ollama](https://ollama.com/)
   - Pull a model, e.g., `ollama pull llama3`
6. Run the FastAPI server:
   ```bash
   cd backend
   python main.py
   ```
   The backend will start at `http://localhost:8000`.

### 2. Frontend Setup

1. Open a new terminal and navigate to the `frontend` folder:
   ```bash
   cd rag-app/frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   The frontend will start at `http://localhost:5173`.

## 🧠 Using the App

1. **Upload Document**: Drag & Drop a `.txt` or `.pdf` file. Click "Process Document". Watch the UI visualize the chunking and embedding steps.
2. **Configure LLM**: Select your preferred provider (Groq or Ollama) and enter your API key if using Groq.
3. **Ask Questions**: Enter a query related to your uploaded document and click "Generate Answer". Watch the retrieval and generation steps in real-time.

## 📊 Sample Queries

If you uploaded a document about "Quantum Computing":
- "What are the main principles of Quantum Computing?"
- "How does a qubit differ from a classical bit?"

Enjoy the visual journey of your data through the RAG pipeline!
