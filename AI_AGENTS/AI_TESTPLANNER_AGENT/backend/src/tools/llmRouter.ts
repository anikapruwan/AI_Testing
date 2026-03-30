import axios from 'axios';
import fs from 'fs';
import path from 'path';

export function buildPrompt(jiraContext: any, additionalContext: string): string {
    const summary = jiraContext.summary || "N/A";
    const desc = jiraContext.description || "N/A";
    
    const promptPath = path.join(__dirname, '..', '..', '..', 'Testplan_Template', 'prompt.md');
    let basePrompt = "You are an expert QA Engineer. Generate a Test Plan based on the Jira ticket.";
    
    if (fs.existsSync(promptPath)) {
        basePrompt = fs.readFileSync(promptPath, 'utf-8');
    }
    
    return `${basePrompt}\n\n---\nCURRENT JIRA TICKET INFORMATION:\nSummary: ${summary}\nDescription: ${desc}\n\nADDITIONAL USER CONTEXT:\n${additionalContext}\n\nIMPORTANT: Please base your output specifically on the above Current Jira Ticket Information, supplementing the instructions and expectations mentioned earlier. Ensure the output is clean Markdown format. Do NOT output any conversational text.`;
}

export async function routeToLlm(prompt: string, provider: string, ollamaUrl: string, ollamaModel: string, groqKey: string, groqModel: string, claudeKey: string): Promise<string> {
    if (provider === 'ollama') {
        const url = `${ollamaUrl.replace(/\/$/, '')}/api/generate`;
        const res = await axios.post(url, {
            model: ollamaModel || "llama3", prompt, stream: false
        }, { timeout: 600000 });
        return res.data.response || "";
    } else if (provider === 'groq') {
        const res = await axios.post("https://api.groq.com/openai/v1/chat/completions", {
            model: groqModel || "llama-3.3-70b-versatile",
            messages: [{ role: "user", content: prompt }]
        }, { headers: { "Authorization": `Bearer ${groqKey}` }, timeout: 600000 });
        return res.data.choices[0].message.content;
    } else if (provider === 'claude') {
        const res = await axios.post("https://api.anthropic.com/v1/messages", {
            model: "claude-3-haiku-20240307", max_tokens: 4096,
            messages: [{ role: "user", content: prompt }]
        }, { headers: { "x-api-key": claudeKey, "anthropic-version": "2023-06-01" }, timeout: 600000 });
        return res.data.content[0].text;
    }
    throw new Error(`Unknown LLM provider: ${provider}`);
}

export async function testLlmConnection(provider: string, ollamaUrl: string, ollamaModel: string, groqKey: string, groqModel: string, claudeKey: string) {
    try {
        await routeToLlm("Respond with 'OK'", provider, ollamaUrl, ollamaModel, groqKey, groqModel, claudeKey);
        return { success: true, msg: `${provider.charAt(0).toUpperCase() + provider.slice(1)} connected successfully.` };
    } catch (e: any) {
        return { success: false, msg: `${provider} error: ${e.response?.data?.error?.message || e.message}` };
    }
}
