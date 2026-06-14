import ssl, urllib.request, json, certifi

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImFuaXJ1ZGhrYXBhcndhbjEwQGdtYWlsLmNvbSIsImV4cCI6NDkzNTA2MjUyMSwianRpIjoiZWNiNTQxOWMtYjNlMy00YWI0LWE4MjYtMGY4YTcyZGRjN2Q0In0.6ImcTjoaHv6FhL25-iW9NkZW5GKtI568pWCVxijo58U"
ctx = ssl.create_default_context(cafile=certifi.where())
base = "https://api.upload-post.com/api/uploadposts"
content_text = "Automated pipeline test post — QA automation and AI in testing"
h = {"User-Agent": "Mozilla/5.0", "Authorization": token, "Content-Type": "application/json"}

# Try the remaining unprobbed endpoints
tests = [
    "create-post",
    "create",
    "post",
    "upload",
    "linkedin/post",
    "linkedin-post",
    "publish",
    "post-now",
    "instant-post",
]

for endpoint in tests:
    url = f"{base}/{endpoint}"
    try:
        req = urllib.request.Request(url, data=json.dumps({"content": content_text}).encode(), headers=h, method="POST")
        resp = urllib.request.urlopen(req, timeout=12, context=ctx)
        body = resp.read().decode()
        print(f"[{resp.status}] POST /{endpoint}")
        try:
            j = json.loads(body)
            print(f"  {json.dumps(j, indent=2)[:400]}")
        except:
            print(f"  {body[:300]}")
    except urllib.error.HTTPError as e:
        code = e.code
        body = e.read().decode()[:400] if e.fp else ""
        if code not in (404, 405):
            try: body = json.dumps(json.loads(body), indent=2)
            except: pass
            print(f"[{code}] POST /{endpoint}: {body}")
    except Exception as e:
        print(f"[ERR] POST /{endpoint}: {type(e).__name__}: {str(e)[:150]}")
    print()
