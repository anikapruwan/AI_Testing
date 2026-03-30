import pandas as pd

data = [
    ["TC-001", "Functional", "Verify primary email and password login flow", "User is on app.vwo.com", "1. Enter valid email\n2. Enter valid password\n3. Submit form", "User smoothly transitions to personalized VWO dashboard", "High"],
    ["TC-002", "Functional", "Verify Multi-Factor Authentication (MFA/2FA)", "User has MFA configured", "1. Complete primary authentication\n2. Provide MFA challenge", "User successfully authenticates and transitions to dashboard", "High"],
    ["TC-003", "Functional", "Verify Enterprise Single Sign-On (SAML/OAuth)", "User belongs to an organization with SSO configured", "1. Select SSO login\n2. Authenticate via Identity Provider", "User successfully authenticates and transitions to dashboard", "High"],
    ["TC-004", "Functional", "Verify Social Login integration", "User relies on Google/Microsoft for identity", "1. Select Social Login\n2. Authenticate through provider", "User successfully authenticates and transitions to dashboard", "Medium"],
    ["TC-005", "User Interface", "Verify real-time field validation on blur", "User interacts with the login form", "1. Focus an input field\n2. Blur from the input field", "Immediate validation feedback is provided", "Medium"],
    ["TC-006", "Functional", "Verify automatic email format validation", "User navigates to login page", "1. Enter email strings into the email field", "Specialized validation checks format automatically", "High"],
    ["TC-007", "Functional", "Verify password strength indicators during input", "User is setting/resetting password", "1. Input password of varying complexity", "Visual password strength indicators enforce complexity requirements", "Medium"],
    ["TC-008", "Functional", "Verify forgot password/recovery options", "User encounters the login page", "1. Request password reset via forgot password link", "User shown multiple recovery options; password reset flow triggers", "High"],
    ["TC-009", "Negative", "Verify login failure with incorrect credentials", "User has invalid credentials", "1. Attempt login with invalid credentials", "[Needs clarification - explicit error messages/codes are not defined in PRD]", "High"],
    ["TC-010", "Negative", "Verify rate limiting against brute-force attacks", "User encounters login page", "1. Perform continuous rapid authentication requests", "Mechanism throttles requests [Needs clarification - specific threshold and lock-out behaviour not defined]", "High"],
    ["TC-011", "Security", "Verify login data uses End-to-End encryption", "User initiates authentication process", "1. Analyze transmitted authentication payloads", "Data is transmitted securely via HTTPS and stored using industry-standard hashing", "High"],
    ["TC-012", "Performance", "Verify login page load time on standard connections", "User is on a standard connection", "1. Load app.vwo.com", "Page successfully loads within 2 seconds", "High"],
    ["TC-013", "User Interface", "Verify auto-focus functionality", "User arrives at login page", "1. Load the login interface", "First input field receives automatic focus", "Low"],
    ["TC-014", "Accessibility", "Verify login form keyboard navigation and ARIA labels", "User relying on keyboard/screen readers accesses login page", "1. Tab through login elements", "Full keyboard navigation is maintained and ARIA labels are compliant with WCAG 2.1 AA", "High"],
]

df = pd.DataFrame(data, columns=["TID", "Category", "Description", "Pre-conditions", "Steps", "Expected", "Priority"])
df.to_excel("/Users/anirudhkapruwan/AI_Training/Antigravity/Prompt_Engneering_Project/Output/VWO_Login_Testcases.xlsx", index=False)
print("Excel test cases generated successfully.")
