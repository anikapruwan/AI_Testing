# LinkedIn Auto-Poster — Command Code + ComfyUI Pipeline

Daily automated LinkedIn content generation using Command Code (headless) as the content brain, ComfyUI for open-source image generation, and LinkedIn API for publishing.

## Architecture

```
cron / systemd timer (daily 9 AM)
        │
        ▼
  run_daily.sh
        │
        ▼
  content_pipeline.py
        │
        ├──[1]── cmd -p "Generate today's post..."  ← Command Code (headless)
        │         returns JSON: {post_text, image_prompt, hashtags}
        │
        ├──[2]── ComfyUI API  ← Stable Diffusion XL (local, open source)
        │         prompt → generated image
        │
        └──[3]── LinkedIn API
                  image upload → post creation → published
```

## Prerequisites

| Component | Install |
|-----------|---------|
| Command Code | `npm i -g command-code && cmd login` |
| Python 3.10+ | `python3 --version` |
| ComfyUI | `git clone https://github.com/comfyanonymous/ComfyUI.git` |
| Stable Diffusion model | `sd_xl_base_1.0.safetensors` in `ComfyUI/models/checkpoints/` |
| LinkedIn App | Create at [linkedin.com/developers](https://linkedin.com/developers) |

### Python dependencies

```bash
pip install pyyaml
```

## Setup

### 1. LinkedIn Developer App

1. Go to [linkedin.com/developers](https://linkedin.com/developers) → Create App
2. Under Products, request **Share on LinkedIn** and **Sign In with LinkedIn**
3. Under Auth, add OAuth 2.0 scopes: `openid`, `profile`, `email`, `w_member_social`
4. Generate a 2-legged OAuth token or follow the 3-legged flow to get an access token
5. Find your Person URN at `GET https://api.linkedin.com/v2/userinfo`

### 2. ComfyUI

```bash
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
pip install -r requirements.txt

# Download SDXL base model
# Place in: ComfyUI/models/checkpoints/sd_xl_base_1.0.safetensors

python main.py --port 8188
```

Create a workflow JSON via the ComfyUI web UI (http://127.0.0.1:8188) with a KS sampler, SDXL checkpoint loader, and CLIP text encoder. Export as `workflow_sdxl.json` and place it in the pipeline directory.

### 3. Configure

```bash
cd pipeline
cp config.yaml config.local.yaml
```

Edit `config.local.yaml` with your values:

```yaml
linkedin:
  access_token: "AQV..."           # Your OAuth token
  person_urn: "urn:li:person:..."  # Your Person URN

comfyui:
  server_url: "http://127.0.0.1:8188"
  workflow_template: "workflow_sdxl.json"
```

### 4. Test

```bash
# Dry run — post to LinkedIn
./run_daily.sh --config config.local.yaml
```

### 5. Schedule

**systemd timer (recommended):**

```ini
# /etc/systemd/system/linkedin-poster.service
[Unit]
Description=LinkedIn Daily Post

[Service]
Type=oneshot
User=your-user
ExecStart=/path/to/pipeline/run_daily.sh --config=/path/to/pipeline/config.local.yaml
```

```ini
# /etc/systemd/system/linkedin-poster.timer
[Unit]
Description=Daily LinkedIn Post Timer

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
systemctl enable linkedin-poster.timer
systemctl start linkedin-poster.timer
```

**Or cron:**

```bash
0 9 * * * /path/to/pipeline/run_daily.sh --config=/path/to/pipeline/config.local.yaml
```

## File Structure

```
pipeline/
├── config.yaml              # Template config
├── config.local.yaml        # Your secrets (gitignored)
├── content_pipeline.py      # Main pipeline
├── run_daily.sh             # Cron/systemd entry point
├── workflow_sdxl.json       # ComfyUI workflow template
└── logs/
    ├── post_history.json    # All posts log
    └── post_2026-06-14.json # Per-post log
```

## Cost

| Component | Cost |
|-----------|------|
| Command Code | Your plan credits (free tier available) |
| ComfyUI + SDXL | Free (runs on your hardware) |
| LinkedIn API | Free |
| **Total** | **$0/month + electricity** |

## Troubleshooting

| Error | Fix |
|-------|-----|
| `cmd: command not found` | `npm i -g command-code` and ensure npm bin is in PATH |
| `cmd -p` returns no JSON | Increase `--max-turns` in config or simplify the prompt |
| ComfyUI timeout | Increase `timeout_seconds` in config. First run is slow (model loading) |
| LinkedIn 401 | Access token expired — regenerate via OAuth flow |
| LinkedIn 403 | Check scopes include `w_member_social` |
