You are a QA Automation Expert with 15+ years of experience in enterprise-level testing and reporting.

Your task is to generate a **professional HTML Test Matrix Report** for a web application.

### INPUT DETAILS:
- Application Name: <Application Name>
- Module Name: <Module Name>
- Build Version: <Build Version>
- Test Cycle: <Cycle Name>
- Tester Name: <Tester Name>

### TEST MATRIX DATA:
Provide the test matrix in tabular format with the following columns:
- Test Case ID
- Test Scenario
- Test Description
- Priority (High/Medium/Low)
- Test Type (Functional/UI/API/Regression)
- Environment (Chrome/Firefox/Edge/Mobile)
- Status (Pass/Fail/Blocked/Not Executed)
- Defect ID (if any)
- Execution Time
- Comments

### REQUIREMENTS:
1. Generate a **fully structured HTML report** with:
   - Header section (Application details)
   - Summary dashboard showing:
     - Total Test Cases
     - Passed
     - Failed
     - Blocked
     - Pass Percentage (with progress bar)
   - Detailed Test Matrix Table
   - Defect Summary Section

2. Apply **modern UI styling using CSS**:
   - Clean layout with professional colors
   - Status-based color coding:
     - Pass → Green
     - Fail → Red
     - Blocked → Orange
     - Not Executed → Gray
   - Sticky table header
   - Hover effects

3. Add **basic JavaScript functionality**:
   - Filter by Status dropdown
   - Search by Test Case ID
   - Dynamic summary calculation

4. Ensure:
   - Mobile responsive design
   - Proper semantic HTML5 tags
   - Readable font and spacing

5. Output should be:
   - A **single complete HTML file**
   - Ready to open in browser (no external dependencies)

### OUTPUT FORMAT:
Return ONLY the HTML code inside a code block.

### IMPORTANT:
- Do NOT skip styling or JS
- Do NOT use placeholders in final table — generate realistic sample test data (minimum 10 rows)
- Follow enterprise-level reporting standards

Now generate the HTML Test Matrix Report.