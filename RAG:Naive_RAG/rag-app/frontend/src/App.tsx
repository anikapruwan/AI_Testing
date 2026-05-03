import { useState } from 'react'
import axios from 'axios'
import { 
  FileText, Scissors, Database, Search, MessageSquare, 
  Settings, CheckCircle2, UploadCloud, File, Cpu, Zap, Moon, Sun
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { PipelineCard } from './components/PipelineCard'

const API_URL = 'http://localhost:8000'

function App() {
  const [theme, setTheme] = useState<'dark'|'light'>('dark')
  
  // App state
  const [file, setFile] = useState<File | null>(null)
  const [apiKey, setApiKey] = useState('')
  const [query, setQuery] = useState('')
  const [provider, setProvider] = useState('groq')
  const [model, setModel] = useState('llama-3.1-8b-instant')
  
  // Pipeline State
  const [activeStep, setActiveStep] = useState<number>(-1)
  const [loading, setLoading] = useState(false)
  
  // Results
  const [uploadResult, setUploadResult] = useState<any>(null)
  const [processResult, setProcessResult] = useState<any>(null)
  const [queryResult, setQueryResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark'
    setTheme(newTheme)
    document.documentElement.classList.toggle('dark')
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const processDocument = async () => {
    if (!file) {
      setError("Please select a file first.")
      return
    }
    
    setLoading(true)
    setError(null)
    setActiveStep(0) // Upload
    
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      // 1. Upload
      const uploadRes = await axios.post(`${API_URL}/upload`, formData)
      setUploadResult(uploadRes.data)
      
      // 2. Process (Chunking & Embedding)
      setActiveStep(1) // Chunking
      const processRes = await axios.post(`${API_URL}/process_pipeline`)
      
      // Simulate step delays for visual effect
      setTimeout(() => {
        setActiveStep(2) // Embeddings
        setTimeout(() => {
          setActiveStep(3) // Vector DB Ready
          setProcessResult(processRes.data)
          setLoading(false)
        }, 1000)
      }, 1000)
      
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
      setLoading(false)
      setActiveStep(-1)
    }
  }

  const runQuery = async () => {
    if (!query) {
      setError("Please enter a query.")
      return
    }
    if (provider === 'groq' && !apiKey) {
      setError("Please enter a Groq API key.")
      return
    }
    
    setLoading(true)
    setError(null)
    setActiveStep(4) // Retrieval
    setQueryResult(null)
    
    try {
      const res = await axios.post(`${API_URL}/query`, {
        query,
        provider,
        model,
        api_key: apiKey
      })
      
      setTimeout(() => {
        setActiveStep(5) // Prompting
        setTimeout(() => {
          setActiveStep(6) // LLM Responding
          setQueryResult(res.data)
          setLoading(false)
        }, 1000)
      }, 1000)
      
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
      setLoading(false)
    }
  }

  return (
    <div className={`min-h-screen transition-colors duration-300 ${theme === 'dark' ? 'dark bg-[#0a0a0a] text-white' : 'bg-gray-50 text-gray-900'}`}>
      
      {/* Header */}
      <header className="sticky top-0 z-50 glass-panel border-b border-white/10 px-6 py-4 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="bg-primary/20 p-2 rounded-xl text-primary">
            <Cpu size={24} />
          </div>
          <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-blue-400">
            Nexus RAG
          </h1>
        </div>
        <button onClick={toggleTheme} className="p-2 rounded-full hover:bg-white/10 transition-colors">
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
        </button>
      </header>

      <main className="container mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Panel - Controls */}
        <div className="lg:col-span-4 space-y-6">
          
          <div className="glass-panel p-6 rounded-2xl">
            <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
              <UploadCloud size={20} className="text-primary" />
              1. Document Input
            </h2>
            <div className="space-y-4">
              <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-white/20 rounded-xl cursor-pointer hover:bg-white/5 transition-colors">
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  <FileText className="w-8 h-8 mb-2 text-muted-foreground" />
                  <p className="mb-2 text-sm text-muted-foreground">
                    <span className="font-semibold">Click to upload</span> or drag and drop
                  </p>
                  <p className="text-xs text-muted-foreground">PDF, TXT, DOCX, XLSX, PPTX, CSV (MAX. 10MB)</p>
                </div>
                <input type="file" className="hidden" accept=".pdf,.txt,.docx,.xlsx,.pptx,.csv" onChange={handleFileUpload} />
              </label>
              
              {file && (
                <div className="flex items-center gap-3 p-3 bg-white/5 rounded-lg border border-white/10">
                  <File size={16} className="text-blue-400" />
                  <span className="text-sm truncate">{file.name}</span>
                </div>
              )}
              
              <button 
                onClick={processDocument}
                disabled={!file || loading}
                className="w-full py-3 px-4 bg-primary hover:bg-primary/90 text-white rounded-xl font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading && activeStep < 4 ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/> : <Database size={18} />}
                Process Document
              </button>
            </div>
          </div>

          <div className="glass-panel p-6 rounded-2xl">
            <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
              <Settings size={20} className="text-primary" />
              2. LLM Configuration
            </h2>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-1 block text-muted-foreground">Provider</label>
                <select 
                  value={provider}
                  onChange={(e) => {
                    setProvider(e.target.value);
                    setModel(e.target.value === 'groq' ? 'llama-3.1-8b-instant' : 'llama3');
                  }}
                  className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-sm focus:ring-2 focus:ring-primary outline-none appearance-none"
                >
                  <option value="groq">Groq ⚡ (Cloud)</option>
                  <option value="ollama">Ollama 🦙 (Local)</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium mb-1 block text-muted-foreground">Model</label>
                <select 
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-sm focus:ring-2 focus:ring-primary outline-none appearance-none"
                >
                  {provider === 'groq' ? (
                    <>
                      <option value="llama-3.1-8b-instant">Llama 3.1 8B Instant</option>
                      <option value="llama-3.1-70b-versatile">Llama 3.1 70B Versatile</option>
                      <option value="llama3-70b-8192">Llama 3 70B</option>
                      <option value="mixtral-8x7b-32768">Mixtral 8x7B</option>
                      <option value="gemma2-9b-it">Gemma 2 9B</option>
                    </>
                  ) : (
                    <>
                      <option value="llama3">Llama 3</option>
                      <option value="llama3.2">Llama 3.2</option>
                      <option value="mistral">Mistral</option>
                      <option value="gemma2">Gemma 2</option>
                    </>
                  )}
                </select>
              </div>
              
              <AnimatePresence>
                {provider === 'groq' && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                  >
                    <label className="text-sm font-medium mb-1 block text-muted-foreground">Groq API Key</label>
                    <input 
                      type="password"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="gsk_..."
                      className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-sm focus:ring-2 focus:ring-primary outline-none"
                    />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>

          <div className="glass-panel p-6 rounded-2xl">
            <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
              <MessageSquare size={20} className="text-primary" />
              3. Ask Question
            </h2>
            <div className="space-y-4">
              <textarea 
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="What is this document about?"
                className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-sm focus:ring-2 focus:ring-primary outline-none resize-none h-24"
              />
              <button 
                onClick={runQuery}
                disabled={!processResult || !query || loading}
                className="w-full py-3 px-4 bg-gradient-to-r from-primary to-blue-500 hover:from-primary/90 hover:to-blue-500/90 text-white rounded-xl font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading && activeStep >= 4 ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/> : <Zap size={18} />}
                Generate Answer
              </button>
            </div>
          </div>
          
          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/50 rounded-xl text-red-500 text-sm">
              {error}
            </div>
          )}

        </div>

        {/* Right Panel - Visualization */}
        <div className="lg:col-span-8 space-y-4 relative">
          
          <div className="absolute inset-0 pointer-events-none">
             {/* Decorative background gradients */}
             <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-primary/20 rounded-full blur-[100px]" />
             <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-blue-500/20 rounded-full blur-[100px]" />
          </div>

          <h2 className="text-xl font-bold mb-6 flex items-center gap-2 relative z-10">
            Pipeline Flow
            {loading && <span className="flex h-3 w-3 relative ml-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-primary"></span>
            </span>}
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 relative z-10">
            
            <PipelineCard 
              title="1. Document Upload" 
              icon={<FileText size={20}/>}
              isActive={activeStep === 0}
              isCompleted={activeStep > 0}
            >
              {uploadResult && (
                <div className="bg-black/30 p-3 rounded-lg border border-white/5">
                  <p className="text-green-400 text-xs mb-1">✓ Extracted {uploadResult.char_count} chars</p>
                  <p className="text-xs truncate">{uploadResult.text_preview}</p>
                </div>
              )}
            </PipelineCard>

            <PipelineCard 
              title="2. Chunking" 
              icon={<Scissors size={20}/>}
              isActive={activeStep === 1}
              isCompleted={activeStep > 1}
              latency={processResult?.chunking?.latency_ms}
            >
              {processResult && (
                <div className="bg-black/30 p-3 rounded-lg border border-white/5">
                  <p className="text-blue-400 text-xs mb-2">Created {processResult.chunking.num_chunks} chunks</p>
                  <div className="flex gap-2 overflow-x-auto pb-2">
                    {processResult.chunking.chunks.slice(0, 3).map((c: string, i: number) => (
                      <div key={i} className="min-w-[120px] bg-white/5 p-2 rounded text-[10px] line-clamp-3">
                        {c}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </PipelineCard>

            <PipelineCard 
              title="3. Embeddings" 
              icon={<Database size={20}/>}
              isActive={activeStep === 2}
              isCompleted={activeStep > 2}
              latency={processResult?.embeddings?.latency_ms}
            >
              {processResult && (
                <div className="bg-black/30 p-3 rounded-lg border border-white/5">
                  <p className="text-purple-400 text-xs mb-2">Model: all-MiniLM-L6-v2 ({processResult.embeddings.vector_dimension}d)</p>
                  <div className="flex flex-wrap gap-1">
                    {processResult.embeddings.sample_embedding.map((val: number, i: number) => (
                      <span key={i} className="text-[10px] bg-primary/20 px-1 py-0.5 rounded font-mono">
                        {val.toFixed(2)}
                      </span>
                    ))}
                    <span className="text-[10px] text-muted-foreground px-1">...</span>
                  </div>
                </div>
              )}
            </PipelineCard>

            <PipelineCard 
              title="4. Vector Store Ready" 
              icon={<CheckCircle2 size={20}/>}
              isActive={activeStep === 3}
              isCompleted={activeStep > 3}
            >
               {activeStep > 2 && (
                 <p className="text-xs text-green-400 bg-green-400/10 p-2 rounded-lg inline-block">
                   Qdrant Vector Store saved successfully
                 </p>
               )}
            </PipelineCard>

          </div>

          <div className="my-8 border-t border-white/10 relative z-10" />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 relative z-10">
            
            <PipelineCard 
              title="5. Retrieval" 
              icon={<Search size={20}/>}
              isActive={activeStep === 4}
              isCompleted={activeStep > 4}
              latency={queryResult?.retrieval?.latency_ms}
            >
              {queryResult && (
                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground">Top K matches:</p>
                  {queryResult.retrieval.results.map((r: any, i: number) => (
                    <div key={i} className="bg-black/30 p-2 rounded-lg border border-white/5 text-xs flex justify-between items-start">
                      <span className="line-clamp-2 pr-2">{r.content}</span>
                      <span className="text-orange-400 font-mono shrink-0">{(r.score).toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              )}
            </PipelineCard>

            <PipelineCard 
              title="6. LLM Generation" 
              icon={<Zap size={20}/>}
              isActive={activeStep >= 5}
              isCompleted={activeStep > 5}
              latency={queryResult?.generation?.latency_ms}
            >
              {queryResult && (
                <div className="bg-black/30 p-3 rounded-lg border border-white/5 mt-2 max-h-[300px] overflow-y-auto">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-[10px] bg-primary/20 text-primary px-2 py-1 rounded-full uppercase font-bold tracking-wider">
                      {queryResult.generation.provider}
                    </span>
                    <span className="text-[10px] bg-secondary text-secondary-foreground px-2 py-1 rounded-full">
                      {queryResult.generation.model}
                    </span>
                  </div>
                  <div className="prose prose-sm dark:prose-invert">
                    {queryResult.generation.content}
                  </div>
                </div>
              )}
            </PipelineCard>

          </div>

        </div>
      </main>
    </div>
  )
}

export default App
