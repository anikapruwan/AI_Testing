#!/usr/bin/env python3
"""
LinkedIn Automated Content Pipeline
Vibe-coded: Command Code → Cloudflare Workers → Buffer → LinkedIn
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


def generate_image(prompt, config):
    """Call the Cloudflare Workers image generation API, save JPEG to disk, return filepath."""
    img_cfg = config["image_generation"]
    url = img_cfg["api_url"]
    api_key = img_cfg["api_key"]

    body = json.dumps({"prompt": prompt}).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Python/3.12",
        },
    )
    resp = http_request(req)
    img_data = resp.read()

    out_dir = img_cfg.get("output_dir", "images")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"linkedin_{timestamp}.jpg"
    filepath = os.path.join(out_dir, filename)
    with open(filepath, "wb") as f:
        f.write(img_data)

    return filepath


def upload_image_to_hosting(filepath, config):
    """Upload an image to a public image hosting service, return the public URL."""
    host_cfg = config.get("image_hosting", {})
    provider = host_cfg.get("provider", "imgbb")
    api_key = host_cfg.get("api_key", "")

    if not api_key:
        raise ValueError(f"Image hosting provider '{provider}' requires an api_key in config")

    if provider == "imgbb":
        with open(filepath, "rb") as f:
            img_data = f.read()

        boundary = "----ImgBoundary" + str(int(time.time()))
        body = b""
        body += f"--{boundary}\r\n".encode()
        body += b'Content-Disposition: form-data; name="image"; filename="image.jpg"\r\n'
        body += b"Content-Type: image/jpeg\r\n\r\n"
        body += img_data
        body += f"\r\n--{boundary}--\r\n".encode()

        req = urllib.request.Request(
            f"https://api.imgbb.com/1/upload?key={api_key}",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        resp = json.loads(http_request(req).read())
        if not resp.get("success"):
            raise RuntimeError(f"imgbb upload failed: {resp.get('error', {}).get('message', str(resp))}")
        return resp["data"]["url"]

    elif provider == "custom":
        upload_url = host_cfg["upload_url"]
        url_field = host_cfg.get("url_field", "url")
        headers = {"Content-Type": "image/jpeg"}
        if host_cfg.get("api_key"):
            headers["Authorization"] = f"Bearer {host_cfg['api_key']}"

        with open(filepath, "rb") as f:
            img_data = f.read()
        req = urllib.request.Request(upload_url, data=img_data, headers=headers)
        resp = json.loads(http_request(req).read())
        return resp[url_field]

    else:
        raise ValueError(f"Unknown image hosting provider: {provider}")


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


def publish_upload_post(api_key, user, post_text):
    auth_header = f"Apikey {api_key}"

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


def publish_post(publishing_cfg, post_text, image_filepath=None, config=None):
    """Try each provider in order. First success wins."""
    providers = publishing_cfg.get("providers", ["upload-post"])
    last_error = None
    media_url = None

    # If we have an image, upload it to a public hosting service first
    if image_filepath:
        try:
            media_url = upload_image_to_hosting(image_filepath, config)
            print(f"      Image hosted at: {media_url}")
        except Exception as e:
            print(f"      ⚠️ Image hosting failed: {e}")
            print(f"      Continuing text-only...")

    for provider in providers:
        try:
            print(f"      Trying {provider}...")

            if provider == "upload-post":
                cfg = publishing_cfg["upload_post"]
                result = publish_upload_post(cfg["api_key"], cfg.get("user", ""), post_text)

            elif provider == "buffer":
                cfg = publishing_cfg["buffer"]
                result = publish_buffer(cfg["access_token"], cfg["profile_id"], post_text, media_url)

            elif provider == "linkedin-direct":
                cfg = publishing_cfg["linkedin"]
                result = linkedin_create_post(
                    cfg["access_token"], cfg["api_version"], cfg["person_urn"], post_text, None
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


def publish_buffer(access_token, profile_id, post_text, media_url=None):
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
            "assets": [{"image": {"url": media_url}}] if media_url else [],
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

    # Image generation
    image_filepath = None
    if content_cfg.get("generate_image", True):
        print("[2/6] Generating image...")
        try:
            image_filepath = generate_image(data["image_prompt"], config)
            print(f"      Image saved: {image_filepath}")
        except Exception as e:
            print(f"      ⚠️ Image generation failed: {e}")
            print(f"      Continuing with text-only post...")

    if dry_run:
        print("\n--- DRY RUN OUTPUT ---")
        print(f"\n{data['post_text']}\n")
        print(f"Hashtags: {' '.join(['#' + t for t in data['hashtags']])}")
        print(f"\nImage Prompt:\n{data['image_prompt']}")
        if image_filepath:
            print(f"\nImage saved at: {image_filepath}")
        print("\n✅ Dry run complete — content generated successfully.")
        return

    print("[3/6] Publishing...")
    post_id = publish_post(publishing_cfg, data["post_text"], image_filepath, config)
    print(f"      Post ID: {post_id}")

    print("[4/6] Logging...")
    date_str = datetime.now().strftime("%Y-%m-%d")
    record = {
        "date": date_str,
        "post_id": post_id,
        "post_text": data["post_text"],
        "image_prompt": data.get("image_prompt", ""),
        "hashtags": data["hashtags"],
        "image_filename": os.path.basename(image_filepath) if image_filepath else "none",
        "image_generated": image_filepath is not None,
        "status": "published" if not str(post_id).startswith("all-failed") else "failed",
    }
    log_post(output_cfg["log_dir"], output_cfg["history_file"], record)

    print(f"\n✅ Posted successfully: {date_str}")
    print(f"   Post ID: {post_id}")
    print(f"   Hashtags: {' '.join(['#' + t for t in data['hashtags']])}")


if __name__ == "__main__":
    main()
