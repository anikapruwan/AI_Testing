import express, { Request, Response } from 'express';
import cors from 'cors';
import fs from 'fs';
import path from 'path';
import { testJiraConnection, fetchJiraTicket } from './tools/jiraFetcher';
import { testLlmConnection, routeToLlm, buildPrompt } from './tools/llmRouter';
import { generateDocx } from './tools/docxGenerator';
import { generatePdf } from './tools/pdfGenerator';

const app = express();
app.use(cors());
app.use(express.json());

const PORT = 8000;
const ROOT_DIR = path.join(__dirname, '..', '..');
const SETTINGS_FILE = path.join(ROOT_DIR, '.env_settings.json');
const TMP_DIR = path.join(ROOT_DIR, '.tmp');

if (!fs.existsSync(TMP_DIR)) {
    fs.mkdirSync(TMP_DIR, { recursive: true });
}

interface Settings {
    jira_url: string;
    jira_email: string;
    jira_api_token: string;
    ollama_api_url: string;
    ollama_model: string;
    groq_api_key: string;
    groq_model: string;
    claude_api_key: string;
}

function loadSettings(): Settings {
    const defaults: Settings = {
        jira_url: "", jira_email: "", jira_api_token: "",
        ollama_api_url: "http://localhost:11434", ollama_model: "llama3",
        groq_api_key: "", groq_model: "llama-3.3-70b-versatile", claude_api_key: ""
    };
    if (fs.existsSync(SETTINGS_FILE)) {
        try {
            return { ...defaults, ...JSON.parse(fs.readFileSync(SETTINGS_FILE, 'utf-8')) };
        } catch {}
    }
    return defaults;
}

app.get('/api/settings', (req: Request, res: Response) => {
    res.json(loadSettings());
});

app.post('/api/settings', (req: Request, res: Response) => {
    fs.writeFileSync(SETTINGS_FILE, JSON.stringify(req.body, null, 2));
    res.json({ status: "success" });
});

app.post('/api/test-connection', async (req: Request, res: Response) => {
    const { provider } = req.body;
    const s = loadSettings();
    let success = false;
    let msg = "";

    if (provider === "jira") {
        const result = await testJiraConnection(s.jira_url, s.jira_email, s.jira_api_token);
        success = result.success; msg = result.msg;
    } else {
        const result = await testLlmConnection(provider, s.ollama_api_url, s.ollama_model, s.groq_api_key, s.groq_model, s.claude_api_key);
        success = result.success; msg = result.msg;
    }

    res.json({ status: success ? "success" : "error", message: msg });
});

app.post('/api/generate', async (req: Request, res: Response) => {
    try {
        const { jira_id, additional_context, llm_provider } = req.body;
        const s = loadSettings();

        console.log(`Fetching Jira ticket: ${jira_id}`);
        const context = await fetchJiraTicket(jira_id, s.jira_url, s.jira_email, s.jira_api_token);
        
        const prompt = buildPrompt(context, additional_context || "");
        
        console.log(`Routing prompt to ${llm_provider}`);
        const llmResponse = await routeToLlm(prompt, llm_provider, s.ollama_api_url, s.ollama_model, s.groq_api_key, s.groq_model, s.claude_api_key);

        const docxFilename = `testplan-${jira_id}.docx`;
        const pdfFilename = `testplan-${jira_id}.pdf`;

        await generateDocx(llmResponse, path.join(TMP_DIR, docxFilename));
        await generatePdf(llmResponse, path.join(TMP_DIR, pdfFilename));

        res.json({
            status: "success",
            message: "Generation completed successfully.",
            download_url: `/api/download/${docxFilename}`,
            download_url_pdf: `/api/download/${pdfFilename}`,
            preview_text: llmResponse
        });
    } catch (e: any) {
        console.error(e);
        res.status(500).json({ status: "error", message: e.message || "Unknown error" });
    }
});

app.get('/api/download/:filename', (req: Request, res: Response) => {
    const filename = decodeURIComponent(req.params.filename as string);
    const file = path.resolve(TMP_DIR, filename);
    console.log(`[DOWNLOAD] Requesting: ${file}`);
    if (fs.existsSync(file)) {
        res.download(file, filename, { dotfiles: 'allow' }, (err) => {
            if (err) {
                console.error(`[DOWNLOAD ERROR] Failed to send ${file}:`, err);
                if (!res.headersSent) res.status(500).send("Error downloading file");
            }
        });
    } else {
        console.error(`[DOWNLOAD ERORR] File doesn't exist: ${file}`);
        res.status(404).json({ detail: "File not found" });
    }
});

const FRONTEND_DIR = path.join(ROOT_DIR, 'frontend');
if (fs.existsSync(FRONTEND_DIR)) {
    app.use(express.static(FRONTEND_DIR));
}

app.listen(PORT, () => {
    console.log(`Express TS Backend running on http://127.0.0.1:${PORT}`);
});
