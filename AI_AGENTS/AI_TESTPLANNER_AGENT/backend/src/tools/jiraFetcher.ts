import axios from 'axios';

export async function fetchJiraTicket(jiraId: string, url: string, email: string, token: string): Promise<any> {
    if (!url || !email || !token) throw new Error("Missing Jira credentials.");
    const apiUrl = `${url.replace(/\/$/, '')}/rest/api/2/issue/${jiraId}`;
    const auth = Buffer.from(`${email}:${token}`).toString('base64');
    
    try {
        const res = await axios.get(apiUrl, {
            headers: {
                "Authorization": `Basic ${auth}`,
                "Accept": "application/json"
            }
        });
        
        const summary = res.data.fields.summary || '';
        const desc = res.data.fields.description || '';
        return { summary, description: desc };
    } catch (e: any) {
        throw new Error(`Jira fetch failed: ${e.response?.data?.errorMessages || e.message}`);
    }
}

export async function testJiraConnection(url: string, email: string, token: string) {
    if (!url || !email || !token) return { success: false, msg: "Missing credentials" };
    const apiUrl = `${url.replace(/\/$/, '')}/rest/api/2/myself`;
    const auth = Buffer.from(`${email}:${token}`).toString('base64');
    try {
        await axios.get(apiUrl, { headers: { "Authorization": `Basic ${auth}` } });
        return { success: true, msg: "Connected to Jira!" };
    } catch (e: any) {
        return { success: false, msg: e.message };
    }
}
