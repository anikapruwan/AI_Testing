import { useState } from 'react';
import './App.css';

interface HistoryItem {
  id: string;
  requirement: string;
  testCases: string;
  timestamp: Date;
  provider: string;
}

function App() {
  const [activeTab, setActiveTab] = useState<'generator' | 'settings'>('generator');
  
  // State for LLM settings // Changed to 127.0.0.1 for Node 18+ IPv4 resolution
  const [ollamaUrl, setOllamaUrl] = useState('http://127.0.0.1:11434');
  const [groqKey, setGroqKey] = useState('');
  const [openAiKey, setOpenAiKey] = useState('');

  // State for Generator
  const [llmProvider, setLlmProvider] = useState('ollama');
  const [requirement, setRequirement] = useState('');
  const [generatedCases, setGeneratedCases] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  // States for Connections Tests
  const [testResults, setTestResults] = useState<Record<string, {success: boolean, message: string}>>({});
  const [testingProvider, setTestingProvider] = useState<string | null>(null);

  // State for History
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [selectedHistoryId, setSelectedHistoryId] = useState<string | null>(null);

  const handleTestConnection = async (providerToTest: string) => {
    setTestingProvider(providerToTest);
    setTestResults(prev => ({ ...prev, [providerToTest]: { success: false, message: 'Testing...' } }));
    
    try {
      const response = await fetch('http://localhost:3001/api/test-connection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: providerToTest,
          settings: { ollamaUrl, groqKey, openAiKey }
        }),
      });
      const data = await response.json();
      setTestResults(prev => ({ 
        ...prev, 
        [providerToTest]: { success: data.success, message: data.message } 
      }));
    } catch (error) {
      setTestResults(prev => ({ 
        ...prev, 
        [providerToTest]: { success: false, message: 'Failed to reach backend server.' } 
      }));
    } finally {
      setTestingProvider(null);
    }
  };

  const handleGenerate = async () => {
    if (!requirement.trim()) return;
    setIsGenerating(true);
    try {
      // In advanced implementation, we pass settings directly to backend or rely on backend env 
      // For now, we'll assume the backend handles the generation with the URL and keys
      const response = await fetch('http://localhost:3001/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          requirement,
          provider: llmProvider,
          settings: {
            ollamaUrl,
            groqKey,
            openAiKey
          }
        }),
      });
      const data = await response.json();
      if (data.success) {
        setGeneratedCases(data.testCases);
        
        // Add to history
        const newHistoryItem: HistoryItem = {
          id: Date.now().toString(),
          requirement,
          testCases: data.testCases,
          timestamp: new Date(),
          provider: llmProvider
        };
        setHistory(prev => [newHistoryItem, ...prev]);
        setSelectedHistoryId(newHistoryItem.id);
      } else {
        setGeneratedCases(`Error: ${data.message}`);
      }
    } catch (error) {
      setGeneratedCases('Failed to connect to generator API.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar for Navigation / History */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2>QA Gen App</h2>
        </div>
        <nav className="sidebar-nav">
          <button 
            className={(activeTab === 'generator' && !selectedHistoryId) ? 'active' : ''} 
            onClick={() => {
              setActiveTab('generator');
              setSelectedHistoryId(null);
            }}
          >
            Generator
          </button>
          <button 
            className={activeTab === 'settings' ? 'active' : ''} 
            onClick={() => {
              setActiveTab('settings');
              setSelectedHistoryId(null);
            }}
          >
            Settings
          </button>
        </nav>
        <div className="history-section">
          <h3>History</h3>
          <div className="history-list">
            {history.length === 0 ? (
              <p className="history-placeholder">No history yet.</p>
            ) : (
              history.map(item => (
                <div 
                  key={item.id} 
                  className={`history-item ${selectedHistoryId === item.id ? 'selected' : ''}`}
                  onClick={() => {
                    setActiveTab('generator');
                    setSelectedHistoryId(item.id);
                  }}
                >
                  <p className="history-req" title={item.requirement}>
                    {item.requirement.length > 30 ? item.requirement.substring(0, 30) + '...' : item.requirement}
                  </p>
                  <span className="history-meta">{item.provider} • {item.timestamp.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        {activeTab === 'generator' && (
          <div className="generator-view">
            <header className="view-header">
              <h1>
                {selectedHistoryId ? 'Past Generation' : 'Test Case Generator'}
              </h1>
              <p>Generated with {selectedHistoryId 
                  ? history.find(h => h.id === selectedHistoryId)?.provider 
                  : 'Ollama API / Groq / OpenAI'}
              </p>
            </header>
            
            <div className="output-container">
              {selectedHistoryId ? (
                <pre className="generated-output">
                  {history.find(h => h.id === selectedHistoryId)?.testCases}
                </pre>
              ) : generatedCases ? (
                <pre className="generated-output">{generatedCases}</pre>
              ) : (
                <div className="placeholder-output">
                  <p>Your generated Jira test cases will appear here.</p>
                </div>
              )}
            </div>

            {!selectedHistoryId && (
              <div className="input-container">
                <textarea 
                  className="requirement-input" 
                  placeholder="Ask here is here TC for Requirement..."
                  value={requirement}
                  onChange={(e) => setRequirement(e.target.value)}
                />
              <select 
                className="provider-select"
                value={llmProvider}
                onChange={(e) => setLlmProvider(e.target.value)}
              >
                <option value="ollama">Ollama</option>
                <option value="groq">Groq</option>
                <option value="openai">OpenAI</option>
              </select>
              <button 
                className="generate-btn" 
                onClick={handleGenerate}
                disabled={isGenerating || !requirement.trim()}
              >
                {isGenerating ? 'Generating...' : 'Generate'}
              </button>
              </div>
            )}
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="settings-view">
             <header className="view-header">
              <h1>API Settings</h1>
            </header>
            
            <div className="settings-form">
              <div className="form-group">
                <label>Ollama API URL</label>
                <div className="input-with-button">
                  <input 
                    type="text" 
                    value={ollamaUrl} 
                    onChange={(e) => setOllamaUrl(e.target.value)} 
                    placeholder="http://127.0.0.1:11434"
                  />
                  <button 
                    className="test-inline-btn"
                    onClick={() => handleTestConnection('ollama')}
                    disabled={testingProvider === 'ollama'}
                  >
                    {testingProvider === 'ollama' ? 'Testing...' : 'Test'}
                  </button>
                </div>
                {testResults['ollama'] && testResults['ollama'].message !== 'Testing...' && (
                  <div className={`test-feedback ${testResults['ollama'].success ? 'success' : 'error'}`}>
                    {testResults['ollama'].message}
                  </div>
                )}
              </div>

              <div className="form-group">
                <label>Groq API Key</label>
                <div className="input-with-button">
                  <input 
                    type="password" 
                    value={groqKey} 
                    onChange={(e) => setGroqKey(e.target.value)} 
                    placeholder="gsk_..."
                  />
                  <button 
                    className="test-inline-btn"
                    onClick={() => handleTestConnection('groq')}
                    disabled={testingProvider === 'groq'}
                  >
                    {testingProvider === 'groq' ? 'Testing...' : 'Test'}
                  </button>
                </div>
                {testResults['groq'] && testResults['groq'].message !== 'Testing...' && (
                  <div className={`test-feedback ${testResults['groq'].success ? 'success' : 'error'}`}>
                    {testResults['groq'].message}
                  </div>
                )}
              </div>

              <div className="form-group">
                <label>OpenAI API Key</label>
                <div className="input-with-button">
                  <input 
                    type="password" 
                    value={openAiKey} 
                    onChange={(e) => setOpenAiKey(e.target.value)} 
                    placeholder="sk-..."
                  />
                  <button 
                    className="test-inline-btn"
                    onClick={() => handleTestConnection('openai')}
                    disabled={testingProvider === 'openai'}
                  >
                    {testingProvider === 'openai' ? 'Testing...' : 'Test'}
                  </button>
                </div>
                {testResults['openai'] && testResults['openai'].message !== 'Testing...' && (
                  <div className={`test-feedback ${testResults['openai'].success ? 'success' : 'error'}`}>
                    {testResults['openai'].message}
                  </div>
                )}
              </div>

              <div className="settings-actions">
                <button className="save-btn">Save Settings</button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
