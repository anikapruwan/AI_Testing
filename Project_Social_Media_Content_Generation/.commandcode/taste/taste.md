# Taste (Continuously Learned by [CommandCode][cmd])

[cmd]: https://commandcode.ai/

# tool-selection
- Prefer open-source and free tools over proprietary alternatives. When open-source isn't feasible, clearly explain the tradeoffs. Confidence: 0.70
- Include CommandCode in the tool stack for this project; the user has an API key for it. Confidence: 0.80

# upload-post-api
- For Upload-Post.com API upload_text endpoint, use `user: "linkedin"` as the form-data field value. Confidence: 0.85

# publishing
- Support multiple publishing backends (Upload-Post.com, Buffer) with automatic fallback — if one platform fails, the next automatically posts. Confidence: 0.75

# image-generation
- Use only Google Imagen (free tier) for image generation — remove DALL-E, Stability, ComfyUI. Confidence: 0.65
