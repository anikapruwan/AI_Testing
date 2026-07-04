#!/usr/bin/env python3
"""
FreeGen.app Image Generator
Uses prompt-signer → image-generator → WebSocket flow to generate images.
"""

import asyncio
import base64
import hashlib
import json
import os
import ssl
import time
import urllib.request
from pathlib import Path
from urllib.parse import unquote

import certifi
import websockets

SIGNER_URL = "https://prompt-signer.freegen.app"
GENERATOR_URL = "https://image-generator.freegen.app"
WEBSOCKET_URL = "wss://websocket-bridge.freegen.app/ws"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://freegen.app/",
    "Origin": "https://freegen.app",
}


def _http_post(url, body, timeout=30):
    ctx = ssl.create_default_context(cafile=certifi.where())
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=HEADERS)
    resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
    return json.loads(resp.read())


def _ws_auth(job_id):
    ts = int(time.time())
    msg = job_id + str(ts)
    h = hashlib.sha256(msg.encode()).hexdigest()
    return base64.b64encode(h.encode()).decode()[:20] + ":" + str(ts)


async def _listen_ws(job_id, timeout=90):
    auth = _ws_auth(job_id)
    ws_ssl = ssl.create_default_context()
    ws_ssl.check_hostname = False
    ws_ssl.verify_mode = ssl.CERT_NONE

    async with websockets.connect(
        WEBSOCKET_URL,
        ssl=ws_ssl,
        additional_headers={
            "Origin": "https://freegen.app",
            "User-Agent": HEADERS["User-Agent"],
        }
    ) as ws:
        await ws.send(json.dumps({"type": "subscribe", "job_id": job_id, "auth": auth}))

        async for msg in ws:
            data = json.loads(msg)
            if data.get("type") == "result":
                return data["image_data"]
            elif data.get("type") == "error":
                raise RuntimeError(data.get("message", "Unknown WebSocket error"))


def _download_image(image_url, output_path):
    data_url_prefix = "data:image/jpeg;base64,"
    if image_url.startswith(data_url_prefix):
        img_data = base64.b64decode(image_url[len(data_url_prefix):])
    elif image_url.startswith("http"):
        ctx = ssl.create_default_context(cafile=certifi.where())
        req = urllib.request.Request(image_url, headers={"User-Agent": HEADERS["User-Agent"]})
        img_data = urllib.request.urlopen(req, context=ctx).read()
    else:
        raise ValueError(f"Unsupported image URL format: {image_url[:60]}...")

    Path(os.path.dirname(output_path) or ".").mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(img_data)

    return len(img_data)


def generate(prompt, output_path=None, aspect_ratio="4:3", timeout=120):
    """
    Generate an image using FreeGen.app and save it to output_path.
    
    Args:
        prompt: Text prompt for image generation
        output_path: Path to save the image (default: ./freegen_<timestamp>.jpg)
        aspect_ratio: "1:1", "4:3", "3:4", "16:9", or "9:16"
        timeout: Maximum seconds to wait for image generation
    
    Returns:
        Absolute path to the saved image file
    """
    if output_path is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = f"freegen_{timestamp}.jpg"

    print(f"[FreeGen] Signing prompt...")
    signer_resp = _http_post(SIGNER_URL, {"prompt": prompt})
    ts, sig = signer_resp["ts"], signer_resp["sig"]

    print(f"[FreeGen] Requesting generation...")
    gen_resp = _http_post(GENERATOR_URL, {
        "prompt": prompt,
        "ts": ts,
        "sig": sig,
        "ratio_id": aspect_ratio,
    })
    job_id = gen_resp["job_id"]

    print(f"[FreeGen] Waiting for image (job: {job_id[:8]}...)...")
    image_url = asyncio.run(_listen_ws(job_id, timeout=timeout))

    size = _download_image(image_url, output_path)
    abs_path = os.path.abspath(output_path)
    print(f"[FreeGen] Saved: {abs_path} ({size} bytes)")

    return abs_path


if __name__ == "__main__":
    import sys
    prompt = sys.argv[1] if len(sys.argv) > 1 else "A fluffy seal point cat lounging in a vibrant green grass field, cinematic lighting"
    generate(prompt)
