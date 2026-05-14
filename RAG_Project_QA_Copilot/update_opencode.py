import os

files_to_update = [
    "docker-compose.yml",
    "README.md",
    "frontend/src/api/api.js",
    "frontend/src/components/ChatWidget.jsx",
    "frontend/src/components/SettingsModal.jsx",
    "backend/app/main.py",
    "backend/app/api/settings.py",
    "backend/app/api/chat.py",
    "backend/app/services/rag_service.py",
    "backend/app/models/settings.py",
    "backend/app/config.py"
]

replacements = {
    "openai_api_key": "opencode_api_key",
    "OPENAI_API_KEY": "OPENCODE_API_KEY",
    "openai_valid": "opencode_valid",
    "openaiKey": "opencodeKey",
    "openaiKeySet": "opencodeKeySet",
    "OpenAI API Key": "OpenCode API Key",
    "openai.com": "opencode.ai",
    "is_openai_model": "is_opencode_model",
    "OPENAI_MODELS": "OPENCODE_MODELS",
    "openai_model_name": "opencode_model_name",
    "OpenAI validation error": "OpenCode validation error",
    "OpenAI": "OpenCode"
}

for file_path in files_to_update:
    if not os.path.exists(file_path):
        continue
    with open(file_path, "r") as f:
        content = f.read()
    
    for old, new in replacements.items():
        content = content.replace(old, new)
        
    with open(file_path, "w") as f:
        f.write(content)

print("Done updating basic files.")
