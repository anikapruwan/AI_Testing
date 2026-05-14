import { useState, useRef, useEffect } from 'react'
import { sendChat } from '../api/api'

function ChatWidget({ models, settings }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I\'m your QA Search Bot assistant. I can help you with:\n\n• Answering questions about test cases\n• Generating new test cases\n• Debugging test failures\n• Searching documentation\n\nConfigure your API keys in Settings to get started!'
    }
  ])
  const [input, setInput] = useState('')
  const [selectedModel, setSelectedModel] = useState(settings?.default_model || 'llama-3.3-70b-versatile')
  const [sources, setSources] = useState(['test_cases', 'pdf_docs', 'code_base'])
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const groqKeySet = localStorage.getItem('groq_api_key')
  const opencodeKeySet = localStorage.getItem('opencode_api_key')
  const hasApiKey = groqKeySet || opencodeKeySet

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setLoading(true)

    setMessages(prev => [...prev, { role: 'user', content: userMessage }])

    setMessages(prev => [
      ...prev,
      { role: 'assistant', content: '', isTyping: true }
    ])

    try {
      const response = await sendChat(userMessage, selectedModel, sources)

      setMessages(prev => {
        const newMessages = prev.filter(m => !m.isTyping)
        return [
          ...newMessages,
          {
            role: 'assistant',
            content: response.message,
            sources: response.sources
          }
        ]
      })
    } catch (error) {
      setMessages(prev => {
        const newMessages = prev.filter(m => !m.isTyping)
        return [
          ...newMessages,
          {
            role: 'assistant',
            content: `Error: ${error.response?.data?.detail || error.message}`
          }
        ]
      })
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const toggleSource = (source) => {
    setSources(prev =>
      prev.includes(source)
        ? prev.filter(s => s !== source)
        : [...prev, source]
    )
  }

  const sourceLabels = {
    test_cases: 'Test Cases',
    pdf_docs: 'PDF Docs',
    code_base: 'GitHub Code'
  }

  return (
    <div className="chat-widget">
      <div className="chat-header">
        <h2>Chat with QA Bot</h2>
        <div className="model-selector">
          <label>Model:</label>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            disabled={!models || models.length === 0}
          >
            {models && models.length > 0 ? (
              models.map(model => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))
            ) : (
              <option value="">Loading...</option>
            )}
          </select>
        </div>
      </div>

      {!hasApiKey && (
        <div className="no-api-key">
          <p>⚠️ No API keys configured</p>
          <p>Please add your API keys in Settings to start chatting</p>
        </div>
      )}

      <div className="source-filters">
        {Object.entries(sourceLabels).map(([key, label]) => (
          <label key={key} className="source-checkbox">
            <input
              type="checkbox"
              checked={sources.includes(key)}
              onChange={() => toggleSource(key)}
            />
            {label}
          </label>
        ))}
      </div>

      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            {msg.isTyping ? (
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            ) : (
              <>
                {msg.content}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="message sources">
                    <strong>Sources:</strong>
                    {msg.sources.map((src, i) => (
                      <div key={i} className="source-item">
                        <strong>{sourceLabels[src.source] || src.source}</strong>
                        <br />
                        <small>{src.content?.substring(0, 200)}...</small>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <textarea
          className="chat-input"
          placeholder="Ask a question about your test cases, code, or documentation..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={loading}
          rows={1}
        />
        <button
          className="send-btn"
          onClick={handleSend}
          disabled={loading || !input.trim() || !hasApiKey}
        >
          {loading ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  )
}

export default ChatWidget