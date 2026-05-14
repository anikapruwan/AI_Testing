import { useState, useEffect } from 'react'
import { updateSettings, validateKeys, getSettings } from '../api/api'

function SettingsModal({ isOpen, onClose, models, currentSettings }) {
  const [groqKey, setGroqKey] = useState('')
  const [opencodeKey, setOpencodeKey] = useState('')
  const [defaultModel, setDefaultModel] = useState('llama-3.3-70b-versatile')
  const [saving, setSaving] = useState(false)
  const [validationStatus, setValidationStatus] = useState({})
  const [error, setError] = useState('')

  useEffect(() => {
    if (isOpen) {
      const storedGroq = localStorage.getItem('groq_api_key')
      const storedOpencode = localStorage.getItem('opencode_api_key')
      setGroqKey(storedGroq || '')
      setOpencodeKey(storedOpencode || '')
      setDefaultModel(currentSettings?.default_model || 'llama-3.3-70b-versatile')
    }
  }, [isOpen, currentSettings])

  const handleValidate = async () => {
    setError('')
    setValidationStatus({})

    if (!groqKey && !opencodeKey) {
      setError('At least one API key is required.')
      return
    }

    try {
      const result = await validateKeys(
        groqKey || null,
        opencodeKey || null
      )

      setValidationStatus({
        groq: result.groq_valid,
        opencode: result.opencode_valid
      })

      const errors = []
      if (groqKey && !result.groq_valid) errors.push('Groq')
      if (opencodeKey && !result.opencode_valid) errors.push('OpenCode')

      if (errors.length > 0) {
        if (errors.length === 2) {
          setError('Both API keys are invalid. Please check and try again.')
        } else {
          setError(`The provided ${errors[0]} API key is invalid.`)
        }
      } else {
        if (!result.groq_valid && !result.opencode_valid) {
          setError('Please provide at least one valid API key.')
        }
      }
    } catch (err) {
      let errorMessage = 'Failed to validate keys. Please try again.'
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          errorMessage = err.response.data.detail[0].msg
        } else {
          errorMessage = err.response.data.detail
        }
      }
      setError(errorMessage)
    }
  }

  const handleSave = async () => {
    if (!groqKey && !opencodeKey) {
      setError('At least one API key is required.')
      return
    }

    setSaving(true)
    setError('')

    try {
      if (groqKey) {
        localStorage.setItem('groq_api_key', groqKey)
      } else {
        localStorage.removeItem('groq_api_key')
      }

      if (opencodeKey) {
        localStorage.setItem('opencode_api_key', opencodeKey)
      } else {
        localStorage.removeItem('opencode_api_key')
      }

      await updateSettings(
        {
          groq_api_key: groqKey || null,
          opencode_api_key: opencodeKey || null
        },
        defaultModel
      )

      onClose()
    } catch (err) {
      let errorMessage = 'Failed to save settings'
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          errorMessage = err.response.data.detail[0].msg
        } else {
          errorMessage = err.response.data.detail
        }
      }
      setError(errorMessage)
    } finally {
      setSaving(false)
    }
  }

  if (!isOpen) return null

  const groqKeySet = groqKey.length > 0
  const opencodeKeySet = opencodeKey.length > 0

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Settings</h3>
          <button className="modal-close" onClick={onClose}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <div className="modal-body">
          <div className="form-group">
            <label>Groq API Key</label>
            <input
              type="password"
              value={groqKey}
              onChange={(e) => setGroqKey(e.target.value)}
              placeholder="gsk_..."
            />
            <div className="form-hint">
              Get your API key from <a href="https://console.groq.com" target="_blank" rel="noopener">groq.com</a>
            </div>
            {groqKeySet && (
              <div className="api-key-status">
                <span className={`status-dot ${validationStatus.groq ? 'set' : 'not-set'}`}></span>
                {validationStatus.groq ? 'Valid' : 'Not validated'}
              </div>
            )}
          </div>

          <div className="form-group">
            <label>OpenCode API Key</label>
            <input
              type="password"
              value={opencodeKey}
              onChange={(e) => setOpencodeKey(e.target.value)}
              placeholder="sk-..."
            />
            <div className="form-hint">
              Get your API key from <a href="https://platform.opencode.ai" target="_blank" rel="noopener">opencode.ai</a>
            </div>
            {opencodeKeySet && (
              <div className="api-key-status">
                <span className={`status-dot ${validationStatus.opencode ? 'set' : 'not-set'}`}></span>
                {validationStatus.opencode ? 'Valid' : 'Not validated'}
              </div>
            )}
          </div>

          <div className="form-group">
            <label>Default Model</label>
            <select
              value={defaultModel}
              onChange={(e) => setDefaultModel(e.target.value)}
              disabled={!models || models.length === 0}
            >
              {models && models.length > 0 ? (
                models.map(model => (
                  <option key={model.id} value={model.id}>
                    {model.name}
                  </option>
                ))
              ) : (
                <option value="">Loading models...</option>
              )}
            </select>
            <div className="form-hint">
              This model will be selected by default in the chat
            </div>
          </div>

          {error && (
            <div className="form-group" style={{ color: 'var(--error)' }}>
              {error}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={handleValidate}>
            Validate Keys
          </button>
          <button
            className="btn-primary"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default SettingsModal