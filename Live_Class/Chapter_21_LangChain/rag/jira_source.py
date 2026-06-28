"""Fetch all JIRA issues for a project via JQL (enhanced /search/jql endpoint,
with fallback to the legacy /search endpoint). Used to feed the RAG."""
import os

import requests

FIELDS = "summary,description,issuetype,priority,status,components,labels,reporter"


def _adf_to_text(node) -> str:
    """Flatten Atlassian Document Format (API v3) into plain text."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "".join(_adf_to_text(n) for n in node)
    if isinstance(node, dict):
        if node.get("type") == "text":
            return node.get("text", "")
        text = _adf_to_text(node.get("content"))
        if node.get("type") in {"paragraph", "heading", "listItem", "blockquote", "codeBlock"}:
            text += "\n"
        return text
    return ""


def _format_issue(key: str, f: dict) -> str:
    summary = f.get("summary", "(no summary)")
    desc = _adf_to_text(f.get("description")).strip() or "(no description)"
    issuetype = (f.get("issuetype") or {}).get("name", "?")
    priority = (f.get("priority") or {}).get("name", "?")
    status = (f.get("status") or {}).get("name", "?")
    components = ", ".join(c.get("name", "") for c in (f.get("components") or [])) or "—"
    labels = ", ".join(f.get("labels") or []) or "—"
    reporter = (f.get("reporter") or {}).get("displayName", "?")
    return (
        f"[{key}] {summary}\n"
        f"Type: {issuetype} | Priority: {priority} | Status: {status}\n"
        f"Components: {components} | Labels: {labels} | Reporter: {reporter}\n\n"
        f"Description:\n{desc}"
    )


def _auth():
    base = (os.getenv("JIRA_URL") or "").rstrip("/")
    email = os.getenv("JIRA_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")
    if not (base and email and token):
        raise RuntimeError("set JIRA_URL, JIRA_EMAIL and JIRA_API_TOKEN in .env")
    return base, (email, token)


def fetch_project_issues(project: str = "VWO", limit: int = 200) -> list[dict]:
    """Return [{key, fields(dict), report(str)}] for every issue in `project`
    (newest first), capped at `limit`. Tries the enhanced endpoint, falls back
    to legacy paging."""
    base, auth = _auth()
    jql = f"project = {project} ORDER BY created DESC"
    headers = {"Accept": "application/json"}
    issues: list[dict] = []

    # --- enhanced /search/jql (nextPageToken paging) ---
    token = None
    while len(issues) < limit:
        params = {"jql": jql, "fields": FIELDS, "maxResults": min(100, limit - len(issues))}
        if token:
            params["nextPageToken"] = token
        r = requests.get(f"{base}/rest/api/3/search/jql", auth=auth,
                         headers=headers, params=params, timeout=60)
        if r.status_code in (404, 410):
            issues = []          # endpoint not available -> legacy fallback
            break
        r.raise_for_status()
        body = r.json()
        for it in body.get("issues", []):
            issues.append({"key": it["key"], "fields": it.get("fields", {}),
                           "report": _format_issue(it["key"], it.get("fields", {}))})
        token = body.get("nextPageToken")
        if not token or body.get("isLast"):
            return issues

    if issues:
        return issues

    # --- legacy /search (startAt paging) ---
    start = 0
    while len(issues) < limit:
        params = {"jql": jql, "fields": FIELDS, "startAt": start,
                  "maxResults": min(100, limit - len(issues))}
        r = requests.get(f"{base}/rest/api/3/search", auth=auth,
                         headers=headers, params=params, timeout=60)
        r.raise_for_status()
        body = r.json()
        batch = body.get("issues", [])
        for it in batch:
            issues.append({"key": it["key"], "fields": it.get("fields", {}),
                           "report": _format_issue(it["key"], it.get("fields", {}))})
        start += len(batch)
        if start >= body.get("total", 0) or not batch:
            break
    return issues
