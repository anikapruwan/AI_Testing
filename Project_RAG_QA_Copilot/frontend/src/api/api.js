import axios from 'axios'

const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Get stored API keys from localStorage
const getStoredKeys = () => ({
  groq_api_key: localStorage.getItem('groq_api_key') || null,
  opencode_api_key: localStorage.getItem('opencode_api_key') || null
})

// Settings endpoints
export const getSettings = async () => {
  const response = await api.get('/settings')
  return response.data
}

export const getModels = async () => {
  const response = await api.get('/models')
  return response.data
}

export const updateSettings = async (apiKeys, defaultModel) => {
  const response = await api.post('/settings', {
    api_keys: apiKeys,
    default_model: defaultModel
  })
  return response.data
}

export const validateKeys = async (groqKey, opencodeKey) => {
  const response = await api.post('/validate-keys', {
    groq_api_key: groqKey,
    opencode_api_key: opencodeKey
  })
  return response.data
}

// Chat endpoints
export const sendChat = async (message, model, sources) => {
  const keys = getStoredKeys()

  const response = await api.post('/chat/with-keys', {
    message,
    model,
    sources,
    groq_api_key: keys.groq_api_key,
    opencode_api_key: keys.opencode_api_key
  })

  return response.data
}

// Search endpoints
export const searchData = async (query, sources, topK = 5) => {
  const response = await api.post('/search', {
    query,
    sources,
    top_k: topK
  })
  return response.data
}

// Ingest endpoints
export const ingestCSV = async (sourcePath = null) => {
  const response = await api.post('/ingest/csv', { source_path: sourcePath })
  return response.data
}

export const ingestPDF = async (sourcePath = null) => {
  const response = await api.post('/ingest/pdf', { source_path: sourcePath })
  return response.data
}

export const ingestGitHub = async (repoUrl, token = null) => {
  const response = await api.post('/ingest/github', {
    repo_url: repoUrl,
    github_token: token
  })
  return response.data
}

export const rebuildIndex = async () => {
  const response = await api.post('/rebuild-index')
  return response.data
}

export const getCollections = async () => {
  const response = await api.get('/collections')
  return response.data
}

export const getSources = async () => {
  const response = await api.get('/sources')
  return response.data
}

export default api