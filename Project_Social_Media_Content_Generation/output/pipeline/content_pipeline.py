#!/usr/bin/env python3
"""
LinkedIn Automated Content Pipeline
Vibe-coded: Command Code → ComfyUI → LinkedIn
"""

import json
import os
import random
import ssl
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

import certifi
import yaml


def http_request(req, timeout=30):
    ctx = ssl.create_default_context(cafile=certifi.where())
    return urllib.request.urlopen(req, timeout=timeout, context=ctx)


def load_config(path=None):
    paths = [path] if path else ["config.local.yaml", "config.yaml"]
    for p in paths:
        if os.path.exists(p):
            with open(p) as f:
                return yaml.safe_load(f)
    raise FileNotFoundError("No config file found (tried config.local.yaml, config.yaml)")


def build_system_prompt(domains, max_chars, hashtag_count, fixed_hashtags):
    topic = random.choice(domains)
    fixed_str = ", ".join(fixed_hashtags)
    return (
        f"You are a Senior QA Automation Architect and B2B Content Strategist. "
        f"Generate ONE LinkedIn post about: {topic}. "
        f"Output ONLY valid JSON, no markdown wrapping, no backticks:\n"
        f'{{"post_text": "...", "image_prompt": "...", "hashtags": ["..."]}}\n'
        f"Rules:\n"
        f"- post_text under {max_chars} characters\n"
        f"- Hashtags array: include at least {len(fixed_hashtags)} fixed hashtags: [{fixed_str}], "
        f"plus {hashtag_count - len(fixed_hashtags)} unique topic-relevant ones (total exactly {hashtag_count})\n"
        f"- image_prompt: ultra-detailed, cinematic, photorealistic, 8k, "
        f"about software testing / QA / AI themes\n"
        f"- Tone: professional, authoritative, no fluff"
    )


def append_hashtags(post_text, hashtags):
    tag_string = " ".join(["#" + t for t in hashtags])
    if post_text.rstrip().endswith(tag_string):
        return post_text
    if not post_text.endswith("\n\n"):
        post_text = post_text.rstrip() + "\n\n"
    return post_text + tag_string


def call_command_code(prompt, config):
    cc = config["command_code"]
    args = ["cmd", "-p"]
    if cc.get("max_turns"):
        args += ["--max-turns", str(cc["max_turns"])]
    if cc.get("trust"):
        args.append("--trust")
    args.append(prompt)

    result = subprocess.run(args, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"Command Code failed: {result.stderr}")

    return result.stdout


def parse_json_response(raw_text):
    text = raw_text.strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found in Command Code output")
    return json.loads(text[start:end])
# ── Image Generation ──────────────────────────────────────────────────────────


def generate_image_google_imagen(api_key, model, prompt):
    """Generate image via Google AI Studio Imagen (free tier)."""
    import base64

    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
        },
    }).encode()

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=body,
                headers={"x-goog-api-key": api_key, "Content-Type": "application/json"})
            resp = json.loads(http_request(req, timeout=60).read())

            for part in resp.get("candidates", [{}])[0].get("content", {}).get("parts", []):
                if "inlineData" in part:
                    img_data = base64.b64decode(part["inlineData"]["data"])
                    mime = part["inlineData"].get("mimeType", "image/png")
                    ext = "png" if "png" in mime else "jpg"
                    filename = f"imagen_{int(time.time())}.{ext}"
                    Path("logs").mkdir(parents=True, exist_ok=True)
                    path = os.path.join("logs", filename)
                    with open(path, "wb") as f:
                        f.write(img_data)
                    return path, filename

            raise ValueError("No image returned")

        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                wait = (attempt + 1) * 15
                print(f"      Rate limited, retrying in {wait}s...")
                time.sleep(wait)
                continue
            raise



def generate_image_dalle(api_key, model, size, quality, prompt):
    body = json.dumps({"model": model, "prompt": prompt, "n": 1, "size": size, "quality": quality}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/images/generations", data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    resp = json.loads(http_request(req).read())
    url = resp["data"][0]["url"]
    filename = f"dalle_{int(time.time())}.png"
    return url, filename


def generate_image_stability(api_key, engine, prompt):
    body = json.dumps({"text_prompts": [{"text": prompt, "weight": 1}], "cfg_scale": 7,
        "height": 1024, "width": 1024, "samples": 1, "steps": 30}).encode()
    req = urllib.request.Request(f"https://api.stability.ai/v1/generation/{engine}/text-to-image",
        data=body, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    resp = json.loads(http_request(req, timeout=60).read())
    import base64
    img_data = base64.b64decode(resp["artifacts"][0]["base64"])
    filename = f"stability_{int(time.time())}.png"
    Path("logs").mkdir(parents=True, exist_ok=True)
    path = os.path.join("logs", filename)
    with open(path, "wb") as f:
        f.write(img_data)
    return path, filename


def generate_image_comfyui(server_url, prompt, template_file, width, height, steps, cfg, timeout_s, poll_s):
    with open(template_file) as f:
        workflow = json.load(f)
    for nid, node in workflow.items():
        inp = node.get("inputs", {})
        if inp and ("text" in inp or "prompt" in inp):
            key = "text" if "text" in inp else "prompt"
            inp[key] = prompt
            if "steps" in inp: inp["steps"] = steps
            if "cfg" in inp: inp["cfg"] = cfg
            break

    req = urllib.request.Request(f"{server_url}/prompt",
        data=json.dumps({"prompt": workflow}).encode(),
        headers={"Content-Type": "application/json"})
    prompt_id = json.loads(http_request(req).read())["prompt_id"]

    elapsed = 0
    while elapsed < timeout_s:
        time.sleep(poll_s)
        elapsed += poll_s
        try:
            history = json.loads(http_request(urllib.request.Request(f"{server_url}/history/{prompt_id}")).read())
            if prompt_id in history:
                for outputs in history[prompt_id]["outputs"].values():
                    for img in outputs.get("images", []):
                        url = f"{server_url}/view?filename={img['filename']}&subfolder={img.get('subfolder','')}"
                        return url, img["filename"]
        except Exception:
            continue
    raise TimeoutError(f"ComfyUI timed out after {timeout_s}s")


def download_image(image_url, filename):
    urllib.request.urlretrieve(image_url, filename)
    return filename


def generate_image(image_cfg, prompt):
    """Try each image provider in order. First success wins."""
    providers = image_cfg.get("providers", ["comfyui"])
    last_error = None

    for provider in providers:
        try:
            print(f"      Trying image generator: {provider}...")

            if provider == "google-imagen":
                cfg = image_cfg["google_imagen"]
                path, filename = generate_image_google_imagen(cfg["api_key"], cfg["model"], prompt)
                return path, filename

            elif provider == "dall-e":
                cfg = image_cfg["dall_e"]
                url, filename = generate_image_dalle(cfg["api_key"], cfg["model"], cfg["size"], cfg["quality"], prompt)
                return url, filename

            elif provider == "stability":
                cfg = image_cfg["stability"]
                path, filename = generate_image_stability(cfg["api_key"], cfg["engine"], prompt)
                return path, filename

            elif provider == "comfyui":
                cfg = image_cfg["comfyui"]
                url, filename = generate_image_comfyui(
                    cfg["server_url"], prompt, cfg["workflow_template"],
                    cfg["width"], cfg["height"], cfg["steps"], cfg["cfg"],
                    cfg["timeout_seconds"], cfg["poll_interval"],
                )
                return url, filename

            else:
                raise ValueError(f"Unknown image provider: {provider}")

        except Exception as e:
            last_error = f"{provider}: {e}"
            print(f"      ❌ {last_error}")
            continue

    raise RuntimeError(f"All image providers failed: {last_error}")


def linkedin_upload_image(access_token, api_version, person_urn, image_path):
    init_url = "https://api.linkedin.com/rest/images?action=initializeUpload"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "LinkedIn-Version": api_version,
        "Content-Type": "application/json",
    }
    body = json.dumps({"initializeUploadRequest": {"owner": person_urn}}).encode()
    req = urllib.request.Request(init_url, data=body, headers=headers)
    resp = json.loads(http_request(req).read())
    upload_url = resp["value"]["uploadUrl"]
    image_urn = resp["value"]["image"]

    with open(image_path, "rb") as f:
        img_data = f.read()
    req = urllib.request.Request(upload_url, data=img_data, method="PUT")
    req.add_header("Content-Type", "application/octet-stream")
    http_request(req)

    return image_urn


def linkedin_create_post(access_token, api_version, person_urn, post_text, image_urn):
    post_url = "https://api.linkedin.com/rest/posts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "LinkedIn-Version": api_version,
        "Content-Type": "application/json",
    }
    body = {
        "author": person_urn,
        "commentary": post_text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "content": {"media": {"id": image_urn}},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    req = urllib.request.Request(post_url, data=json.dumps(body).encode(), headers=headers)
    resp = json.loads(http_request(req).read())
    return resp.get("id", "unknown")


def publish_upload_post(api_key, user, post_text, image_path=None):
    auth_header = f"Apikey {api_key}"

    if image_path:
        return publish_upload_post_with_image(api_key, user, post_text, image_path)

    boundary = "----PipelineBoundary" + str(int(time.time()))
    body = ""
    body += f"--{boundary}\r\n"
    body += f'Content-Disposition: form-data; name="user"\r\n\r\n{user}\r\n'
    body += f"--{boundary}\r\n"
    body += f'Content-Disposition: form-data; name="platform[]"\r\n\r\nlinkedin\r\n'
    body += f"--{boundary}\r\n"
    body += f'Content-Disposition: form-data; name="title"\r\n\r\n{post_text}\r\n'
    body += f"--{boundary}--\r\n"

    req = urllib.request.Request(
        "https://api.upload-post.com/api/upload_text",
        data=body.encode("utf-8"),
        headers={
            "Authorization": auth_header,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    resp = json.loads(http_request(req).read())
    if resp.get("success"):
        return resp.get("request_id", resp.get("job_id", "published"))
    return "unknown"


def publish_upload_post_with_image(api_key, user, post_text, image_path):
    auth_header = f"Apikey {api_key}"
    boundary = "----PipelineBoundary" + str(int(time.time()))
    body_bytes = bytearray()

    def add_field(name, value):
        body_bytes += f"--{boundary}\r\n".encode()
        body_bytes += f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        body_bytes += value.encode()
        body_bytes += b"\r\n"

    add_field("user", user)
    add_field("platform[]", "linkedin")
    add_field("title", post_text)

    with open(image_path, "rb") as f:
        img_data = f.read()
    filename = os.path.basename(image_path)
    body_bytes += f"--{boundary}\r\n".encode()
    body_bytes += f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode()
    body_bytes += b"Content-Type: image/jpeg\r\n\r\n"
    body_bytes += img_data
    body_bytes += f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        "https://api.upload-post.com/api/upload_photos",
        data=bytes(body_bytes),
        headers={
            "Authorization": auth_header,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    resp = json.loads(http_request(req).read())
    if resp.get("success"):
        return resp.get("request_id", resp.get("job_id", "published"))
    return "unknown"


def publish_post(publishing_cfg, post_text, image_path=None):
    """Try each provider in order. First success wins. Logs failures and continues."""
    providers = publishing_cfg.get("providers", ["upload-post"])
    last_error = None

    for provider in providers:
        try:
            print(f"      Trying {provider}...")

            if provider == "upload-post":
                cfg = publishing_cfg["upload_post"]
                result = publish_upload_post(cfg["api_key"], cfg.get("user", ""), post_text, image_path)

            elif provider == "buffer":
                cfg = publishing_cfg["buffer"]
                result = publish_buffer(cfg["access_token"], cfg["profile_id"], post_text, image_path)

            elif provider == "linkedin-direct":
                cfg = publishing_cfg["linkedin"]
                if image_path:
                    image_urn = linkedin_upload_image(
                        cfg["access_token"], cfg["api_version"], cfg["person_urn"], image_path
                    )
                else:
                    image_urn = None
                result = linkedin_create_post(
                    cfg["access_token"], cfg["api_version"], cfg["person_urn"], post_text, image_urn
                )

            else:
                raise ValueError(f"Unknown provider: {provider}")

            if result and not str(result).startswith("error"):
                print(f"      ✅ {provider} succeeded")
                return result
            else:
                raise Exception(str(result))

        except Exception as e:
            last_error = f"{provider}: {e}"
            print(f"      ❌ {last_error}")
            continue

    return f"all-failed: {last_error}"


def publish_buffer(access_token, profile_id, post_text, image_path=None):
    """
    Publish via Buffer GraphQL API — https://api.buffer.com
    Mutation: createPost with variables (handles special chars safely)
    """
    if image_path:
        raise Exception("Buffer createPost does not support inline images; use Upload-Post.")

    mutation = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        __typename
        ... on PostActionSuccess { post { id status } }
        ... on MutationError { message }
      }
    }
    """

    variables = {
        "input": {
            "channelId": profile_id,
            "text": post_text,
            "schedulingType": "automatic",
            "mode": "shareNow",
        }
    }

    body = json.dumps({"query": mutation, "variables": variables}).encode()
    req = urllib.request.Request(
        "https://api.buffer.com/",
        data=body,
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
    )

    resp = json.loads(http_request(req).read())
    if "errors" in resp:
        return f"error: {resp['errors'][0].get('message', str(resp['errors']))}"

    result = resp.get("data", {}).get("createPost", {})
    if result.get("__typename") == "PostActionSuccess":
        return result.get("post", {}).get("id", "published")
    elif result.get("__typename") == "MutationError":
        return f"error: {result.get('message', 'unknown')}"

    return "unknown"


def log_post(log_dir, history_file, record):
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    history = []
    if os.path.exists(history_file):
        with open(history_file) as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []

    history.append(record)
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2, default=str)

    log_path = os.path.join(log_dir, f"post_{record['date']}.json")
    with open(log_path, "w") as f:
        json.dump(record, f, indent=2, default=str)


def main():
    dry_run = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    config_path = args[0] if args else None
    config = load_config(config_path)

    content_cfg = config["content"]
    image_cfg = config.get("image_generation", {"providers": ["comfyui"]})
    publishing_cfg = config["publishing"]
    output_cfg = config["output"]

    print("[1/6] Generating content via Command Code...")
    prompt = build_system_prompt(
        content_cfg["domains"],
        content_cfg["max_chars"],
        content_cfg["hashtag_count"],
        content_cfg.get("fixed_hashtags", []),
    )
    raw_output = call_command_code(prompt, config)
    data = parse_json_response(raw_output)
    data["post_text"] = append_hashtags(data["post_text"], data["hashtags"])
    print(f"      Topic: {data.get('hashtags', [''])[0]}")
    print(f"      Post length: {len(data.get('post_text', ''))} chars")

    if dry_run:
        print("\n--- DRY RUN OUTPUT ---")
        print(f"\n{data['post_text']}\n")
        print(f"Hashtags: {' '.join(['#' + t for t in data['hashtags']])}")
        print(f"\nImage Prompt:\n{data['image_prompt']}")
        print("\n✅ Dry run complete — content generated successfully.")
        return

    try:
        print("[2/6] Generating image...")
        image_url, image_filename = generate_image(image_cfg, data["image_prompt"])
        print(f"      Image: {image_url}")

        if image_url.startswith("http"):
            print("[3/6] Downloading generated image...")
            local_path = os.path.join(output_cfg.get("log_dir", "./logs"), image_filename)
            download_image(image_url, local_path)
            image_path = local_path
        else:
            image_path = image_url

    except (FileNotFoundError, ConnectionError, TimeoutError, RuntimeError) as e:
        print(f"      ⚠️  Image generation failed: {e}. Publishing text-only.")
        image_path = None

    print("[4/6] Publishing...")
    post_id = publish_post(publishing_cfg, data["post_text"], image_path)
    print(f"      Post ID: {post_id}")

    print("[5/6] Logging...")
    date_str = datetime.now().strftime("%Y-%m-%d")
    record = {
        "date": date_str,
        "post_id": post_id,
        "post_text": data["post_text"],
        "image_prompt": data["image_prompt"],
        "hashtags": data["hashtags"],
        "image_filename": image_path if image_path else "none",
        "status": "published" if post_id != "unknown" else "failed",
    }
    log_post(output_cfg["log_dir"], output_cfg["history_file"], record)

    print(f"\n✅ Posted successfully: {date_str}")
    print(f"   Post ID: {post_id}")
    print(f"   Hashtags: {' '.join(['#' + t for t in data['hashtags']])}")


if __name__ == "__main__":
    main()
