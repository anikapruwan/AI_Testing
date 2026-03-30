import { useState, useEffect } from 'react'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import './App.css'

function App() {
  const [showSettings, setShowSettings] = useState(false)
  const [settings, setSettings] = useState({
    jira_url: '', jira_email: '', jira_api_token: '',
    ollama_api_url: 'http://localhost:11434', ollama_model: 'llama3', groq_api_key: '', groq_model: 'llama-3.3-70b-versatile', claude_api_key: ''
  })
  
  const [jiraId, setJiraId] = useState('')
  const [contextInput, setContextInput] = useState('')
  const [provider, setProvider] = useState('groq')
  
  const [output, setOutput] = useState('<div style="color: #94a3b8; font-style: italic; text-align: center; margin-top: 20%;">Output Window</div>')
  const [isGenerating, setIsGenerating] = useState(false)
  const [downloadUrl, setDownloadUrl] = useState(null)
  const [downloadUrlPdf, setDownloadUrlPdf] = useState(null)
  const [history, setHistory] = useState([])
  const [statusMsg, setStatusMsg] = useState({ text: '', type: '' })

  useEffect(() => {
    fetch('/api/settings').then(r => r.json()).then(data => {
      if (data) setSettings(prev => ({ ...prev, ...data }))
    }).catch(e => console.error("Could not fetch settings", e))
  }, [])

  const handleSaveSettings = async () => {
    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      if(res.ok) {
        setStatusMsg({ text: 'Settings saved!', type: 'success-text' })
        setTimeout(() => setShowSettings(false), 1000)
      }
    } catch(e) {
      setStatusMsg({ text: 'Failed to save settings.', type: 'error-text' })
    }
  }

  const handleTestConnection = async (type) => {
    setStatusMsg({ text: 'Testing...', type: 'text-secondary' });
    await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
    }); // Auto-save first

    try {
      const res = await fetch('/api/test-connection', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: type })
      });
      const data = await res.json()
      setStatusMsg({ text: data.message, type: data.status === 'success' ? 'success-text' : 'error-text' })
    } catch(e) {
      setStatusMsg({ text: 'Network Error', type: 'error-text' })
    }
  }

  const handleGenerate = async () => {
    if(!jiraId) {
        setOutput('<span class="error-text">Please enter a Jira ID.</span>')
        return
    }

    setIsGenerating(true)
    setDownloadUrl(null)
    setDownloadUrlPdf(null)
    setOutput('<div style="text-align:center;"><div class="loader"></div> Generating Test Plan... this may take a minute.</div>')
    
    try {
      const res = await fetch('/api/generate', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jira_id: jiraId, additional_context: contextInput, llm_provider: provider })
      });
      const data = await res.json()
      
      if(res.ok && data.status === 'success') {
        const rawHtml = marked.parse(data.preview_text)
        const cleanHtml = DOMPurify.sanitize(rawHtml)
        setOutput(cleanHtml)
        setDownloadUrl(data.download_url)
        setDownloadUrlPdf(data.download_url_pdf)
        setHistory(h => ["Testplan for " + jiraId, ...h])
      } else {
        setOutput(`<span class="error-text">Error: ${data.message || data.detail || 'Unknown error'}</span>`)
      }
    } catch(e) {
      setOutput('<span class="error-text">Network Error: Could not connect to backend. Please ensure the backend is running.</span>')
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar glass">
        <button className="primary-btn" onClick={() => {setShowSettings(true); setStatusMsg({text:'', type:''})}}>⚙️ Settings</button>
        <div className="history-section">
          <h3>History</h3>
          <ul>
            {history.length === 0 ? <li className="history-item placeholder">No recent plans</li> : history.map((h, i) => <li key={i}>{h}</li>)}
          </ul>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content glass">
        <div className="output-window hide-scroll">
          <div dangerouslySetInnerHTML={{ __html: output }} />
        </div>

        <div className="input-section">
          <div className="input-row">
            <input type="text" placeholder="Enter Jira ID (e.g. PROJ-123)" className="glass-input" value={jiraId} onChange={e => setJiraId(e.target.value)} />
            <input type="text" placeholder="Additional prompt context..." className="glass-input flex-grow" value={contextInput} onChange={e => setContextInput(e.target.value)} />
          </div>
          
          <div className="action-row">
            <select className="glass-select" value={provider} onChange={e => setProvider(e.target.value)}>
              <option value="groq">Groq (Llama 3)</option>
              <option value="ollama">Ollama (Local)</option>
              <option value="claude">Claude (Anthropic)</option>
            </select>
            <button className="primary-btn action-btn" onClick={handleGenerate} disabled={isGenerating}>
                {isGenerating ? "Generating..." : "Generate"}
            </button>
            {downloadUrl && <a className="secondary-btn action-btn" href={downloadUrl} download style={{textAlign: 'center', textDecoration: 'none', lineHeight: '20px'}}>📥 Download<br/>DOCX</a>}
            {downloadUrlPdf && <a className="primary-btn action-btn" href={downloadUrlPdf} download style={{background: '#e11d48', textAlign: 'center', textDecoration: 'none', lineHeight: '20px'}}>📥 Download<br/>PDF</a>}
          </div>
        </div>
      </main>

      {/* Settings Modal */}
      {showSettings && (
        <div className="modal">
          <div className="modal-content glass">
            <div className="modal-header">
              <button className="icon-btn" onClick={() => setShowSettings(false)}>⬅</button>
              <h2>Settings</h2>
            </div>
            
            <div className="settings-form">
              <div className="form-group"><label>Jira Domain URL</label><input type="text" value={settings.jira_url} onChange={e => setSettings({...settings, jira_url: e.target.value})} placeholder="https://your-domain.atlassian.net" /></div>
              <div className="form-group"><label>Jira Email</label><input type="email" value={settings.jira_email} onChange={e => setSettings({...settings, jira_email: e.target.value})} placeholder="user@example.com" /></div>
              <div className="form-group"><label>Jira API Token</label><input type="password" value={settings.jira_api_token} onChange={e => setSettings({...settings, jira_api_token: e.target.value})} /></div>
              <div className="form-group test-btn-group"><button className="secondary-btn" onClick={() => handleTestConnection('jira')}>Test Jira</button></div>
              <hr />
              
              <div className="form-group"><label>Ollama API URL</label><input type="text" value={settings.ollama_api_url} onChange={e => setSettings({...settings, ollama_api_url: e.target.value})} /></div>
              <div className="form-group"><label>Ollama Model Name</label><input type="text" value={settings.ollama_model} onChange={e => setSettings({...settings, ollama_model: e.target.value})} placeholder="e.g. llama3, mistral" /></div>
              <div className="form-group test-btn-group"><button className="secondary-btn" onClick={() => handleTestConnection('ollama')}>Test Ollama</button></div>
              <hr />
              
              <div className="form-group"><label>Groq API Key</label><input type="password" value={settings.groq_api_key} onChange={e => setSettings({...settings, groq_api_key: e.target.value})} /></div>
              <div className="form-group"><label>Groq Model Name</label><input type="text" value={settings.groq_model} onChange={e => setSettings({...settings, groq_model: e.target.value})} placeholder="e.g. llama-3.3-70b-versatile" /></div>
              <div className="form-group test-btn-group"><button className="secondary-btn" onClick={() => handleTestConnection('groq')}>Test Groq</button></div>
              <hr />
              
              <div className="form-group"><label>Claude API Key</label><input type="password" value={settings.claude_api_key} onChange={e => setSettings({...settings, claude_api_key: e.target.value})} /></div>
              <div className="form-group test-btn-group"><button className="secondary-btn" onClick={() => handleTestConnection('claude')}>Test Claude</button></div>
              
              <div className="modal-footer">
                <span className={`status-msg ${statusMsg.type}`}>{statusMsg.text}</span>
                <button className="primary-btn" onClick={handleSaveSettings}>Save</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
