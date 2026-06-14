import ssl, urllib.request, json, certifi, sys
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImFuaXJ1ZGhrYXBhcndhbjEwQGdtYWlsLmNvbSIsImV4cCI6NDkzNTA2MjUyMSwianRpIjoiZWNiNTQxOWMtYjNlMy00YWI0LWE4MjYtMGY4YTcyZGRjN2Q0In0.6ImcTjoaHv6FhL25-iW9NkZW5GKtI568pWCVxijo58U"
ctx = ssl.create_default_context(cafile=certifi.where())
h = {"Authorization": token, "Content-Type": "application/json"}
base = "https://api.upload-post.com/api/uploadposts"
content = "Pipeline test post"

results = []
for ep in ["schedule", "history", "account"]:
    url = f"{base}/{ep}"
    try:
        req = urllib.request.Request(url, data=json.dumps({"content": content}).encode(), headers=h, method="POST")
        resp = urllib.request.urlopen(req, timeout=10, context=ctx)
        results.append(f"[{resp.status}] POST /{ep}: {resp.read().decode()[:300]}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300] if e.fp else ""
        if e.code not in (404, 405):
            results.append(f"[{e.code}] POST /{ep}: {body}")
    except Exception as e:
        results.append(f"[ERR] POST /{ep}: {e}")

for r in results:
    print(r)
