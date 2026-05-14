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
    "setOpenaiKey": "setOpencodeKey",
    "storedOpenai": "storedOpencode",
    "validationStatus.openai": "validationStatus.opencode",
    "result.openai_valid": "result.opencode_valid",
    "openai: ": "opencode: "
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

print("Done sweeping remaining openai references.")
