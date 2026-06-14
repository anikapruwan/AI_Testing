# Automated LinkedIn Posting Workflow — Architecture Map

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SCHEDULER (n8n Cron Node)                         │
│                     Triggers daily at 9:00 AM UTC                        │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    CONTENT GENERATION (Google Gemini API)                 │
│  • Sends system prompt with RICE POT framework instructions              │
│  • Receives: LinkedIn post text + image generation prompt                │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                              ▼
┌───────────────────────────────┐  ┌──────────────────────────────────────┐
│   IMAGE GENERATION             │  │   CONTENT ASSEMBLY                    │
│   (Stability AI / Leonardo)    │  │   • Parse Gemini JSON response        │
│   • Sends image prompt         │  │   • Extract post text                 │
│   • Receives image URL         │  │   • Extract image prompt              │
└───────────────┬───────────────┘  └──────────────────┬────────────────────┘
                │                                      │
                └──────────────┬───────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    LINKEDIN PUBLISHING (LinkedIn API)                     │
│  • Posts text content                                                     │
│  • Uploads generated image                                                │
│  • Publishes to personal feed                                             │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    LOGGING & MONITORING (Google Sheets + Email)           │
│  • Logs post ID, timestamp, content snippet                               │
│  • Alerts on failure via email/slack                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Walkthrough

### Phase 1: Scheduling Trigger

**Platform:** n8n (self-hosted or cloud)
**Node:** Cron Trigger

- Fires every day at 9:00 AM UTC (adjustable per timezone)
- Passes the current date as a data payload for context-aware generation
- On failure, retries once after 5 minutes

### Phase 2: Content Prompt Construction

**Node:** n8n Set / Function Node

Constructs the full system prompt dynamically:

```javascript
const systemPrompt = `
You are a Senior AI Automation Architect and B2B Content Strategist 
specializing in QA and software testing.

Generate ONE LinkedIn post for today (${new Date().toLocaleDateString()}).
Focus on: QA automation, AI in testing, or software testing trends.

Output as JSON:
{
  "post_text": "...",
  "image_prompt": "...",
  "hashtags": ["..."]
}

Rules:
- Keep post under 1300 characters
- Include exactly 5 relevant hashtags
- Make image prompt cinematic and ultra-detailed
- Vary topic from previous days (avoid repetition)
`;
```

### Phase 3: Text Generation via Gemini API

**Node:** n8n HTTP Request

```
Method: POST
URL: https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent
Headers:
  Content-Type: application/json
  x-goog-api-key: {{$env.GEMINI_API_KEY}}
Body:
{
  "contents": [{
    "parts": [{"text": "{{systemPrompt}}"}]
  }],
  "generationConfig": {
    "temperature": 0.9,
    "maxOutputTokens": 800
  }
}
```

**Response parsing:**
- Extract the JSON block from Gemini's text response
- Validate post_text length (<1300 chars) and hashtag count (5)
- Split output into two parallel paths: image generation + content assembly

### Phase 4: Image Generation via Leonardo AI

**Node:** n8n HTTP Request (executes in parallel with content assembly)

```
Method: POST
URL: https://cloud.leonardo.ai/api/rest/v1/generations
Headers:
  Authorization: Bearer {{$env.LEONARDO_API_KEY}}
  Content-Type: application/json
Body:
{
  "prompt": "{{imagePrompt}}",
  "modelId": "1e60896f-3c26-4296-8ecc-53e2afecc132",
  "width": 1024,
  "height": 1024,
  "num_images": 1
}
```

**Polling for completion:**
- Leonardo returns a `generationId`
- Wait 10 seconds, then poll `GET /api/rest/v1/generations/{id}`
- Extract the generated image URL once status is COMPLETE
- Timeout after 120 seconds; fall back to text-only post if image generation fails

### Phase 5: LinkedIn Post Creation

**Node:** n8n HTTP Request

#### Step 5a: Register Image Upload

```
Method: POST
URL: https://api.linkedin.com/rest/images?action=initializeUpload
Headers:
  Authorization: Bearer {{$env.LINKEDIN_ACCESS_TOKEN}}
  LinkedIn-Version: 202405
  Content-Type: application/json
Body:
{
  "initializeUploadRequest": {
    "owner": "urn:li:person:{{$env.LINKEDIN_PERSON_URN}}"
  }
}
```

- Extract `uploadUrl` and `image` URN from response

#### Step 5b: Upload Image Binary

```
Method: PUT
URL: {{uploadUrl}}
Headers:
  Content-Type: application/octet-stream
Body: (binary image data fetched from Leonardo URL via n8n Read Binary File node)
```

#### Step 5c: Create Post

```
Method: POST
URL: https://api.linkedin.com/rest/posts
Headers:
  Authorization: Bearer {{$env.LINKEDIN_ACCESS_TOKEN}}
  LinkedIn-Version: 202405
  Content-Type: application/json
Body:
{
  "author": "urn:li:person:{{$env.LINKEDIN_PERSON_URN}}",
  "commentary": "{{postText}}",
  "visibility": "PUBLIC",
  "distribution": {
    "feedDistribution": "MAIN_FEED",
    "targetEntities": [],
    "thirdPartyDistributionChannels": []
  },
  "content": {
    "media": {
      "id": "{{imageUrn}}"
    }
  },
  "lifecycleState": "PUBLISHED",
  "isReshareDisabledByAuthor": false
}
```

### Phase 6: Logging & Alerting

**Nodes:** n8n Google Sheets + Email/Slack

- Append a row to Google Sheets: `[Date, Post ID, Status, Content Snippet, Image URL]`
- On failure at any node: Send email via Gmail node or Slack webhook with error details
- Weekly summary email with engagement stats (optional: pull via LinkedIn Analytics API)

---

## Vibe Coding Integration Notes

This entire workflow is "vibe coded" because:

1. **Natural language drives content** — The Gemini system prompt is the only content logic; no hardcoded copy
2. **Prompt-chaining replaces code** — Each step passes natural language output to the next API
3. **Low-code orchestration** — n8n's visual nodes + built-in HTTP request modules eliminate custom backend code
4. **API-first design** — Every tool is accessed via REST API, stitched together with n8n's HTTP Request nodes

---

## Alternative Architecture Variants

| Component | Primary Choice | Alternative |
|-----------|---------------|-------------|
| Orchestration | n8n (self-hosted) | Make.com |
| Text LLM | Gemini 1.5 Pro | OpenAI GPT-4o |
| Image Gen | Leonardo AI | Stability AI (via Replicate) |
| Publishing | LinkedIn API | Buffer API (indirect) |
| Logging | Google Sheets | Airtable |
