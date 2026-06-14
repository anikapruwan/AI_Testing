# Recommended Tool Stack — Vibe-Coded LinkedIn Automation

## Selection Philosophy

Each tool was chosen based on three criteria:
1. **API accessibility** — Must have a well-documented REST API that works from n8n HTTP Request nodes
2. **Cost-effectiveness** — Free tier or pay-as-you-go pricing fits solo operators and small teams
3. **Vibe-code compatibility** — Natural language prompts drive the tool, not complex configuration

---

## 1. Orchestration / Integration

| Tool | Why | Pricing |
|------|-----|---------|
| **n8n (Self-Hosted)** ⭐ | Full visual workflow builder. Cron triggers built in. No vendor lock-in. Runs on a $6/month VPS or free on Railway. 400+ native integrations. JSON/Function nodes handle any custom logic. | Free (self-hosted) / Cloud from €20/month |

**Why not Make.com or Zapier?** n8n's self-hosted option means unlimited workflow runs at zero monthly cost. Zapier charges per task — this workflow runs 30+ times/month minimum. Make.com is a solid second choice if you prefer a managed service.

**Setup:**
```bash
# One-command deploy on Railway or Render
docker run -d --name n8n -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  -e N8N_SECURE_COOKIE=false \
  n8nio/n8n
```

---

## 2. Content Generation (LLM)

| Tool | Why | Pricing |
|------|-----|---------|
| **Google Gemini 1.5 Pro** ⭐ | Free tier gives 1,500 requests/day. Handles structured JSON output reliably. Excellent at following format constraints (character limits, hashtag counts). No credit card required to start. | Free: 1,500 req/day / Paid: $3.50 per 1M input tokens |

**Why not GPT-4o or Claude?** Gemini's free tier is unmatched at this volume. 30 posts/month with ~500 tokens each is completely free. OpenAI and Anthropic have no sustainable free tier for daily production use.

**If budget allows (for higher quality):**
- **Claude 3.5 Sonnet** via Anthropic API — Better tone and nuance, $3/$15 per 1M input/output tokens
- **OpenAI GPT-4o** — Broadest ecosystem support, $5/$15 per 1M input/output tokens

**API endpoint:**
```
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent
```

---

## 3. Image Generation

| Tool | Why | Pricing |
|------|-----|---------|
| **Leonardo AI** ⭐ | API-native from day one. Cinematic/photorealistic models (Leonardo Diffusion XL, Phoenix). Returns images via URL — no file management needed. Generous free tier. | Free: 150 credits/day / Paid: from $12/month |

**Alternatives:**

| Tool | When to Use | Pricing |
|------|-------------|---------|
| **Stability AI (Replicate)** | If you need SDXL/SD3 with fine-grained control. Replicate handles GPU infra. | ~$0.002 per image |
| **DALL-E 3 (OpenAI)** | Simplest integration if you already use OpenAI for text. Consistent quality. | $0.04 per image |
| **Midjourney** | Best image quality, but no API. Requires Discord bot workaround via `/imagine`. Only viable if click-ops acceptable. | From $10/month |

**Leonardo API endpoint:**
```
POST https://cloud.leonardo.ai/api/rest/v1/generations
```

---

## 4. Publishing (LinkedIn)

| Tool | Why | Pricing |
|------|-----|---------|
| **LinkedIn API (Direct)** ⭐ | Complete control. Posts with images, carousels, and video. No intermediary costs. The only way to truly automate content publishing. | Free (requires LinkedIn app registration) |

**Why not a scheduler like Buffer or Hootsuite?** Scheduling tools let you queue posts but still require manual creation. The LinkedIn API is the only path to fully automated, hands-off publishing. You need to:

1. Create a LinkedIn Developer App at [linkedin.com/developers](https://linkedin.com/developers)
2. Request the following OAuth 2.0 scopes: `openid`, `profile`, `email`, `w_member_social`
3. Generate a 60-day access token (refresh before expiry)
4. Post via `POST https://api.linkedin.com/rest/posts`

**Note:** LinkedIn API requires your app to be company-verified for some scopes. For personal profiles, `w_member_social` works out of the box.

---

## 5. Logging & Monitoring

| Tool | Why | Pricing |
|------|-----|---------|
| **Google Sheets** ⭐ | Zero-cost logging. Append a row per post via n8n's native Google Sheets node. Easy to review, filter, and share. | Free |
| **Gmail (SMTP)** | Native n8n email node for failure alerts. Sends error details when any step fails. | Free |

**Log schema:**

| Date | Post ID | Status | Content Preview | Image URL | Engagement (48h) |
|------|---------|--------|-----------------|-----------|-------------------|
| 2026-06-14 | urn:li:post:... | Published | "Is AI replacing manual testing..." | leonardo.ai/img/abc123 | — |

---

## 6. Environment Variables & Secrets

Create an `.env` file or set in n8n credentials:

```bash
GEMINI_API_KEY=AIza...
LEONARDO_API_KEY=abc123...
LINKEDIN_ACCESS_TOKEN=AQV...
LINKEDIN_PERSON_URN=urn:li:person:abc123
GOOGLE_SHEET_ID=1BxiMVs0...
ALERT_EMAIL=you@gmail.com
```

---

## Total Monthly Cost

| Component | Free Tier | Paid Minimum |
|-----------|-----------|--------------|
| n8n | $0 (self-hosted) | $0 |
| Gemini 1.5 Pro | $0 (1,500 req/day) | $0 |
| Leonardo AI | $0 (150 credits/day) | $0 |
| LinkedIn API | $0 | $0 |
| Google Sheets | $0 | $0 |
| VPS (optional) | $0 (Railway free tier) | $5-10/month |
| **TOTAL** | **$0/month** | **$5-10/month** |

This stack runs completely free for up to 30 posts/month at production quality.
