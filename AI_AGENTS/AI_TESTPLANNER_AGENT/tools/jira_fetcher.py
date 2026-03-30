import requests
from requests.auth import HTTPBasicAuth

def fetch_jira_ticket(jira_id: str, domain: str, email: str, api_token: str):
    """
    Fetches the ticket summary and description from Jira (using API v2 for string descriptions).
    """
    if not domain or not email or not api_token:
        raise ValueError("Jira credentials are incomplete.")
        
    url = f"{domain.rstrip('/')}/rest/api/2/issue/{jira_id}"
    auth = HTTPBasicAuth(email, api_token)
    headers = {
        "Accept": "application/json"
    }

    response = requests.request("GET", url, headers=headers, auth=auth)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch Jira ticket {jira_id}: {response.text}")

    data = response.json()
    fields = data.get("fields", {})
    
    summary = fields.get("summary", "")
    description = fields.get("description", "")
    
    return {
        "summary": summary,
        "description": description if description else ""
    }

def test_jira_connection(domain: str, email: str, api_token: str):
    """
    Test connection by fetching current user info
    """
    if not domain or not email or not api_token:
        return False, "Jira credentials are missing."
        
    url = f"{domain.rstrip('/')}/rest/api/2/myself"
    auth = HTTPBasicAuth(email, api_token)
    headers = {"Accept": "application/json"}
    
    try:
        response = requests.request("GET", url, headers=headers, auth=auth, timeout=10)
        if response.status_code == 200:
            return True, "Jira connected successfully."
        return False, f"Jira error: {response.text}"
    except Exception as e:
        return False, f"Jira error: {str(e)}"
