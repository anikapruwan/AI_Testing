# QA Copilot — Deploy on a DigitalOcean Droplet

A Streamlit app that routes a QA request to one of three production LangChain agents:
**bug triage**, **root-cause analysis (RCA)**, and **test design** — with graceful
fallback to pasted text / dummy data when JIRA, Jenkins, or the RAG KB are not reachable.

These steps are copy-paste ready (Ubuntu 22.04/24.04 droplet). Run them in order.

---

## 0. Prerequisites

- A DigitalOcean droplet (Ubuntu, ≥ 1 GB RAM), SSH access as a sudo user.
- A **Groq API key** — https://console.groq.com/keys (this is the only *required* secret).
- Everything else (JIRA, Jenkins, GitHub token, Ollama/RAG) is **optional**: if absent,
  that feature falls back to pasted text or a built-in dummy sample and the app still runs.

---

## 1. Install system packages

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git
python3 --version   # expect 3.10+ (developed on 3.12)
```

---

## 2. Clone the repository

```bash
cd ~
git clone https://github.com/PramodDutta/AITesterBlueprint2x.git
cd AITesterBlueprint2x/Chapter_21_LangChain
```

---

## 3. Create a virtualenv and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Set up environment variables (`.env`)

Create `Chapter_21_LangChain/.env`. Only `GROQ_API_KEY` + `LLM_MODEL` are required;
the rest enable the "real" data sources and otherwise fall back automatically.

```bash
cat > .env <<'EOF'
# ---- REQUIRED ----
GROQ_API_KEY=gsk_your_groq_key_here
LLM_MODEL=openai/gpt-oss-120b          # triage needs a json_schema-capable Groq model
ROUTER_MODEL=llama-3.3-70b-versatile   # small model used only to classify requests

# ---- JIRA (triage + test design from a ticket; else paste text in the UI) ----
JIRA_URL=https://your-org.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=your_atlassian_api_token   # id.atlassian.com/manage-profile/security/api-tokens

# ---- RCA sources (all optional; each self-falls-back) ----
JENKINS_URL=http://localhost:8080         # local Jenkins usually NOT reachable in prod ->
JENKINS_JOB=AdvancePlaywrightFramework1x  # the tool returns a sample log automatically
JENKINS_BUILD=lastBuild
JENKINS_USER=admin
JENKINS_TOKEN=admin
GITHUB_REPO=PramodDutta/AdvancePlaywrightFramework1x   # public repo -> works with no token
# GITHUB_TOKEN=ghp_...                    # optional, only raises the rate limit
HEALTH_URL=https://app.thetestingacademy.com/playwright/ttacart/

# ---- RAG embeddings (optional; if Ollama absent, RAG returns empty context) ----
OLLAMA_URL=http://localhost:11434
EMBED_MODEL=nomic-embed-text
EOF
```

Edit the placeholders (`GROQ_API_KEY`, JIRA values) with real values.

> **The `.env` is gitignored** — it is never committed. Set it on the server directly.

---

## 5. (Optional) Build the RAG knowledge base

Only needed if you want triage/design **grounded in prior VWO test cases**. Requires Ollama.
Skip this whole step and the app still runs (RAG just returns empty context → fallback).

```bash
# install + start Ollama, pull the embedding model
curl -fsSL https://ollama.com/install.sh | sh
ollama pull nomic-embed-text

# generate sample data + build the local Chroma KB
python data/generate_dummy_data.py
python -m rag.ingest
```

---

## 6. Open the firewall for the app port

```bash
sudo ufw allow 8610/tcp     # if ufw is enabled
```

Also add an inbound rule for TCP **8610** in the DigitalOcean cloud firewall if you use one.

---

## 7. Run the app

```bash
# from Chapter_21_LangChain/ with the venv active
streamlit run src/QACopilot_Final/qa_copilot_ui.py \
  --server.port 8610 \
  --server.address 0.0.0.0 \
  --server.headless true
```

Open **http://YOUR_DROPLET_IP:8610** in a browser.

### Run it detached (survives your SSH session)

```bash
nohup streamlit run src/QACopilot_Final/qa_copilot_ui.py \
  --server.port 8610 --server.address 0.0.0.0 --server.headless true \
  > ~/qa_copilot.log 2>&1 &
echo "started; logs -> ~/qa_copilot.log"
```

### (Optional) Run as a systemd service

```bash
sudo tee /etc/systemd/system/qa-copilot.service >/dev/null <<EOF
[Unit]
Description=QA Copilot (Streamlit)
After=network.target

[Service]
User=$USER
WorkingDirectory=$HOME/AITesterBlueprint2x/Chapter_21_LangChain
ExecStart=$HOME/AITesterBlueprint2x/Chapter_21_LangChain/.venv/bin/streamlit run src/QACopilot_Final/qa_copilot_ui.py --server.port 8610 --server.address 0.0.0.0 --server.headless true
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now qa-copilot
sudo systemctl status qa-copilot --no-pager
```

---

## 8. Verify

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8610/    # expect 200
```

In the browser:
- **Auto-route** — type any request; the router picks triage / RCA / design.
- **Bug Triage / Test Design** — enter a JIRA key (e.g. `VWO-105`) or paste text.
- **Root-Cause Analysis** — ask a question; it pings Jenkins/GitHub/health (dummy fallback).

---

## Command-line alternative (no UI)

```bash
python src/QACopilot_Final/qa_copilot.py   # runs the 3 sample requests through the router
```

---

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| `400 tool_use_failed … expected boolean` on triage | `LLM_MODEL` is not json-schema-capable. Use `openai/gpt-oss-120b` (not `llama-3.1-8b-instant`). |
| RCA says `[FALLBACK — live Jenkins unavailable …]` | Expected in prod — Jenkins is on localhost; the tool uses a sample log so RCA still works. |
| Triage/design show `fallback · pasted text` | JIRA not configured/reachable — paste the report/story in the UI instead. |
| RAG context is empty | Ollama not running or KB not built (Step 5). App still works without it. |
| Page not reachable from outside | Open TCP 8610 in `ufw` **and** the DigitalOcean cloud firewall; bind `--server.address 0.0.0.0`. |
