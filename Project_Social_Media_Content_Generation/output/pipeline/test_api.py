import ssl, urllib.request, json, certifi

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImFuaXJ1ZGhrYXBhcndhbjEwQGdtYWlsLmNvbSIsImV4cCI6NDkzNTA2MjUyMSwianRpIjoiZWNiNTQxOWMtYjNlMy00YWI0LWE4MjYtMGY4YTcyZGRjN2Q0In0.6ImcTjoaHv6FhL25-iW9NkZW5GKtI568pWCVxijo58U"
ctx = ssl.create_default_context(cafile=certifi.where())
h = {"User-Agent": "Mozilla/5.0", "Authorization": token, "Content-Type": "application/json"}
base = "https://api.upload-post.com/api/uploadposts"
content = "Test post from automated LinkedIn pipeline"

# Try schedule POST
tests = [
    ("POST /schedule", "POST", f"{base}/schedule",
     json.dumps({"content": content, "schedule_type": "now"}).encode()),
    ("POST /account", "POST", f"{base}/account",
     json.dumps({"content": content}).encode()),
    ("POST /upload", "POST", f"{base}/upload",
     json.dumps({"content": content}).encode()),
    ("PUT /account", "PUT", f"{base}/account",
     json.dumps({"content": content}).encode()),
    ("POST /create-post", "POST", f"{base}/create-post",
     json.dumps({"content": content}).encode()),
    ("POST /publish", "POST", f"{base}/publish",
     json.dumps({"content": content}).encode()),
    ("POST /generate", "POST", f"{base}/generate",
     json.dumps({"content": content}).encode()),
    ("POST /now", "POST", f"{base}/now",
     json.dumps({"content": content}).encode()),
    ("POST /instant", "POST", f"{base}/instant",
     json.dumps({"content": content}).encode()),
    ("POST /linkedin/post", "POST", f"{base}/linkedin/post",
     json.dumps({"content": content}).encode()),
]

for name, method, url, data in tests:
    try:
        req = urllib.request.Request(url, data=data, headers=h, method=method)
        resp = urllib.request.urlopen(req, timeout=12, context=ctx)
        body = resp.read().decode()
        print(f"[{resp.status}] {name}")
        try: print(f"  {json.dumps(json.loads(body), indent=2)[:400]}")
        except: print(f"  {body[:300]}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:400] if e.fp else ""
        if e.code not in (404, 405):
            try: body = json.dumps(json.loads(body), indent=2)
            except: pass
            print(f"[{e.code}] {name}: {body}")
    except Exception as e:
        print(f"[ERR] {name}: {type(e).__name__}: {str(e)[:200]}")
    print()

# Try the other JS bundle for API route clues
try:
    req = urllib.request.Request("https://www.upload-post.com/_astro/NavBar.astro_astro_type_script_index_0_lang.BrYIdfx4.js",
                                 headers={"User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=12, context=ctx)
    js = resp.read().decode()
    import re
    urls = re.findall(r'https?://[^"\'\s]+', js)
    print("=== NavBar JS URLs ===")
    for u in urls[:30]:
        print(f"  {u}")
except Exception as e:
    print(f"JS: {e}")
