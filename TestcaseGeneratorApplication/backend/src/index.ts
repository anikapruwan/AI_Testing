import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import axios from 'axios';
import { OpenAI } from 'openai';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

const systemPrompt = `You are an expert QA Engineer. Generate comprehensive test cases (both functional and non-functional) for the user's requirement.
You MUST format your output beautifully as Jira Tasks/Stories. Use Jira markdown structure if applicable.
Include the following in your output for EACH test case:
- Summary: [A clear, concise title]
- Description: [Detailed explanation]
- Preconditions: [What needs to be set up]
- Steps to Reproduce: [1...2...3...]
- Expected Result: [What should happen]
- Priority/Severity: [e.g., High, Medium, Low]
- Test Type: [Functional / Non-functional / API / UI]

Respond ONLY with the test cases. Do not include introductory text.`;

app.post('/api/generate', async (req, res) => {
  const { requirement, provider, settings } = req.body;

  try {
    let testCases = '';

    if (provider === 'ollama') {
      const ollamaUrl = (settings.ollamaUrl || 'http://127.0.0.1:11434').replace('localhost', '127.0.0.1');
      const prompt = `${systemPrompt}\n\nRequirement:\n${requirement}`;
      
      // Fetch available models first to avoid 404s
      const tagsResponse = await axios.get(`${ollamaUrl}/api/tags`);
      const models = tagsResponse.data.models;
      if (!models || models.length === 0) {
        return res.status(400).json({ success: false, message: 'No models are currently installed in your local Ollama instance. Please pull a model first.' });
      }
      
      const targetModel = models[0].name; // Use the first available model

      const response = await axios.post(`${ollamaUrl}/api/generate`, {
        model: targetModel,
        prompt: prompt,
        stream: false
      }, {
        headers: { 'Content-Type': 'application/json' }
      });
      
      testCases = response.data.response;
    } 
    
    else if (provider === 'groq') {
      if (!settings.groqKey) {
        return res.status(400).json({ success: false, message: 'Groq API Key is missing.' });
      }
      const groqClient = new OpenAI({
        apiKey: settings.groqKey,
        baseURL: 'https://api.groq.com/openai/v1',
      });
      const response = await groqClient.chat.completions.create({
        model: 'openai/gpt-oss-120b', // Updated per user request and official Groq ID
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: requirement }
        ],
      });
      testCases = response.choices[0].message.content || '';
    } 
    
    else if (provider === 'openai') {
      if (!settings.openAiKey) {
        return res.status(400).json({ success: false, message: 'OpenAI API Key is missing.' });
      }
      const openai = new OpenAI({ apiKey: settings.openAiKey });
      const response = await openai.chat.completions.create({
        model: 'gpt-3.5-turbo',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: requirement }
        ],
      });
      testCases = response.choices[0].message.content || '';
    } 
    
    else {
      return res.status(400).json({ success: false, message: 'Invalid LLM Provider selected.' });
    }

    res.json({ success: true, testCases });

  } catch (error: any) {
    console.error('Generation error:', error.message || error);
    res.status(500).json({ success: false, message: error.message || 'Error occurred during generation.' });
  }
});

app.post('/api/test-connection', async (req, res) => {
  const { provider, settings } = req.body;
  try {
    if (provider === 'ollama') {
      const ollamaUrl = (settings.ollamaUrl || 'http://127.0.0.1:11434').replace('localhost', '127.0.0.1');
      // Simple fetch to confirm Ollama is reachable
      await axios.get(`${ollamaUrl}/api/tags`);
      return res.json({ success: true, message: 'Ollama connection successful!' });
    } 
    else if (provider === 'groq') {
       if (!settings.groqKey) return res.status(400).json({ success: false, message: 'Groq API Key is missing.' });
       const groqClient = new OpenAI({ apiKey: settings.groqKey, baseURL: 'https://api.groq.com/openai/v1' });
       // Check if the key works AND if the specified model is valid
       const modelsResponse = await groqClient.models.list();
       
       const targetModel = 'openai/gpt-oss-120b';
       const availableModels = modelsResponse.data.map(m => m.id);
       
       if (!availableModels.includes(targetModel)) {
         // Optionally, try to find a close match if they made a typo (like gpt instead of gtp)
         const closeMatch = availableModels.find(id => id.includes('gpt') || id.includes('120b'));
         if (closeMatch) {
            return res.status(400).json({ success: false, message: `Connected to Groq successfully, but model '${targetModel}' was not found. Did you mean '${closeMatch}'?` });
         }
         return res.status(400).json({ success: false, message: `Connected successfully, but model '${targetModel}' is not supported by your Groq API.` });
       }

       return res.json({ success: true, message: `Groq connection successful! Model ${targetModel} is valid.` });
    }
    else if (provider === 'openai') {
       if (!settings.openAiKey) return res.status(400).json({ success: false, message: 'OpenAI API Key is missing.' });
       const openai = new OpenAI({ apiKey: settings.openAiKey });
       // Minimal ping to models list
       await openai.models.list();
       return res.json({ success: true, message: 'OpenAI connection successful!' });
    }
    
    return res.status(400).json({ success: false, message: 'Invalid LLM Provider selected for ping.' });
  } catch (error: any) {
    console.error('Test connection error:', error.message || error);
    res.status(500).json({ success: false, message: `Connection failed: ${error.message || 'Unknown error'}` });
  }
});

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', message: 'Test Case Generator API is running' });
});

app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
